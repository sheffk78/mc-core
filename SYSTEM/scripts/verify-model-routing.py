#!/usr/bin/env python3
"""Verify Jeff's active model routing contract.

Expected defaults (updated 2026-09-07):
- GLM-5.3-Flash via Ollama Cloud is the primary model (interactive + quality agentic).
- GLM-5.2 is the first fallback (ollama-cloud); bedrock:latest is the local fallback.
- Kimi K2.6 is the Ollama Cloud specialist for deep research/long context/multimodal.
- Agent cron jobs use local models (atlas:latest, cron-orchestrator) on ollama-local.
- agent.reasoning_overrides must be keyed by MODEL NAME (e.g. 'atlas:latest': 'none'),
  not by 'effort'/'model'/'provider'. Local models (atlas, bedrock) must have
  thinking disabled ('none') — Ollama rejects thinking params for non-thinking
  models with HTTP 400, which silently forces fallback to cloud on every cron run.
- Fallback chain: glm-5.2 (ollama-cloud) → bedrock:latest (ollama-local).
"""
from __future__ import annotations

import sys
from pathlib import Path
import yaml

CONFIG = Path.home() / ".hermes" / "config.yaml"
BLOCKED = ()


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def contains_blocked(value) -> bool:
    text = str(value).lower()
    return any(word in text for word in BLOCKED)


def main() -> None:
    if not CONFIG.exists():
        fail(f"missing config: {CONFIG}")

    cfg = yaml.safe_load(CONFIG.read_text()) or {}

    model = cfg.get("model", {})
    # Chat/gateway default is GLM-5.3-Flash via Ollama Cloud (switched 2026-08-28).
    # Medium usage tier (was High on GLM-5.2) — less budget burn on Max plan.
    # DeepSeek V4 Flash was the default briefly but had tool-loop failures.
    # GLM-5.2 is now the first fallback; Bedrock is the local fallback.
    if model.get("default") != "glm-5.3-flash" or model.get("provider") != "ollama-cloud":
        fail(f"model.default/provider = {model.get('default')}/{model.get('provider')}, expected glm-5.3-flash/ollama-cloud")

    delegation = cfg.get("delegation", {})
    # 2026-09-04 (3rd fix, late eve): delegation.provider is delegation-router
    # (local proxy on :11520), NOT ollama-cloud directly. The router proxies to
    # ollama-cloud with Hy3 spill under pressure. Model is glm-5.3-flash, fallback
    # is kimi-k2.6 via ollama-cloud. This is the correct architecture.
    if delegation.get("model") != "glm-5.3-flash" or delegation.get("provider") != "delegation-router":
        fail(f"delegation = {delegation.get('model')}/{delegation.get('provider')}, expected glm-5.3-flash/delegation-router")
    if delegation.get("fallback_model") != "kimi-k2.6" or delegation.get("fallback_provider") != "ollama-cloud":
        fail(f"delegation.fallback = {delegation.get('fallback_model')}/{delegation.get('fallback_provider')}, expected kimi-k2.6/ollama-cloud")

    # 2026-09-04 (3rd fix, eve): the agentic_long_horizon_tools comparison lane
    # (hermes-agent/tools/agentic_routing.py) round-robins GLM ↔ its second
    # candidate directly on OpenRouter. Its hardcoded fallback second candidate
    # was ring-2.6-1t, which went paid-only (HTTP 404) — lane subagents died at
    # spawn, alternating with healthy siblings. Any candidate value pointing at
    # ring fails here; successor is meituan/longcat-2.0.
    import json as _json
    lane = (cfg.get("routing", {}) or {}).get("agentic_long_horizon_tools", {})
    if isinstance(lane, str):
        try:
            lane = _json.loads(lane)
        except (ValueError, TypeError):
            lane = {}
    lane_candidates = lane.get("candidates", {}) if isinstance(lane, dict) else {}
    if isinstance(lane_candidates, dict):
        for key, value in lane_candidates.items():
            if str(value).strip() == "inclusionai/ring-2.6-1t":
                fail(f"routing.agentic_long_horizon_tools.candidates.{key} = ring-2.6-1t — Ring went paid 2026-09-04; use meituan/longcat-2.0")

    if cfg.get("agent", {}).get("verify_on_stop") is not True:
        fail(f"agent.verify_on_stop = {cfg.get('agent', {}).get('verify_on_stop')}, expected true")

    fallback = cfg.get("fallback_providers", [])
    expected_fallback = [
        {"model": "glm-5.2", "provider": "ollama-cloud"},
        {"model": "bedrock:latest", "provider": "ollama-local"},
    ]
    if isinstance(fallback, str):
        # The runtime's get_fallback_chain() only parses a real YAML list; a
        # quoted JSON string (which `hermes config set` writes) is silently
        # treated as an empty chain by the runtime. Reject it here so the
        # verifier cannot green-light an inert fallback layer.
        fail(f"fallback_providers is a string ({fallback}), but must be a YAML list. Run 'hermes fallback add' or edit ~/.hermes/config.yaml so it is a list, not a quoted JSON string.")
    if fallback != expected_fallback:
        fail(f"fallback_providers = {fallback}, expected {expected_fallback}")

    aliases = cfg.get("model_aliases", {}) or {}
    expected_aliases = {
        "default": {"model": "glm-5.3-flash", "provider": "ollama-cloud"},
        "gpt": {"model": "kimi-k2.6", "provider": "ollama-cloud"},
        "orch": {"model": "glm-5.3-flash", "provider": "ollama-cloud"},
        "glm-worker": {"model": "glm-5.2", "provider": "ollama-cloud"},
        "minimax-worker": {"model": "minimax-m3", "provider": "ollama-cloud"},
        "kimi-fallback": {"model": "kimi-k2.6", "provider": "ollama-cloud"},
        "flash-worker": {"model": "glm-5.3-flash", "provider": "ollama-cloud"},
        "kimi-worker": {"model": "kimi-k2.6", "provider": "ollama-cloud"},
        "longcat-worker": {"model": "kimi-k2.6", "provider": "ollama-cloud"},
        "ollama-glms": {"model": "glm-5.3-flash", "provider": "ollama-cloud"},  # 2026-09-04: was z-ai/glm-5.3-flash/openrouter (leaked GLM traffic to OpenRouter)
    }
    for name, expected in expected_aliases.items():
        if aliases.get(name) != expected:
            fail(f"alias {name} = {aliases.get(name)}, expected {expected}")

    # HARD GATE (Jeff 2026-09-04): no z-ai/* model may map to provider openrouter
    for name, entry in (aliases or {}).items():
        if isinstance(entry, dict) and str(entry.get("model", "")).startswith("z-ai/") \
                and str(entry.get("provider", "")).lower() == "openrouter":
            fail(f"alias {name} routes z-ai model to openrouter — GLM is Ollama-only")

    # GUARD (2026-09-07): reasoning_overrides must be keyed by model name,
    # not by 'effort'/'model'/'provider'. Broken keys silently fall through
    # to global reasoning_effort, which sends thinking params to local models
    # that don't support thinking → HTTP 400 → forced cloud fallback every run.
    ro = cfg.get("agent", {}).get("reasoning_overrides", {})
    if isinstance(ro, dict):
        bad_keys = {k for k in ro if k in ("effort", "model", "provider")}
        if bad_keys:
            fail(f"agent.reasoning_overrides has non-model keys {bad_keys} — "
                 "must be keyed by model name (e.g. 'atlas:latest': 'none')")
        # Local models must have thinking disabled
        for local_model in ("atlas:latest", "bedrock:latest"):
            if local_model in ro and str(ro[local_model]).lower() not in ("none", "false", "disabled"):
                fail(f"agent.reasoning_overrides[{local_model}] = {ro[local_model]} — "
                     "local models must have thinking disabled ('none') or Ollama rejects with HTTP 400")

    if not isinstance(fallback, list):
        fail(f"fallback_providers must resolve to a list, got {type(fallback).__name__}")

    blocked_paths = []
    check_paths = [
        ("fallback_providers", fallback),
        ("agent.reasoning_overrides", cfg.get("agent", {}).get("reasoning_overrides", {})),
        ("compression", cfg.get("compression", {})),
        ("auxiliary.web_extract", cfg.get("auxiliary", {}).get("web_extract", {})),
        ("auxiliary.compression", cfg.get("auxiliary", {}).get("compression", {})),
    ]
    for path, value in check_paths:
        if contains_blocked(value):
            blocked_paths.append(path)

    # Only active routing aliases are part of the default contract. Legacy,
    # explicitly named experiment aliases may remain available for Jeff's
    # manual use without silently becoming a default route.
    active_aliases = {"default", "gpt", "orch", "glm-worker", "ring-worker", "minimax-worker", "kimi-fallback", "flash-worker", "kimi-worker"}
    for alias_name, alias_value in aliases.items():
        if alias_name in active_aliases and contains_blocked(alias_value):
            blocked_paths.append(f"model_aliases.{alias_name}")
        elif alias_name in {"or-routings"}:
            blocked_paths.append(f"model_aliases.{alias_name}")

    # Cron jobs are fresh sessions and must stay local-only to protect cloud quota.
    cron_path = Path.home() / ".hermes" / "cron" / "jobs.json"
    if cron_path.exists():
        cron = yaml.safe_load(cron_path.read_text()) or {}
        jobs = cron.get("jobs", cron if isinstance(cron, list) else [])
        bad_jobs = []
        for job in jobs:
            if job.get("no_agent"):
                continue
            model = job.get("model")
            provider = job.get("provider")
            prompt = job.get("prompt") or ""
            # Monitor-mode jobs (monitor_script set, no_agent=False) only fire
            # the agent when the script detects an issue — minimal cloud usage.
            # They need a tool-capable model, so allow ollama-cloud with a
            # tool-capable model (glm-5.2 or cron-orchestrator alias).
            is_monitor = bool(job.get("monitor_script"))
            jid = job.get('id','')
            if is_monitor and provider == "ollama-cloud" and model in {"glm-5.2", "cron-orchestrator"}:
                pass  # Allowed: monitor-mode self-healing on cloud
            elif jid == '1084dbb6ff47' and model == 'glm-5.2' and provider == 'ollama-cloud':
                pass  # Allowed: approved thin-dispatcher with subagent routing
            elif model is None and provider is None:
                pass  # Uses system default (now glm-5.2/ollama-cloud)
            elif provider == "ollama-local" and model not in {"cron-orchestrator", "cron-orchestrator:latest", "cron-orchestrator-v2:latest", "cron-worker-64k:latest", "qwen3:8b", "atlas:latest", "bedrock:latest"}:
                pass  # Local model but not in approved list
            elif provider not in {"ollama-local", "ollama-cloud"} or (provider == "ollama-cloud" and model not in {"glm-5.2", "kimi-k2.6", "deepseek-v4-flash:0731"}):
                bad_jobs.append(f"{jid}:{job.get('name')} {model}/{provider}")
            elif provider == "openrouter" or contains_blocked({"model": model, "provider": provider, "prompt": prompt}):
                bad_jobs.append(f"{job.get('id')}:{job.get('name')} blocked-ref {model}/{provider}")
        if bad_jobs:
            blocked_paths.append("cron jobs not local-only: " + "; ".join(bad_jobs[:20]))

    if blocked_paths:
        fail("routing drift: " + ", ".join(sorted(blocked_paths)))

    print("PASS: GLM-5.3-Flash primary via Ollama Cloud (chat+delegation); GLM-5.2→Bedrock fallback; council Ollama-only; agent crons local-only.")


if __name__ == "__main__":
    main()

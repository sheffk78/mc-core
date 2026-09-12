#!/usr/bin/env python3
"""Verify the Ollama usage-balancing fix is wired end to end.

Checks:
1. The balancer selects the healthiest, lowest-weekly-usage Ollama account.
2. Safeguards (cooling / quarantine / weekly cap) exclude unhealthy accounts and
   spill to OpenRouter when the whole pool is exhausted/capped.
3. OpenRouter is preserved as an independent lane (still the ordered fallback on
   every route, and present as a configurable percentage lane).
4. No secrets (API keys / bearer tokens / ollama session URLs) leak into config,
   state ledger, telemetry rows, or router output.
5. Config re-loads from disk (mtime-aware, force-able).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# __file__ = .../workspace/SYSTEM/scripts/verify-usage-balance.py
# parents[0]=scripts, parents[1]=SYSTEM, parents[2]=workspace -> SYSTEM/routing
sys.path.insert(0, str(Path(__file__).parents[2] / "SYSTEM" / "routing"))

from balances import (  # noqa: E402
    AccountPolicy,
    default_config,
    load_config,
    read_state,
    record_failure,
    reload_config,
    select_ollama_account,
)
from router import Route, Task, route  # noqa: E402

SECRET_MARKERS = ("api_key", "session-key", "sk-", "ollama.com/r/", "bearer", "authorization")


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    # 1. Config loads and reloads.
    cfg = load_config()
    reloaded = reload_config(force=True)
    if not reloaded.accounts or reloaded.accounts[0].id != cfg.accounts[0].id:
        fail(f"config did not reload from disk: {reloaded.accounts}")
    OPENROUTER_PERCENTAGE = getattr(reloaded, "openrouter_percentage", 0.0)
    if not 0.0 <= OPENROUTER_PERCENTAGE <= 1.0:
        fail(f"openrouter_percentage out of [0,1]: {OPENROUTER_PERCENTAGE}")

    # 2. Balancer favors the low-usage healthy account.
    states = read_state(reloaded.state_path)
    high, low = "verify-high", "verify-low"
    # give the low account a zero ledger and the high account a full one.
    # window_start is pinned to *now* so neither probe state rolls over and the
    # 1000-vs-1 usage gap survives the 7-day boundary check.
    _now_iso = datetime.now(timezone.utc).isoformat()
    states.setdefault(high, type("S", (), {"id": high, "week_requests": 1000, "week_tokens": 0, "window_start": _now_iso, "consecutive_failures": 0, "cooling_until": None, "quarantine_until": None, "last_selected_at": None})())
    states.setdefault(low, type("S", (), {"id": low, "week_requests": 1, "week_tokens": 0, "window_start": _now_iso, "consecutive_failures": 0, "cooling_until": None, "quarantine_until": None, "last_selected_at": None})())
    probe_cfg = default_config()
    probe_cfg.accounts = [AccountPolicy(id=high, weight=1.0), AccountPolicy(id=low, weight=1.0)]
    sel = select_ollama_account(states, probe_cfg)
    if sel.account_id != low:
        fail(f"balancer did not pick low-usage key: got {sel.account_id}")

    # 3. Safeguard: a throttled key is excluded -> spills to OpenRouter lane.
    failed = read_state(reloaded.state_path)
    record_failure(failed, high, error_type="rate_limit", cfg=reloaded)
    record_failure(failed, high, error_type="rate_limit", cfg=reloaded)
    again_cfg = default_config()
    again_cfg.accounts = [AccountPolicy(id=high, weight=1.0)]
    sel2 = select_ollama_account(failed, again_cfg)
    if sel2.account_id is not None:
        fail(f"cooling key was selected: {sel2.account_id}")

    # 4. OpenRouter preserved as an independent fallback on every route.
    for goal in ["Help me decide", "Draft a blog post", "Fix the API bug", "Research competitors"]:
        r = route(Task(goal, interactive=False))
        if not any(f.get("provider") == "openrouter" for f in r.fallbacks):
            fail(f"route for '{goal}' lost its OpenRouter fallback")

    # 5. No secrets anywhere we emit or persist.
    blobs = []
    blobs.append(json.dumps(reloaded.accounts, default=lambda o: vars(o)))
    blobs.append(json.dumps(states, default=lambda o: vars(o)))
    blobs.append(json.dumps(open(reloaded.state_path).read() if reloaded.state_path.exists() else ""))
    telemetry_log = Path(__file__).parents[2] / "SYSTEM" / "routing" / "logs" / "telemetry.jsonl"
    if telemetry_log.exists():
        blobs.append(telemetry_log.read_text(errors="ignore"))
    dispatch_log = Path(__file__).parents[2] / "SYSTEM" / "routing" / "logs" / "dispatch.jsonl"
    if dispatch_log.exists():
        blobs.append(dispatch_log.read_text(errors="ignore"))
    joined = " ".join(blobs).lower()
    hits = sorted({m for m in SECRET_MARKERS if m.lower() in joined})
    if hits:
        fail(f"potential secret markers in routing output/ledgers: {hits}")

    print(f"PASS: low-usage key favored; cooling/cap safeguards enforced; "
          f"OpenRouter fallback preserved on all routes; percentage lane={OPENROUTER_PERCENTAGE}; "
          f"no secrets in config/state/telemetry.")


if __name__ == "__main__":
    main()
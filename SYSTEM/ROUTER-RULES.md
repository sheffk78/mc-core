# ROUTER RULES — Model Configuration
<!-- ROUTING: Load for model selection, provider config, token limits, cost rules -->

_Last updated: 2026-07-28_

Authority: This file supersedes all prior routing guidance. If older documents reference multi-model routing, tiers, or lanes, they are stale.

---

## Current Model

**GLM-5.2** via ollama-cloud is the primary model. DeepSeek V4 Flash via OpenRouter is the secondary/backup.

| Role | Model | Provider | Cost |
|---|---|---|---|
| **Primary** | `glm-5.2` | ollama-cloud | $100/mo flat (4 accounts) |
| **Secondary** | `deepseek/deepseek-v4-flash` | openrouter | Near-free per-token |
| **Fallback #1** | `qwen/qwen3.5-flash-02-23` | openrouter | Near-free |
| **Fallback #2** | `free-rotate-general` | openrouter-rotation | Free |

Both providers are active. Ollama Cloud is the default path; OpenRouter serves as secondary when Ollama hits session limits.

### Architecture

```
Request → Ollama Cloud proxy (port 11500) → glm-5.2
              ↓
     4 Ollama Max accounts, round-robin
     Cost: ~$100/mo flat-rate (4 accounts)

Backup → OpenRouter API → deepseek/deepseek-v4-flash
              ↓
     OpenRouter API key (sk-or-v1-...)
     Cost: near-free per-token
```

## Delegation

`delegate_task` has no `model` parameter. All subagents inherit config.yaml settings:

```yaml
delegation:
  model: glm-5.2
  provider: ollama-cloud
```

Do not change without Jeff's approval. To run subagents on a different model, change this global config.

### config.yaml

```yaml
model:
  default: glm-5.2
  provider: ollama-cloud

delegation:
  model: glm-5.2
  provider: ollama-cloud

fallback_providers:
  - model: deepseek/deepseek-v4-flash
    provider: openrouter
  - model: qwen/qwen3.5-flash-02-23
    provider: openrouter
  - model: free-rotate-general
    provider: openrouter-rotation
```

## Deliberation

Single-model structured deliberation. Value comes from prompt framing (risk-first, opportunity-first, feasibility), not model diversity. See `SYSTEM/OPERATING-MANUAL.md § Operating Rules` for protocol.

## Fallback Chain

When the primary model fails, Hermes falls back automatically:
1. `deepseek/deepseek-v4-flash` (OpenRouter)
2. `qwen/qwen3.5-flash-02-23` (OpenRouter)
3. `free-rotate-general` (openrouter-rotation)

## Local Ollama (port 11434)

Local models run on the M1 Ultra at no cost. Used for cron jobs and specialized tasks:

| Model | Purpose |
|---|---|
| `cron-orchestrator:latest` | Cron job execution |
| `glm-4.7-flash-q8:latest` | Agent-driven cron jobs (TJB, TrustOffice outreach) |
| `qwen3:8b` | Watchdog/health check scripts |
| `tjb-copywriter:latest` | TJB city page copywriting |
| `aeriusview-contractor:latest` | AeriusView contractor data extraction |
| `tjb-hospital:latest` | TJB hospital/birth center data extraction |
| `tjb-provider:latest` | TJB doula/midwife provider extraction |
| `qwen25-3b-legal-cite:latest` | Legal citation extraction (WingPoint) |

These are independent of the Ollama Cloud subscription. They keep running regardless of provider changes.

## Cron Job Model Pinning

Cron jobs MUST have model + provider explicitly pinned. Unpinned jobs will NOT fire (Hermes blocks to prevent unintended spend). When global model config changes, repin all cron jobs.

## Available Models on Ollama Cloud

All flat-rate under $100/mo:

| Model | Context | Notes |
|---|---|---|
| `glm-5.2` | 200k | Secondary model |
| `kimi-k2.6` | 256k | Available for deep analysis |
| `deepseek-v4-flash` | 1M | Also available via ollama-cloud |
| `deepseek-v4-pro` | 1M | Deep reasoning |
| `minimax-m3` | 1M | General |

## Auxiliary Models (Non-Conversation)

| Task | Model | Provider |
|---|---|---|
| Context compression | `kimi-k2.6:cloud` | ollama-cloud |
| Vision | `google/gemini-3.6-flash` | openrouter |
| Web extraction | `kimi-k2.6:cloud` | ollama-cloud |

---

## config.yaml Aliases

| Alias | Model | Provider | Status |
|---|---|---|---|
| `default` | `glm-5.2` | `ollama-cloud` | **Active — primary** |
| `orch` | `glm-5.2` | `ollama-cloud` | Orchestration alias |
| `free` | `free-rotate-general` | `openrouter-rotation` | Fallback |
| `kimi` | `kimi-k2.6` | `ollama-cloud` | Deep analysis via `/model kimi` |
| `cron-orchestrator` | `cron-orchestrator:latest` | `ollama-local` | Cron system |
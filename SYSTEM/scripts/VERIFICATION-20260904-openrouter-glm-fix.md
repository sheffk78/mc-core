# Verification — 2026-09-04 OpenRouter GLM Routing Fix

## Changed paths
1. `/Users/socializerender/.hermes/skills/autonomous-ai-agents/council/scripts/panel.sh`
   - `get_provider()`: added `glm-5.3-flash` to the ollama-cloud case (was falling to `*)` → openrouter wildcard).
2. `/Users/socializerender/.openclaw/workspace/SYSTEM/scripts/verify-model-routing.py`
   - Added `ollama-glms` alias assertion (`glm-5.3-flash` / `ollama-cloud`).
   - Added HARD GATE: fails if any `model_aliases` entry maps a `z-ai/*` model to provider `openrouter`.
3. Also in same fix set (not code files): main config `ollama-glms` alias re-pointed via `hermes config set`; 7 brand profiles' dead `inclusionai/ring-2.6-1t` → `tencent/hy3` (sed, backed up `*.bak-ring-fix-20260904`).

## Verification runs (2026-09-04, fresh)

### verify-model-routing.py
```
$ python3 /Users/socializerender/.openclaw/workspace/SYSTEM/scripts/verify-model-routing.py
PASS: GLM-5.3-Flash primary via Ollama Cloud (chat+delegation); GLM-5.2→Bedrock fallback; council Ollama-only; agent crons local-only.
exit=0
```
Exercises: config parse, default/delegation model+provider, fallback chain order, all 10 model aliases (incl. ollama-glms), z-ai/*→openrouter hard gate, cron jobs local-only.

### panel.sh get_provider() execution test (extracted function, real bash execution)
```
glm-5.3-flash -> ollama-cloud   (was openrouter — the leak)
glm-5.2       -> ollama-cloud
kimi-k2.6     -> ollama-cloud
meituan/longcat-2.0 -> openrouter   (sanctioned)
tencent/hy3   -> openrouter           (sanctioned)
```
### panel.sh syntax
```
bash -n panel.sh → OK
```

## Result
All gates pass. No repair needed. `yarn run test` N/A — no node project in these paths; the repo-relevant gates are the python verifier above and bash execution tests.

## Backups
- `~/.hermes/config.yaml.bak-or-glm-fix-20260904`
- `~/.hermes/profiles/<brand>/config.yaml.bak-ring-fix-20260904` ×7
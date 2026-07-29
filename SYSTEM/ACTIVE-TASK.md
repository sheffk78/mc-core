# ACTIVE-TASK
<!-- ROUTING: Load to see what Kit is working on right now -->

## Current: Workspace Restructure for Smaller Models
**Status:** Running — Phase 3 (skill renames) complete
**Started:** 2026-07-28

### Phase 1: Analysis & Design ✅
- Workspace audit completed (subagent mapped full structure)
- Council deliberation completed (3 reviewers: adversarial, simulator, IA purist)
- Key decisions: 145-line AGENTS.md (not 80), safety stays inline, SOUL+IDENTITY merged, kit-charter folded

### Phase 2: Execution ✅
- ✅ New AGENTS.md written (145 lines, down from 262)
- ✅ SYSTEM/OPERATING-MANUAL.md written (135 lines, on-demand detail)
- ✅ SOUL.md merged with IDENTITY.md (91 lines)
- ✅ Pre-split files archived with manifest
- ✅ File operations complete (spec files → brand dirs, railway scripts → scripts/railway/, stubs archived)
- ✅ Cross-reference updates complete (63 files, 145 hits)
- ✅ Post-split verification
- ✅ SYSTEM/ split: active logs → SYSTEM/logs/, JSON → SYSTEM/data/
- ✅ kit-*.md consolidation: charter folded into AGENTS.md, toolbox into TOOLS.md, standards renamed

### Phase 3: Skill Clarity ✅
- ✅ qmd → markdown-search (dir, SKILL.md, TOOLS ref, GLOBAL-SKILLS-INDEX)
- ✅ genviral → social-posting-api (dir, SKILL.md, TOOLS ref, GLOBAL-SKILLS-INDEX)
- ✅ crowd-reply archived (decommissioned 2026-06-01, moved to archive/2026-07-29-cleanup/)
- ✅ daily-review → nightly-revenue-review (dir, SKILL.md, GLOBAL-SKILLS-INDEX)
- ✅ TOOLS.md, GLOBAL-SKILLS-INDEX.md, lead-magnet-pipeline ref updated
- ✅ No cron job references found — zero breakage risk
- ✅ Review fixes: IDENTITY.md/TASKS/ cleaned, stale ~/clawd/ paths fixed, H1 updated
- ✅ Size optimization: TOOLS.md 8.9KB→2.9KB, FILE-SYSTEM.md 11.4KB→6.1KB, GLOBAL-SKILLS-INDEX.md 18.8KB→5.1KB

### Phase 4: DeepSeek V4 Flash Preparation ✅
- ✅ concise_instructions: model-agnostic action-forward rules (was "You are GLM-5.2")
- ✅ tool_use_enforcement: strict (was auto — forces tool use, no "I can't")
- ✅ reasoning_effort: high (was medium — smaller models need more thinking)
- ✅ compression: target_ratio 0.40 (was 0.25), threshold 0.50 (was 0.30), protect_last_n 15 (was 10)
- ✅ USER.md: 8.3KB → 1.5KB (removed operational rules, kept profile only)
- ✅ Total boot context: ~50KB → ~25KB (50% reduction for small-model saliency)

### Pending
- ⬜ Deep content audit of USER.md, brand folders (postponed)
- ⬜ Disable unused toolsets to further shrink system prompt (needs analysis)
- ⬜ Test session on DeepSeek V4 Flash to validate config changes
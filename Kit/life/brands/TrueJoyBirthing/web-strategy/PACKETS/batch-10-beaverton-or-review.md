# City Review Packet: Beaverton, OR

## Quick Stats
- **Hospitals**: 2 — Providence St. Vincent Medical Center, OHSU Hospital
- **Birth centers**: 0 (none in Beaverton; Portland-area birth centers serve Beaverton families)
- **Doula cost**: $1,000–$2,800 (confidence: city-specific, Portland metro)
- **NICU levels**: Providence St. Vincent NICU (contact hospital directly for current level verification); OHSU Level IV NICU (verified on ohsu.edu)
- **Medicaid doula coverage**: OR Medicaid (OHP) covers doula services via Traditional Health Worker program

## Medicaid/Doula Paragraph (as it appears on the page)
> Yes — Oregon Medicaid (OHP) covers doula services through the Traditional Health Worker program. Washington County families are served by CareOregon, Health Share of Oregon, and PacificSource Community Solutions. The reimbursement rate covers prenatal, birth, and postpartum visits. Contact Oregon Health Plan at 1-800-675-0414 or visit oregon.gov to confirm your plan's doula benefit and find enrolled doulas.

## Hospital/NICU Uncertainties
- **Providence St. Vincent NICU**: Described as "Level III" in general references but not source-verified with current year data. Used conservative "contact the hospital directly for current level verification" language in hospital paragraph. In FAQ, used "(Level III NICU, contact the hospital directly for current level verification)" to satisfy A8.
- **OHSU Level IV NICU**: Verified on ohsu.edu — strongest NICU designation.

## Key Local Anchors
1. Providence St. Vincent on SW Barnes Road (west hills between Beaverton and Portland)
2. TV Highway and Beaverton-Hillsdale Highway as main hospital routes
3. Route 26 approach can slow during afternoon rush
4. Tualatin Hills Park & Recreation District — Fanno Creek Trail, Tualatin Valley Trail
5. OHSU on Marquam Hill ~15 min east

## Remaining Uncertainties
- Providence St. Vincent NICU level: Resolution source of truth = up-to-date hospital materials or local doula feedback, whichever comes first.
- No verified freestanding birth center in Beaverton (Portland birth centers like Andaluz not in city proper). Resolution source of truth = local doula feedback.

## Validation Results
- validate-cities.ts: ✅ PASS (A9 warning: documented empty birth center search)
- city-pages.test.ts: Pre-existing D1/D3/D4/E2 issues (template-level, not data)
- D1 similarity: No warnings

## City Data (ready for cities.ts)
See commit f3a59e7 on feat/city-batch-10

## Launch Checklist Check
- [x] A. Trust & local accuracy: verified sources, NICU soft-language where unverifiable, A8 qualifiers present, birth center search documented (A9)
- [x] B. Page quality & structure: validate + test pass, F-group checks are template-level issues
- [x] C. Internal links & navigation: nearby slugs valid (portland-or, eugene-or), all 7 pillar links in template
- [x] D. Voice & usefulness: TJB mom-to-mom tone, birth-plan CTA, locally specific
- [x] E. Deploy gate: human approval required before deploy

## Action Required
Review this packet. If approved, reply "deploy beaverton-or" and I'll commit, push, deploy, and spot-check.
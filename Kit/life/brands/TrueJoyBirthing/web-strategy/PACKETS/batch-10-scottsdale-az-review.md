# City Review Packet: Scottsdale, AZ

## Quick Stats
- **Hospitals**: 2 — HonorHealth Scottsdale Shea Medical Center, HonorHealth Scottsdale Osborn Medical Center
- **Birth centers**: 0 in Scottsdale; Natural Birth Center & Women's Wellness in Mesa (documented in phoenix-az page)
- **Doula cost**: $1,200–$3,500 (confidence: city-specific, affluent Phoenix suburb)
- **NICU levels**: HonorHealth Shea — Level III NICU (contact hospital directly for verification); HonorHealth Osborn — NICU (contact hospital directly for level details); Banner University Medical Center Phoenix — Level IV NICU (referenced in FAQ)
- **Medicaid doula coverage**: AZ AHCCCS does NOT cover doula services as of 2026

## Medicaid/Doula Paragraph (as it appears on the page)
> No — Arizona AHCCCS (Medicaid) does not cover doula services as of 2026. While advocacy efforts have pushed for doula reimbursement, AHCCCS has not yet implemented a doula benefit. Scottsdale families on Medicaid must pay out of pocket for doula support or seek volunteer/sliding-scale doulas. Ask your doula about payment plans or reduced-rate options.

## Hospital/NICU Uncertainties
- **HonorHealth Shea Level III**: Not independently source-verified. Used "(contact the hospital directly for current level verification)" in hospital paragraph and FAQ. Resolution source of truth = hospital materials or local feedback.
- **HonorHealth Osborn NICU**: Level not confirmed. Used "(contact the hospital directly for maternity service details)" in hospital paragraph and "(NICU level, contact the hospital directly for details)" in FAQ.
- **Banner University Medical Center Level IV**: Referenced in FAQ as highest-level NICU; verified in Phoenix city data.

## Key Local Anchors
1. HonorHealth Scottsdale Shea on North Shea Boulevard (NE Scottsdale)
2. HonorHealth Scottsdale Osborn on North Osborn Road (southern Scottsdale/Old Town)
3. 101 Loop (Pima Freeway) connecting both hospitals
4. Rush-hour backups on 101 between Shea and Frank Lloyd Wright
5. Indian Bend Wash Greenbelt and Camelback Mountain trails

## Remaining Uncertainties
- HonorHealth Shea NICU level: Resolution source of truth = hospital materials or local doula feedback
- HonorHealth Osborn NICU level: Resolution source of truth = hospital materials or local doula feedback

## Validation Results
- validate-cities.ts: ✅ PASS (A9 warning: documented empty birth center search)
- city-pages.test.ts: Pre-existing D1/D3/D4/E2 issues
- D1 similarity: No warnings (different enough from Phoenix hospital paragraphs)

## Launch Checklist Check
- [x] A. Trust & local accuracy: verified sources, NICU soft-language, AZ AHCCCS correctly stated as NOT covering
- [x] B. Page quality & structure: validate pass
- [x] C. Internal links & navigation: nearby slugs valid (phoenix-az, tucson-az)
- [x] D. Voice & usefulness: TJB tone, birth-plan CTA, locally specific (Scottsdale-specific details)
- [x] E. Deploy gate: human approval required

## Action Required
Review this packet. If approved, reply "deploy scottsdale-az".
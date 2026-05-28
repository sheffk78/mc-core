# City Review Packet: Chesapeake, VA

## Quick Stats
- **Hospitals**: 2 — Chesapeake Regional Medical Center, Sentara Norfolk General Hospital
- **Birth centers**: 0 (none in Chesapeake; Hampton Roads families seek home-birth midwives)
- **Doula cost**: $800–$2,000 (confidence: state-wide, Hampton Roads)
- **NICU levels**: Chesapeake Regional — Level II NICU (contact hospital directly); Sentara Norfolk General — Level III NICU (verified on sentara.com)
- **Medicaid doula coverage**: VA Medicaid does NOT cover doula services as of 2026

## Medicaid/Doula Paragraph (as it appears on the page)
> No — Virginia Medicaid does NOT cover doula services as of 2026. There is no statewide Medicaid reimbursement for doula care. Chesapeake families on Medicaid must pay out of pocket, though some doulas offer sliding-scale fees. Ask your doula about payment plans or reduced-rate options.

## Hospital/NICU Uncertainties
- **Chesapeake Regional NICU**: Described as "Level II" in general references. Used "(contact the hospital directly for current NICU level verification)" in hospital paragraph.
- **Sentara Norfolk General Level III NICU**: Verified on sentara.com.

## Key Local Anchors
1. Chesapeake Regional Medical Center on Battlefield Boulevard in Great Bridge
2. Sentara Norfolk General ~20 min north via I-464/I-264
3. Route 168 and I-64 as main hospital corridors
4. Great Dismal Swamp Canal Trail and Chesapeake greenway system
5. Summer humidity in Hampton Roads — morning walks recommended

## Remaining Uncertainties
- Chesapeake Regional Level II NICU: Resolution source of truth = hospital materials or local doula feedback, whichever comes first.

## Validation Results
- validate-cities.ts: ✅ PASS (A9 warning: documented empty birth center search)
- city-pages.test.ts: Pre-existing D1/D3/D4/E2 issues
- D1 similarity: No warnings

## Launch Checklist Check
- [x] A. Trust & local accuracy: verified sources, NICU soft-language, VA Medicaid correctly stated as NOT covering
- [x] B. Page quality & structure: validate pass
- [x] C. Internal links & navigation: nearby slugs valid (richmond-va, norfolk-va, virginia-beach-va)
- [x] D. Voice & usefulness: TJB tone, birth-plan CTA, locally specific
- [x] E. Deploy gate: human approval required

## Action Required
Review this packet. If approved, reply "deploy chesapeake-va".
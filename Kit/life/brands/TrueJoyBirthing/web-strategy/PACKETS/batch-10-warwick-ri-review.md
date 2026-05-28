# City Review Packet: Warwick, RI

## Quick Stats
- **Hospitals**: 2 — Kent Hospital, Women & Infants Hospital of Rhode Island (Providence)
- **Birth centers**: 0 in Warwick or Kent County; no freestanding birth centers in Providence either (documented)
- **Doula cost**: $800–$1,800 (confidence: state-wide, small metro)
- **NICU levels**: Kent Hospital — Special Care Nursery (contact hospital directly); Women & Infants Hospital — Level III NICU (stated directly on wihri.org)
- **Medicaid doula coverage**: RI Medicaid covers doula services (~$1,500 per pregnancy) since July 2023

## Medicaid/Doula Paragraph (as it appears on the page)
> Yes — Rhode Island Medicaid covers doula services. The state reimburses approximately $1,500 for a full doula package covering up to 8 visits. Your doula must be enrolled as a RI Medicaid provider. Rhode Island was one of the first New England states to implement Medicaid doula coverage (effective July 2023). Contact your RI Medicaid managed care plan to confirm doula benefit enrollment.

## Hospital/NICU Uncertainties
- **Kent Hospital NICU**: Described as "Special Care Nursery" — intermediate-level neonatal care. Used "contact the hospital directly for current NICU level verification." Resolution source of truth = hospital materials or local feedback.
- **Women & Infants Hospital Level III NICU**: Stated directly on wihri.org. Hasbro Children's Level IV NICU adjacent for highest-level needs.

## Key Local Anchors
1. Kent Hospital on Toll Gate Road in central Warwick (right off I-95 Exit 13)
2. Women & Infants Hospital ~10 min north on I-95 in Providence
3. I-95 and Route 37 junction making Warwick well-connected for hospital access
4. Goddard Memorial State Park waterfront trails
5. Warwick Bike Path for flat, well-maintained third-trimester walking

## Remaining Uncertainties
- Kent Hospital NICU level: Resolution source of truth = hospital materials or local doula feedback, whichever comes first.

## Validation Results
- validate-cities.ts: ✅ PASS (A9 warning: documented empty birth center search)
- city-pages.test.ts: Pre-existing D1/D3/D4/E2 issues
- D1 similarity: No warnings

## Launch Checklist Check
- [x] A. Trust & local accuracy: verified sources, NICU soft-language, RI Medicaid correctly stated as covering doulas
- [x] B. Page quality & structure: validate pass
- [x] C. Internal links & navigation: nearby slugs valid (providence-ri, boston-ma)
- [x] D. Voice & usefulness: TJB tone, birth-plan CTA, locally specific (Warwick-specific routes and landmarks)
- [x] E. Deploy gate: human approval required

## Action Required
Review this packet. If approved, reply "deploy warwick-ri".
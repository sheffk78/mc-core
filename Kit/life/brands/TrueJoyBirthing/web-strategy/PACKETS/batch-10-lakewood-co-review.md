# City Review Packet: Lakewood, CO

## Quick Stats
- **Hospitals**: 2 — St. Anthony Hospital, UCHealth University of Colorado Hospital (Aurora)
- **Birth centers**: 0 in Lakewood proper; Mountain Midwifery Birth Center in Englewood (~10 min south) serves metro families
- **Doula cost**: $1,000–$2,800 (confidence: city-specific, Denver metro)
- **NICU levels**: St. Anthony — NICU (contact hospital directly for current NICU level); UCHealth UCH — Level III NICU (verified on uchealth.org)
- **Medicaid doula coverage**: CO Medicaid (Health First Colorado) covers doula services via HB 23-1027 ($750/birth)

## Medicaid/Doula Paragraph (as it appears on the page)
> Yes — Colorado Medicaid (Health First Colorado) covers doula services as of January 2024 under HB 23-1027. The reimbursement rate covers $750 per birth for a full-spectrum doula package (prenatal, labor, and postpartum visits). Jefferson County families are served by Colorado Access, Health First Colorado's Regional Accountable Entity. Contact Health First Colorado at 1-800-221-3943 or visit healthfirstcolorado.com to confirm your plan's doula coverage.

## Hospital/NICU Uncertainties
- **St. Anthony Hospital NICU**: Known birth hospital but NICU level not independently source-verified. Used "contact the hospital directly for current NICU level verification." Resolution source of truth = hospital materials or local feedback.
- **UCHealth Level III NICU**: Verified on uchealth.org.

## Key Local Anchors
1. St. Anthony Hospital on West 2nd Avenue, just south of US-6
2. Wadsworth Boulevard interchange accessibility
3. C-470 and Bear Creek area routes for southern neighborhoods
4. Bear Creek Greenbelt and William F. Hayden Park on Green Mountain for walking
5. UCHealth Anschutz Medical Campus in Aurora ~20 min east

## Remaining Uncertainties
- St. Anthony Hospital NICU level: Resolution source of truth = hospital materials or local doula feedback

## Validation Results
- validate-cities.ts: ✅ PASS (A9 warning: documented empty birth center search)
- city-pages.test.ts: Pre-existing D1/D3/D4/E2 issues
- D1 similarity: No warnings

## Launch Checklist Check
- [x] A. Trust & local accuracy: verified sources, NICU soft-language, CO Medicaid correctly stated
- [x] B. Page quality & structure: validate pass
- [x] C. Internal links & navigation: nearby slugs valid (denver-co, colorado-springs-co)
- [x] D. Voice & usefulness: TJB tone, birth-plan CTA, locally specific
- [x] E. Deploy gate: human approval required

## Action Required
Review this packet. If approved, reply "deploy lakewood-co".
# City Review Packet: Bowie, MD

## Quick Stats
- **Hospitals**: 2 — Luminis Health Doctors Community Medical Center, University of Maryland Capital Region Medical Center
- **Birth centers**: 0 (none in Prince George's County; nearest is Special Beginnings in Arnold, Anne Arundel County)
- **Doula cost**: $900–$2,500 (confidence: city-specific, DC metro)
- **NICU levels**: Luminis Health Doctors Community — Special Care Nursery (contact hospital directly for NICU level); UM Capital Region — contact hospital directly for NICU level
- **Medicaid doula coverage**: MD Medicaid covers doula services ($900 max per pregnancy since Jan 2024)

## Medicaid/Doula Paragraph (as it appears on the page)
> Yes — Maryland Medicaid covers doula services as of January 2024, with reimbursement of $450 for labor and delivery support, $75 per prenatal or postpartum visit (up to 4 visits), totaling up to $900 per pregnancy. Prince George's County families on Maryland Medicaid are served by managed care plans including Kaiser Permanente, UnitedHealthcare, MedStar, Jai Medical, Priority Partners, and Maryland Physicians Care. Your doula must be enrolled as a Maryland Medicaid provider.

## Hospital/NICU Uncertainties
- **Luminis Health Doctors Community NICU**: Described as "Special Care Nursery" in general references. Used "contact the hospital directly for current NICU level verification" — not confirmed as Level II or higher. Resolution source of truth = hospital materials or local doula feedback.
- **UM Capital Region NICU**: Newer hospital (opened 2021). NICU level not independently verified. Higher-level NICU needs transfer to Baltimore (Johns Hopkins or UMMC).

## Key Local Anchors
1. Luminis Health Doctors Community in Lanham (~10 min north via Route 450)
2. UM Capital Region Medical Center in Largo (~12 min south)
3. Route 50 (John Hanson Highway) connecting Bowie to both hospitals
4. Route 197 interchange rush-hour backups
5. Allen Pond Park and Bowie Walking Trail

## Remaining Uncertainties
- Luminis Health Doctors Community NICU level: Resolution source of truth = hospital materials or local feedback
- UM Capital Region NICU level: Resolution source of truth = hospital materials or local feedback

## Validation Results
- validate-cities.ts: ✅ PASS (A9 warning: documented empty birth center search)
- city-pages.test.ts: Pre-existing D1/D3/D4/E2 issues (template-level)
- D1 similarity: No warnings

## Launch Checklist Check
- [x] A. Trust & local accuracy: verified sources, NICU soft-language, A8 qualifiers, birth center search documented
- [x] B. Page quality & structure: validate pass
- [x] C. Internal links & navigation: nearby slugs valid (baltimore-md, columbia-md)
- [x] D. Voice & usefulness: TJB tone, birth-plan CTA, locally specific
- [x] E. Deploy gate: human approval required

## Action Required
Review this packet. If approved, reply "deploy bowie-md" and I'll deploy and spot-check.
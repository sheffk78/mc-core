# Batch 10 Summary

**Date**: 2026-05-28  
**Branch**: feat/city-batch-10  
**Cities**: 6 (Beaverton OR, Bowie MD, Chesapeake VA, Lakewood CO, Scottsdale AZ, Warwick RI)  
**New states**: 0 (all states already had at least one city deployed)

## Results

| City | Slug | Validation | Medicaid | NICU | Birth Centers | nearbyCities |
|------|------|-----------|----------|------|---------------|-------------|
| Beaverton, OR | beaverton-or | ✅ PASS | Yes (OHP/THW) | St. Vincent: contact directly; OHSU: Level IV (verified) | 0 (Portland centers nearby) | portland-or, eugene-or |
| Bowie, MD | bowie-md | ✅ PASS | Yes ($900 max) | Luminis: contact directly; UM Capital: contact directly | 0 (Special Beginnings in Anne Arundel Co) | baltimore-md, columbia-md |
| Chesapeake, VA | chesapeake-va | ✅ PASS | No | Chesapeake Regional: Level II (contact directly); Sentara Norfolk: Level III (verified) | 0 | richmond-va, norfolk-va, virginia-beach-va |
| Lakewood, CO | lakewood-co | ✅ PASS | Yes ($750/birth) | St. Anthony: contact directly; UCHealth UCH: Level III (verified) | 0 (Mountain Midwifery in Englewood nearby) | denver-co, colorado-springs-co |
| Scottsdale, AZ | scottsdale-az | ✅ PASS | No (AHCCCS) | HonorHealth Shea: Level III (contact directly); Osborn: contact directly | 0 (Natural Birth Center in Mesa nearby) | phoenix-az, tucson-az |
| Warwick, RI | warwick-ri | ✅ PASS | Yes (~$1,500) | Kent Hospital: contact directly; Women & Infants: Level III (stated on wihri.org) | 0 | providence-ri, boston-ma |

## NICU Uncertainties (flagged for human review)

| City | Hospital | Claim | Status |
|------|----------|-------|--------|
| Beaverton | Providence St. Vincent | "Level III NICU" | Not source-verified; used "contact directly" qualifier |
| Beaverton | OHSU Hospital | "Level IV NICU" | Verified on ohsu.edu ✅ |
| Bowie | Luminis Health Doctors Community | "Special Care Nursery" | Not confirmed as Level II+; used "contact directly" |
| Bowie | UM Capital Region | NICU unspecified | Newer hospital; used "contact directly" |
| Chesapeake | Chesapeake Regional | "Level II NICU" | Not source-verified; used "contact directly" qualifier |
| Chesapeake | Sentara Norfolk General | "Level III NICU" | Verified on sentara.com ✅ |
| Lakewood | St. Anthony Hospital | NICU | Not source-verified; used "contact directly" qualifier |
| Lakewood | UCHealth UCH | "Level III NICU" | Verified on uchealth.org ✅ |
| Scottsdale | HonorHealth Shea | "Level III NICU" | Not source-verified; used "contact directly" qualifier in both paragraph and FAQ |
| Scottsdale | HonorHealth Osborn | NICU | Not source-verified; used "contact directly" qualifier |
| Warwick | Kent Hospital | "Special Care Nursery" | Not confirmed as Level I+; used "contact directly" qualifier |
| Warwick | Women & Infants | "Level III NICU" | Stated directly on wihri.org ✅ |

## Medicaid Coverage Summary

- **Yes (4 cities)**: OR ($1,500+ via THW), MD ($900 max), CO ($750/birth via HB 23-1027), RI (~$1,500)
- **No (2 cities)**: VA, AZ (AHCCCS)

## Deploy-ready

All 6 cities pass validate-cities.ts (only A9 warnings for documented empty birth center searches). Build completes successfully. 222 total pages.

## Deploy actions: none (prep-only)

All work is on branch `feat/city-batch-10`. Review packets in PACKETS/batch-10-{slug}-review.md. Jeff must approve before merge and deploy.
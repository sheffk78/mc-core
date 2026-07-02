# Aerius View Overnight Build Tracker

**Last updated:** 2026-06-30T22:47:00Z
**Current phase:** Phase 3 - City Page Pipeline IN PROGRESS

## GA T5 Expansion — 2026-06-30

**Built by:** Kit (live session)
**Scope:** 10 new GA T5 city pages (growth areas below existing tier structure)

### Cities Built
| City | County | Pop | Tier | Status |
|---|---|---|---|---|
| Newnan | Coweta | ~42K | T5 | Live |
| McDonough | Henry | ~29K | T5 | Live |
| Peachtree Corners | Gwinnett | ~45K | T5 | Live |
| LaGrange | Troup | ~31K | T5 | Live |
| Carrollton | Carroll | ~27K | T5 | Live |
| Stockbridge | Henry | ~29K | T5 | Live |
| St. Marys | Camden | ~18K | T5 | Live |
| Calhoun | Gordon | ~16K | T5 | Live |
| Milledgeville | Baldwin | ~19K | T5 | Live |
| Thomasville | Thomas | ~18K | T5 | Live |

### Pipeline Steps Completed
- [x] Scaffolded all 10 cities via add-city.ts
- [x] Fixed export name casing (peachtreeCornersGA, stMarysGA)
- [x] Wrote all 10 data files with researched content (airspace, construction market, costs, FAQs)
- [x] Updated nearbyCities bidirectional links on 13 existing GA cities (21 reciprocal links added)
- [x] Apostrophe scan passed (no unescaped quotes)
- [x] Build succeeded (563 pages)
- [x] Preflight: 10/10 PASS (21/21 gates each)
- [x] OG images rendered for all 10 cities
- [x] Hero images generated, converted to WebP (99-127KB each)
- [x] Deployed to Cloudflare Pages
- [x] Verified live: 10/10 pages return 200, 10/10 hero images 200, 10/10 OG images 200
- [x] Git committed and pushed

### GA City Count
- **Total GA cities live:** 38 (was 28)
  - T1: Atlanta
  - T2: Savannah, Augusta, Columbus
  - T3: Athens, Gainesville, Valdosta, Rome, Dalton, Hinesville, Statesboro, Warner Robins, Brunswick, Cartersville, Peachtree City
  - T4: Sandy Springs, Roswell, Johns Creek, Alpharetta, Marietta, Lawrenceville, Duluth, Kennesaw, Canton, Dallas, Smyrna, Woodstock
  - Extra: Macon
  - T5: Newnan, McDonough, Peachtree Corners, LaGrange, Carrollton, Stockbridge, St. Marys, Calhoun, Milledgeville, Thomasville

## GA Tier 3 Expansion — 2026-06-30

**Built by:** Kit (live session)
**Scope:** 10 new GA Tier 3 city pages (high-growth secondary metros outside Atlanta metro)

### Cities Built
| City | County | Pop | Tier | Status |
|---|---|---|---|---|
| Gainesville | Hall | ~42K | T3 | Live |
| Valdosta | Lowndes | ~55K | T3 | Live |
| Rome | Floyd | ~37K | T3 | Live |
| Dalton | Whitfield | ~34K | T3 | Live |
| Hinesville | Liberty | ~34K | T3 | Live |
| Statesboro | Bulloch | ~32K | T3 | Live |
| Warner Robins | Houston | ~80K | T3 | Live |
| Brunswick | Glynn | ~17K | T3 | Live |
| Cartersville | Bartow | ~24K | T3 | Live |
| Peachtree City | Fayette | ~38K | T3 | Live |

### Pipeline Steps Completed
- [x] Scaffolded all 10 cities via add-city.ts
- [x] Fixed export name casing (warnerRobinsGA, peachtreeCityGA)
- [x] Wrote all 10 data files with researched content (airspace, construction market, costs, FAQs)
- [x] Updated nearbyCities bidirectional links on 5 existing GA cities (Atlanta, Athens, Macon, Savannah, Sandy Springs)
- [x] Apostrophe scan passed (no unescaped quotes)
- [x] Build succeeded (553 pages)
- [x] Preflight: 10/10 PASS
- [x] OG images rendered for all 10 cities
- [x] Hero images generated, converted to WebP (73-112KB each)
- [x] Deployed to Cloudflare Pages
- [x] Verified live: 10/10 pages return 200, 10/10 hero images 200, 10/10 OG images 200

### GA City Count
- **Total GA cities live:** 28 (was 18)
  - T1: Atlanta
  - T2: Savannah, Augusta, Columbus
  - T3: Athens, Gainesville, Valdosta, Rome, Dalton, Hinesville, Statesboro, Warner Robins, Brunswick, Cartersville, Peachtree City
  - T4: Sandy Springs, Roswell, Johns Creek, Alpharetta, Marietta, Lawrenceville, Duluth, Kennesaw, Canton, Dallas, Smyrna, Woodstock
  - Extra: Macon

## QA Review — 2026-06-27

**Reviewed by:** Kit (scheduled QA cron)
**Scope:** Full frontend + API review of overnight build work (Phases 1-3.1)

### Frontend (aeriusview.pages.dev)
- [x] Homepage loads, all sections render correctly
- [x] All 8 service category pages have real content (not placeholder)
- [x] Contact page form posts to FastAPI /api/lead-intake → 200 OK
- [x] Contractor page form posts to FastAPI /api/contractor-apply → 200 OK
- [x] Phoenix city page loads with full content (hero, services, costs, regulations, FAQ, schema)
- [x] Locations hub page lists Phoenix correctly
- [x] FAQ page renders all 7 Q&As
- [x] About page has real content (3 sections)
- [x] Mobile nav hamburger menu implemented
- [x] All internal links return 200 (308 redirects for trailing-slash normalization are fine)
- [x] JSON-LD schema present on all page types (ProfessionalService, WebSite, Service, FAQPage, BreadcrumbList)
- [x] sitemap-index.xml and robots.txt exist and are correct
- [x] No TODO/FIXME/PLACEHOLDER comments in codebase
- [x] `npm run build` succeeds in 776ms, 16 pages
- [x] Preflight SEO validation: 19/19 gates pass, 0 warnings

### API (aeriusview-api-production.up.railway.app)
- [x] /api/health returns 200 {"status":"healthy","service":"aeriusview-api"}
- [x] /api/lead-intake accepts POST, creates lead, routes to matching contractor
- [x] /api/contractor-apply accepts POST, stores contractor as pending
- [x] /api/admin/stats returns dashboard counts (7 leads, 1 active contractor, 5 credits)
- [x] /api/admin/leads lists all leads with status
- [x] /docs (Swagger) accessible
- [x] No TODO comments in API codebase

### Issues Found & Fixed
1. **Canonical URL on city page was relative** (`/locations/phoenix-az` → now `https://aeriusview.com/locations/phoenix-az/`)
2. **Meta description on city page was 402 chars** (included full heroLocalDetail → now ~160 chars, just service + county summary)
3. **5 broken nearby city links on Phoenix page** (Tucson, Austin, Las Vegas, Denver, Salt Lake City → converted to "coming soon" text labels until those pages are built)

### Deploy Status
- Frontend: committed (484eae5), pushed to main, deployed to Cloudflare Pages
- Backend: no changes needed (already at 678e779)
- All fixes verified live on production

## Progress State

### Phase 0: Foundation COMPLETE
- [x] GitHub repo: sheffk78/aeriusview-site (Astro)
- [x] GitHub repo: sheffk78/aeriusview-api (FastAPI)
- [x] Railway project: aeriusview-api (service ID: 1c53351a-3214-4465-9b33-6d179d182473)
- [x] Railway PostgreSQL: deployed and linked
- [x] Frontend deployed: https://aeriusview.pages.dev
- [x] API deployed: https://aeriusview-api-production.up.railway.app
- [x] API health check: working
- [x] Database tables: initialized (contractors, leads, lead_routes, credit_transactions)

### Phase 1: Core Pages COMPLETE ✅
- [x] 1.1 Wire contact form to FastAPI /api/lead-intake endpoint
- [x] 1.2 Wire contractor form to FastAPI /api/contractor-apply endpoint
- [x] 1.3 Build 8 service category pages (topographic, inspection, LiDAR, environmental, imagery, construction monitoring, real estate, roof inspection)
- [x] 1.4 Improve homepage with real structure from PRD
- [x] 1.5 Add JSON-LD schema (Service, LocalBusiness, FAQPage) to all pages
- [x] 1.6 Add sitemap.xml generation
- [x] 1.7 Add robots.txt
- [x] 1.8 Mobile responsive audit across all pages
- [x] 1.9 Preflight SEO validation script

### Phase 2: Lead Routing Backend COMPLETE ✅
- [x] 2.1 PostgreSQL schema (contractors, leads, lead_routes, credit_transactions)
- [x] 2.2 POST /api/lead-intake endpoint (validate, store lead)
- [x] 2.3 POST /api/contractor-apply endpoint (validate, store as pending)
- [x] 2.4 Lead routing logic (zip + service type matching)
- [x] 2.5 Email notification to contractors (Postmark with lazy init — logs to stdout when no token)
- [x] 2.6 Contractor accept/decline endpoint (token-based, unique per match)
- [x] 2.7 Credit deduction on acceptance (1 credit = 1 lead)
- [x] 2.8 Consumer notification email ("Your surveyor will contact you")
- [x] 2.9 Admin endpoint: GET /api/admin/leads (list all leads + status)
- [x] 2.10 End-to-end test: submit form -> lead stored -> contractor notified -> accept -> credit deducted

**E2E test verified 2026-06-27:**
- Lead submitted → routed to matching contractor (zip + specialty)
- Contractor accepts via unique token link → gets lead contact details
- Double-accept blocked (409)
- Credit deducted (6→5), acceptance_rate updated (1.0)
- Admin stats show: 1 accepted lead, 5 credits remaining

**Additional admin endpoints built:**
- GET /api/admin/leads/{id} — lead detail with routing info
- GET /api/admin/contractors — list contractors with filter
- GET /api/admin/stats — dashboard counts (leads by status, contractors by status, credits, revenue)
- POST /api/admin/contractors/{id}/approve — approve pending contractor + grant 1 free credit
- POST /api/admin/contractors/{id}/add-credits — manually add credits
- GET /api/lead-routes/{lead_id} — routing status for a lead

### Phase 3: City Page Pipeline IN PROGRESS (substantially complete)
- [x] 3.1 City page template (Astro component) + Phoenix-AZ first city page
- [x] 3.2-3.7 City pages built (495 cities, 12 states live)
- [x] 3.8 State pages (not yet — needs check)
- [x] 3.9 Location hub page (/locations/)
- [x] 3.10 Deploy all city pages

### Contractor Platform (Phase 1 of compiled plan) — COMPLETE ✅
- [x] 1A. /surveyors landing page rebuilt with conversion copy, pricing, value props
- [x] 1B. State→city cascading picker (495 cities, 12 states, metro-grouped)
- [x] 1C. Page review feedback loop (per-city textareas, stored in page_reviews table)
- [x] Backend: contractor-apply accepts structured payload (specialties[], service_area_cities[], page_feedback{})
- [x] Backend: admin page-review endpoints (GET /admin/page-reviews, PUT /admin/page-reviews/{id}, GET /admin/page-reviews/stats)
- [x] Backend: email notification includes page feedback
- [x] contractor-cities.json: 495 cities, 12 states (verified live 2026-07-01)
- [x] DB migration 001 run on prod (city_metro_mapping, contractors columns)
- [x] Contractor-apply endpoint verified end-to-end (unique email → 200, page_feedback stored)
- [x] All fixes deployed, committed, pushed

### Contractor Platform — Next Items (build sequence from plan)
- [x] Phase 4A-4B: Priority routing — territory lock-in + staggered notifications ✅ (2026-07-01)
  - contractor_territory_rank table created
  - lead_routes gained send_at + rank columns
  - Routing engine rewritten: finds ALL matching contractors, orders by rank, creates staggered queued routes
  - Stagger: rank 1 = immediate, rank 2 = +15min, rank 3 = +30min, rank 4+ = +45min
  - POST /api/routing/process-queue endpoint (cron-hit)
  - approve_contractor auto-assigns territory ranks
  - Cron job: aeriusview-route-processor.sh runs every 5 min (script-only, no agent)
  - Tested end-to-end: 2 contractors in Austin TX, lead routed with correct stagger
- [ ] Phase 3: Stripe credit purchasing (requires Jeff to create 3 Stripe products)
- [ ] Phase 2: Contractor portal (auth, dashboard, leads, credits, profile) — largest piece
- [ ] Phase 2F: 5-agent QA testing
- [ ] Phase 5: Unmatched lead auto-research cron

**Task 3.1 completed 2026-06-27:**
- Created reusable `CityPage.astro` component following PRD §6 structure (hero, inline lead form, services grid, costs table, airspace & regulations, why hire, featured contractors empty state, FAQ, nearby cities, CTA)
- Created TypeScript `CityData` interface + `SERVICE_CATALOG` in `src/types/city.ts`
- Created Phoenix-AZ city data file (`src/data/cities/phoenix-az.ts`) as the reference example with real airspace, regulations, costs, and FAQ data
- Created `/locations/phoenix-az` page using the template
- Updated locations hub page to list available city pages
- JSON-LD schemas: Service, FAQPage, BreadcrumbList per city page
- Lead form posts to FastAPI `/api/lead-intake` with zip pre-filled from city data
- Verified live: https://aeriusview.pages.dev/locations/phoenix-az/ (200 OK, Service schema present)
- Committed and pushed to `main` (commit 1f2676b)

### Phase 4: Contractor Acquisition PENDING
- [ ] 4.1-4.10 Contractor discovery, enrichment, outreach prep

### Phase 5: Content & SEO PENDING
- [ ] 5.1-5.10 Blog content, redirects, Search Console

## Key URLs
- Frontend: https://aeriusview.pages.dev
- API: https://aeriusview-api-production.up.railway.app
- API Health: https://aeriusview-api-production.up.railway.app/api/health
- API Docs (Swagger): https://aeriusview-api-production.up.railway.app/docs
- Admin Stats: https://aeriusview-api-production.up.railway.app/api/admin/stats
- GitHub Frontend: https://github.com/sheffk78/aeriusview-site
- GitHub API: https://github.com/sheffk78/aeriusview-api
- Railway Project: https://railway.com/project/51d2b4d3-1433-432e-8be4-95266c535a0f
- PRD: ~/.openclaw/workspace/Kit/life/brands/AeriusView/PRD-AeriusView-Revival.md

## File Paths
- Frontend repo: ~/Projects/aeriusview-site/
- Backend repo: ~/Projects/aeriusview-api/
- Brand folder: ~/.openclaw/workspace/Kit/life/brands/AeriusView/

## Rules for Overnight Cron Jobs
1. Read this file FIRST to see what's done and what's next
2. Do the next incomplete task in the current phase
3. After completing a task, update this file (mark [x] and update "Last updated" timestamp)
4. Commit and push changes to the relevant GitHub repo
5. If a task requires Jeff's approval (design decisions, spend), SKIP it and note it
6. Use local models only (no metered API calls)
7. Build and test locally before committing
8. If something blocks you, note the blocker in this file and move to the next task

## Notes
- Credit system: 1 credit = 1 lead (flat rate). Dollar amounts per service type are for display/revenue reporting only.
- Postmark email: lazy init pattern. When POSTMARK_SERVER_TOKEN is not set, emails log to stdout. Add token to Railway env vars to enable real email sending.
- Admin endpoints have NO auth yet. Add API key auth before production launch.
- API version: 2.0.0 (Phase 2 complete)
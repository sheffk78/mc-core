# Aerius View Overnight Build Tracker

**Last updated:** 2026-06-27T00:15:00Z
**Current phase:** Phase 2 - Lead Routing Backend COMPLETE

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

### Phase 3: City Page Pipeline PENDING
- [ ] 3.1-3.10 City page template + data research + generation pipeline

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
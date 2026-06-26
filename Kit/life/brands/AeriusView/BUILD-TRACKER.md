# Aerius View Overnight Build Tracker

**Last updated:** 2026-06-26T22:10:00Z
**Current phase:** Phase 1 - Core Pages (mobile audit done, preflight SEO validation next)

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

### Phase 1: Core Pages IN PROGRESS
- [x] 1.1 Wire contact form to FastAPI /api/lead-intake endpoint
- [x] 1.2 Wire contractor form to FastAPI /api/contractor-apply endpoint
- [x] 1.3 Build 8 service category pages (topographic, inspection, LiDAR, environmental, imagery, construction monitoring, real estate, roof inspection)
- [x] 1.4 Improve homepage with real structure from PRD
- [x] 1.5 Add JSON-LD schema (Service, LocalBusiness, FAQPage) to all pages
- [x] 1.6 Add sitemap.xml generation
- [x] 1.7 Add robots.txt
- [x] 1.8 Mobile responsive audit across all pages
- [ ] 1.9 Preflight SEO validation script

### Phase 2: Lead Routing Backend PENDING
- [ ] 2.1-2.10 Full lead routing with email notifications, accept/decline, credit deduction

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
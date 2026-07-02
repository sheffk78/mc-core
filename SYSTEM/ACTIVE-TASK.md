# ACTIVE TASK

**Mission:** AeriusView Contractor Platform Build — resume phased build after DB migration fix

**Status:** Phase 1 (landing page + registration + page feedback) COMPLETE and verified live. Ready to start Phase 4A-4B (priority routing backend).

**Completed this session:**
- Fixed 3 bugs found in post-migration verification: admin page-review route double-prefix, contractor-cities.json missing 302 cities, stale deployed JSON
- All fixes deployed to Railway + Cloudflare Pages, committed, pushed
- Contractor-apply endpoint verified end-to-end with unique email
- contractor-cities.json verified: 495 cities, 12 states
- Admin page-review endpoints verified: working, showing test feedback

**Next (build sequence from plan):**
1. Phase 4A-4B: Priority routing — territory lock-in + staggered notifications (0.5 day)
2. Phase 3: Stripe credit purchasing — needs Jeff to create 3 Stripe products ($150/$275/$500)
3. Phase 2: Contractor portal — auth, dashboard, leads, credits, profile (2-3 days)
4. Phase 2F: 5-agent QA testing
5. Phase 5: Unmatched lead auto-research cron

**Decisions still needed from Jeff:**
- Stripe products: 3 tiers at $150/5, $275/10, $500/20 credits. Confirm pricing?
- 15-minute stagger interval for priority notifications?
- Magic link auth (email-only, no passwords)?
- Contractor approval: manual or auto?
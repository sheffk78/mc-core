# AeriusView Demand Generation Execution Plan

**Created:** July 21, 2026
**Phase:** 3 — Demand Generation (Weeks 3-6 of roadmap)
**Owner:** Jeff
**Goal:** Validate that qualified buyers (GCs, engineering firms) will post real drone projects, and that 30+ qualified leads/month flow through 5 priority metros within 8 weeks.

**Source docs:** `PLANS/strategy-v2.md`, `ACTIVE-TASK.md`

---

## 1. Direct Outbound to Buyers

### 1.1 Target Metros (5)

Prioritized by (a) existing city-page traffic signals, (b) construction spend density, (c) operator supply already in pipeline:

| # | Metro | Why | Lead Target (wk 6) |
|---|---|---|---|
| 1 | **Austin, TX** | Top construction-spend growth, 3+ contractors in Batch 1 outreach, city page live | 8 leads/mo |
| 2 | **Denver, CO** | Strong civil/earthwork market, LiDAR-friendly ecosystem, city page live | 6 leads/mo |
| 3 | **Phoenix, AZ** | Massive master-plan communities, multi-quarry aggregates, city page live | 6 leads/mo |
| 4 | **Salt Lake City, UT** | AGC Utah chapter strong, engineering firm density, city page live | 5 leads/mo |
| 5 | **Seattle, WA** | Tech-forward GCs, infrastructure spend (Light Rail expansion), city page live | 5 leads/mo |

**Total target: 30+ qualified leads/month across 5 metros by week 8.**

### 1.2 Prospect List Sources

For each metro, build a list of 30-50 buyer-side contacts (target 200 total across 5 metros):

| Source | Who | How | Cost |
|---|---|---|---|
| **AGC Member Directories** | Member GC rosters per chapter (AGC of Texas, AGC of Colorado, etc.) | Scrape chapter websites, download member PDFs | Free (members) |
| **ENR Top Lists** | ENR Texas, Mountain West, Pacific Northwest top GCs ($50M-$500M) | enr.com/toplists (filtered by region + revenue band) | Free |
| **LinkedIn Sales Navigator** | Project engineers, VPs of Construction, Preconstruction Managers at mid-market GCs | Filter: title (Preconstruction, Project Engineer, VP Construction, Survey Manager), company size 50-500, geo = metro radius | ~$80/mo |
| **Dodge Construction Network** | Projects in design/bidding phase in each metro | Free Dodge leads portal, filtered by project stage | Free tier |
| **State DOT contractor listings** | Heavy-civil firms doing DOT work (volumetrics, earthwork) | TxDOT, CDOT, ADOT, UDOT, WSDOT awarded-contractor databases | Free |
| **AGC chapter event rosters** | Mid-market GCs who show up to chapter meetings | Download attendee lists from AGC chapter event pages | Free (members) |

**Ideal buyer profile per contact:**
- Title: Preconstruction Manager, Project Engineer, VP of Operations, Survey/Field Technology Manager, or Chief Estimator
- Company: GC or engineering firm, $50M-$500M annual revenue, 50-500 employees
- Project mix: includes earthwork, site development, or infrastructure (volumetrics/progress monitoring signals)

### 1.3 Outreach Script / Sequence (5-touch, 14-day)

Send from `outreach@aeriusview.com` (subdomain-separated per strategy-v2). Sign as Jeff. ZeroBounce-verify all emails before sending. One buyer per company per metro.

**Touch 1 — Day 0 (Tuesday send): Hook with a real scenario**

> Subject: Drone work for [Company] — stockpile volumes & progress shots
>
> Hi [First],
>
> I run AeriusView — we connect GCs with FAA-certified drone operators for construction progress monitoring, stockpile volume estimates, and 3D site capture.
>
> We just placed a 3,800-acre LiDAR project in [Metro] and have vetted operators in [City] ready for project work. No subscription, no platform fee — you post a project, we send one qualified operator, you pay nothing to post.
>
> Are you doing any drone work in-house right now, or outsourcing it?
>
> Jeff
> Jeff Anderson, AeriusView
> (512) 555-0143

**Touch 2 — Day 4: Use-case specificity**

> Subject: Re: Drone work for [Company]
>
> [First],
>
> Quick follow-up. Most GCs we talk to in [Metro] are doing one of three things:
> 1. Monthly progress orthomosaics for owner reporting
> 2. Stockpile volume estimates for earthwork reconciliation
> 3. Pre-pour site verification with 3D reality capture
>
> If any of those fit, I can send you a sample deliverable from a vetted operator in your area. 2 minutes to post a project, no commitment.
>
> Jeff

**Touch 3 — Day 7: Proof point**

> Subject: How [similar GC] cut earthwork reconciliation time
>
> [First],
>
> [Short 2-sentence case study: a GC (anonymized or named with permission) used AeriusView for monthly stockpile volumes, reduced surveyor callout time from 2 weeks to 48 hours.]
>
> Happy to set up a 10-minute call to show how it works. What works better, Tuesday or Thursday morning?
>
> Jeff

**Touch 4 — Day 10: Low-friction ask**

> Subject: One question
>
> [First],
>
> One question: what's the biggest pain with your current drone work (or not having any)?
>
> Either way, I'll stop reaching out after this.
>
> Jeff

**Touch 5 — Day 14: Breakup + soft handoff**

> Subject: Closing the loop
>
> [First],
>
> I'll stop here — don't want to crowd your inbox. If drone project work comes up, you can post it here: aeriusview.com/post-project (2 minutes, no fee).
>
> If it's easier to text, my cell is (512) 555-0143.
>
> Jeff

### 1.4 What We Offer (Value Proposition to Buyers)

| Offer | Detail |
|---|---|
| **Free to post** | No platform fee, no subscription, no commitment |
| **One vetted operator** | Not 5 quotes — one matched, vetted contractor with COI on file |
| **Pre-qualified leads** | We collect budget, timeline, site address, deliverable spec — before matching |
| **Airspace pre-check** | Automatic LAANC/airspace check on your site address before dispatch |
| **Sample deliverables** | We show you actual project outputs (not highlight reels) from the matched operator before you commit |
| **No disintermediation risk** | We don't lock you in — you keep the operator relationship if you want |

### 1.5 Tracking

Track in a shared spreadsheet (`PLANS/buyer-outreach-tracker.csv`) with columns:
- Metro, Company, Contact Name, Title, Email, Phone, Source, Tier (A/B/C), Send Date, Touch #, Reply (Y/N), Reply Date, Reply Sentiment, Meeting Booked, Project Posted, Lead Quality Score

**Weekly review:** Friday 4pm, Jeff reviews reply rates per metro and per source.

**Target reply rate:** 15%+ (buyer cold outreach benchmarks). Below 10% = revise script. Above 20% = scale that metro's list faster.

---

## 2. Google Ads Test ($1,500)

### 2.1 Budget

- **Total test budget:** $1,500 over 4 weeks
- **Daily cap:** ~$50/day
- **Metro allocation:** $300/metro × 5 metros (Austin, Denver, Phoenix, SLC, Seattle)
- **Match type:** Phrase + exact (no broad)

### 2.2 Use-Case Keywords (NOT category keywords)

Strategy-v2 is explicit: bid on use-case intent, not "drone surveying" category terms.

| Cluster | Keywords | Match | Rationale |
|---|---|---|---|
| **Stockpile volume** | "stockpile volume estimates", "stockpile measurement", "drone stockpile calculation", "aggregate volume survey", "stockpile report" | Phrase + exact | Aggregates/quarries, earthwork GCs — Professional tier ($75-200/lead) |
| **Construction progress** | "construction progress monitoring", "construction drone progress report", "monthly progress drone photos", "construction site aerial documentation", "drone progress tracking" | Phrase + exact | Mid-market GCs, developers — Professional tier |
| **LiDAR scanning** | "drone LiDAR scanning services", "aerial LiDAR for construction", "3D reality capture construction", "drone 3D scanning", "LiDAR topographic data" | Phrase + exact | Engineering firms — Premium tier ($200-500/lead) |
| **Topographic / earthwork** | "drone topographic data collection", "drone earthwork volume", "site survey drone services" (negative: "land surveyor") | Phrase + exact | Site development GCs — Professional tier |
| **Construction progress monitoring (as-built)** | "drone as-built documentation", "as-built 3D model drone", "drone as-built data collection" | Phrase + exact | MEP/structural firms — Professional tier (covered by construction_progress canonical service) |

**Negative keywords (critical):**
`-land surveyor`, `-licensed surveyor`, `-free`, `-DIY`, `-how to`, `-job`, `-training`, `-certification course`, `-insurance claim`, `-roof inspection` (real estate tier — different funnel)

### 2.3 Ad Copy

**Ad Group 1: Stockpile Volume**

> **H1:** Stockpile Volume Estimates — Drone Data in 48 Hours
> **D1:** Vetted FAA-certified drone operators. Stockpile volume reports for earthwork reconciliation. Free to post. One matched operator. No platform fee.
> **D2:** Get accurate stockpile volume estimates from vetted local drone operators. Post your project free. We match one qualified operator. No subscription.

**Ad Group 2: Construction Progress**

> **H1:** Construction Progress Drone Monitoring — Monthly Reports
> **D1:** Orthomosaic progress maps, aerial site documentation, owner-ready progress reports. Vetted local operators. Free to post. No platform fee.
> **D2:** Monthly aerial progress photos, orthomosaic site maps, and 3D site capture. Post your project free. One vetted operator matched. No subscription.

**Ad Group 3: LiDAR Scanning**

> **H1:** Drone LiDAR Scanning — 3D Reality Capture for Construction
> **D1:** Aerial LiDAR data collection, 3D terrain models, topographic data for engineering firms. Vetted RTK/PPK operators. Free to post. No platform fee.
> **D2:** LiDAR scanning and 3D reality capture from vetted local drone operators. Post your project free. One qualified match. No subscription.

### 2.4 Landing Pages

**Do NOT send to homepage or city pages.** Build 3 dedicated use-case landing pages (one per ad group):

| URL | Headline | CTA |
|---|---|---|
| `aeriusview.com/use-cases/stockpile-volume-estimates` | "Stockpile Volume Estimates from Vetted Drone Operators" | "Post a Stockpile Project" (2-min form) |
| `aeriusview.com/use-cases/construction-progress-monitoring` | "Monthly Drone Progress Reports for Your Job Site" | "Post a Progress Project" |
| `aeriusview.com/use-cases/lidar-3d-scanning` | "Aerial LiDAR & 3D Reality Capture, Vetted Local Operators" | "Post a LiDAR Project" |

Each landing page:
- Use-case hero (headline + 1-line value prop + CTA button above fold)
- 3 trust signals: "FAA-certified operators", "COI on file", "Sample deliverables before you commit"
- Inline lead form: Project type, Site address, Timeline, Budget range, Name, Email, Phone (matches strategy-v2 intake spec)
- Airspace pre-check callout: "We verify airspace/LAANC on your site address before dispatch"
- Disclaimer footer (terminology compliance per strategy-v2)

### 2.5 Conversion Tracking

| Event | Track via | Goal |
|---|---|---|
| Form submission (lead posted) | Google Ads conversion + GA4 event `lead_posted` | 10+ conversions in 4 weeks |
| Phone call (call tracking #) | Google Ads call conversion | 3+ calls |
| Click to email | GA4 event `email_click` | Track |
| Cost per qualified lead | Ads cost / qualified leads (post-spam-filter) | <$150 target |
| Landing page bounce rate | GA4 | <65% |

Use a dedicated call tracking number per metro (via OpenPhone or similar) so we can attribute calls back to the metro campaign.

**Kill criteria:** If after week 2, cost per lead >$250 AND no qualified leads, pause and diagnose. Don't burn the full $1,500 without signal.

---

## 3. GC Interview Script (10 Interviews)

### 3.1 Target

- **10 interviews** with preconstruction managers, VPs of construction, or survey/field-tech managers at mid-market GCs ($50M-$500M revenue)
- 2 interviews per metro (Austin, Denver, Phoenix, SLC, Seattle)
- **Recruit via AGC chapters** — Jeff (or delegate) attends or cold-emails chapter members:
  - AGC of Texas (Austin)
  - AGC of Colorado (Denver)
  - AGC of Arizona (Phoenix)
  - AGC of Utah (SLC)
  - AGC of Washington (Seattle)
- **Incentive:** Offer a free sample drone deliverable (orthomosaic or stockpile report) for their next project, no strings. Or a $50 Amazon gift card.

### 3.2 Recruiting Script

> Hi [First],
>
> I'm Jeff with AeriusView — we're a drone project lead platform for commercial construction. I'm doing research on how mid-market GCs use (or don't use) drone work, and I'd love 15 minutes of your time.
>
> In exchange, I'll comp a drone orthomosaic or stockpile report on your next project — free, no strings.
>
> Does Tuesday or Thursday this week work for a quick call?

### 3.3 Interview Script (10 Questions, 15-20 min)

**Section A: Current State (3 questions)**

1. "How does your company handle aerial/drone work today — in-house, outsourced, or not doing it?"
   - If outsourced: "Who do you use, and how did you find them?"
   - If in-house: "What equipment and software? How many pilots on staff?"
   - If none: "What would it take for you to start?"

2. "What drone deliverables do you actually use — orthomosaics, progress photos, stockpile volumes, LiDAR, 3D models? Which ones matter most?"

3. "How often do you need drone work — monthly, quarterly, project-based?"

**Section B: Pain Points (3 questions)**

4. "What's the biggest pain with your current drone work process? (scheduling, quality, cost, deliverable format, operator reliability)"
   - Probe: "Is it finding operators, or trusting the deliverable quality?"

5. "Have you ever had a drone deliverable that didn't meet expectations? What went wrong?"

6. "What would make you trust a drone operator you've never worked with before?"
   - Probe: "COI? Sample deliverables? Accuracy methodology? References?"

**Section C: Buying Process (2 questions)**

7. "When you need drone work for a new project, what's the process — who approves it, what's the budget range, how long does it take to get an operator on-site?"

8. "What's the typical budget per drone project? And for recurring monthly work?"

**Section D: Platform Validation (2 questions)**

9. "If a platform matched you with one vetted operator (COI verified, sample deliverables shown), collected your project specs, and you paid nothing to post — would you use that?"

10. "What would stop you from using it? What's the dealbreaker?"

### 3.4 Data to Collect

Record (with permission) and log in `PLANS/gc-interview-logs.md`:

| Field | Why |
|---|---|
| Company name, revenue band, employee count | Segment fit |
| Metro | Geo validation |
| Current drone usage (in-house/outsourced/none) | Market state |
| Deliverable types used | Product spec validation |
| Frequency (monthly/quarterly/project) | Recurring revenue signal |
| Top pain point | Messaging input |
| Budget per project / per month | Pricing validation |
| Trust factors required | Operator profile spec |
| Platform interest (1-5 scale) | Demand signal |
| Dealbreakers | Objection handling |
| Would they post a project in next 30 days? | Hot lead |

**Output:** After 10 interviews, write a 1-page summary in `PLANS/gc-interview-summary.md` answering:
- Top 3 pains (ranked by frequency)
- Top 3 trust factors
- Average budget range
- % who would use the platform
- Top 3 dealbreakers
- Recommended pricing tier adjustments (if any)

---

## 4. Tracking Dashboard

### 4.1 Metrics to Track

| Metric | Source | Target (wk 8) |
|---|---|---|
| Qualified leads posted (total) | AeriusView DB (lead-intake table) | 30+/month across 5 metros |
| Leads per metro | DB, filtered by metro | 5-8/metro/month |
| Lead-to-operator match rate | DB (matched vs. unmatched) | >60% |
| Buyer reply rate (outbound) | Outreach tracker | >15% |
| Meetings booked (outbound) | Calendar | 10+ |
| Ads: impressions, clicks, CTR, CPC | Google Ads | — |
| Ads: conversions (leads posted) | Google Ads + GA4 | 10+ in 4 weeks |
| Ads: cost per qualified lead | Ads cost / qualified leads | <$150 |
| GC interviews completed | Interview log | 10 |
| Revenue per lead (avg) | Stripe + DB | $50-200 blended |
| Active contractors (per metro) | DB | 3+ per metro |
| Operator reply rate (lead-triggered outreach) | Outreach cron logs | >30% |

### 4.2 Where to Track

**Single dashboard:** Build a simple Google Sheet (`AeriusView Demand Gen Dashboard`) with 5 tabs:

1. **Overview** — weekly summary: total leads, leads by metro, match rate, revenue
2. **Buyer Outbound** — one row per contact, columns from §1.5 tracker
3. **Google Ads** — daily: spend, impressions, clicks, CTR, CPC, conversions, cost/lead
4. **GC Interviews** — one row per interview, data from §3.4
5. **Contractor Supply** — active operators per metro, lead-triggered outreach sent, reply rate

Pull lead data from the AeriusView DB via the existing admin endpoint (`GET /api/routing/waitlist` and lead-intake query). Jeff to manually input outbound + ads + interview data weekly.

**Future:** Build a live dashboard page in the admin portal once data volume justifies it (after Phase 4).

### 4.3 Weekly Cadence

| Day | Action | Who |
|---|---|---|
| **Monday 9am** | Pull DB lead counts, update Overview tab | Jeff (or delegate) |
| **Tuesday** | Send outbound Touch 1 batch (new contacts) | Jeff |
| **Wednesday** | Review ads performance (pause underperformers) | Jeff |
| **Thursday** | Send outbound follow-ups (Touches 2-5 due) | Jeff |
| **Friday 4pm** | Weekly review: reply rates, lead quality, metro-level adjustments | Jeff |
| **Friday 5pm** | Log GC interviews completed that week; update summary | Jeff |

---

## 5. SEO / Content Pivot

### 5.1 Use-Case Keyword Pages (Build First)

Build 5 use-case landing pages (also serve as SEO targets for the Google Ads test in §2.4):

| Priority | URL | Target Keyword | Title |
|---|---|---|---|
| 1 | `/use-cases/stockpile-volume-estimates` | "stockpile volume estimates" | Stockpile Volume Estimates — Drone Data for Aggregates & Earthwork |
| 2 | `/use-cases/construction-progress-monitoring` | "construction progress monitoring" | Construction Progress Drone Monitoring — Monthly Site Reports |
| 3 | `/use-cases/lidar-3d-scanning` | "drone LiDAR scanning" | Drone LiDAR Scanning — 3D Reality Capture for Construction |
| 4 | `/use-cases/topographic-data-collection` | "drone topographic data" | Topographic Data Collection — Drone Terrain Models |
| 5 | `/use-cases/as-built-documentation` | "drone as-built documentation" | As-Built Documentation — Drone 3D Data Collection (covered by construction progress monitoring canonical service) |

Each page:
- 1,500-2,000 words, structured: hero → what it is → why use drones → deliverable specs → who it's for → how to post a project → CTA
- Terminology-compliant (no "survey" — use "data collection", "estimates", "documentation" per strategy-v2)
- Disclaimer footer
- Internal links to relevant city pages (e.g., stockpile page links to Austin, Denver, Phoenix city pages)
- Schema: Service + FAQ schema

### 5.2 Content First (Blog / Resource)

After use-case pages, publish 3 blog posts (resume the 5 queued posts from ACTIVE-TASK, prioritize these):

| # | Title | Target Keyword | Why |
|---|---|---|---|
| 1 | "How GCs Use Drone Stockpile Volume Estimates for Earthwork Reconciliation" | stockpile volume drone | Links to stockpile use-case page; targets GC buyers |
| 2 | "Drone Progress Monitoring: Monthly Aerial Reports for Construction Projects" | construction progress drone | Links to progress monitoring use-case page |
| 3 | "LiDAR vs Photogrammetry for Construction Site Data Collection" | drone LiDAR vs photogrammetry | Links to LiDAR use-case page; targets engineering firms |

### 5.3 Leverage 626 City Pages

The 626 city pages are the biggest SEO asset. Pivot them to use-case funnels:

**Tactical changes:**
1. **Add use-case section to every city page** — below the existing operator-listing section, add 3 use-case blocks (Stockpile Volumes, Progress Monitoring, LiDAR Scanning) each linking to the corresponding `/use-cases/` page
2. **Add CTA per use-case** — "Need stockpile volume estimates in [City]? Post a project — free, 2 minutes."
3. **Cross-link city ↔ use-case** — Every city page links to all 5 use-case pages. Every use-case page links to the top 10 city pages (Austin, Denver, Phoenix, SLC, Seattle + 5 more by traffic).
4. **Add FAQ section per city page** — 3-5 questions targeting use-case keywords ("How much do drone stockpile volume estimates cost in [City]?", "Who does drone progress monitoring in [City]?")
5. **Internal linking from blog** — every blog post links to 2-3 relevant city pages

**Prioritize city page updates by traffic:** Jeff needs to log into Google Search Console (blocking item from ACTIVE-TASK) to identify which of the 626 pages get organic traffic. Update those first with use-case sections + CTAs.

**Don't expand city pages** (frozen per strategy-v2). Optimize existing 626, don't add more.

---

## Execution Timeline (Weeks 3-6)

| Week | Direct Outbound | Google Ads | GC Interviews | SEO/Content |
|---|---|---|---|---|
| **W3** | Build 200-contact prospect list (5 subagents, 1 per metro). ZeroBounce verify. | Build 3 use-case landing pages. Set up campaigns, conversion tracking, call tracking. Launch all 5 metros. | Recruit 4 interviews via AGC chapters (1-2 per metro). | Build use-case pages 1-2 (stockpile, progress monitoring). |
| **W4** | Send Touch 1 to first 100 contacts (20/metro). Monitor replies. | Monitor ads daily. Pause keywords with >$250 CPL after 7 days. | Conduct 4 interviews. Log data. | Build use-case pages 3-5. Publish blog post 1. |
| **W5** | Send Touch 1 to remaining 100. Send Touch 2-5 to W4 batch. | Optimize ad copy (A/B test 2 headlines per ad group). Increase budget on winning metros if CPL <$150. | Conduct 4 interviews. Mid-point summary. | Add use-case sections + CTAs to top 20 city pages by traffic (post-GSC data). Publish blog post 2. |
| **W6** | Full sequence running. Review reply rates per metro per source. Scale winners. | Final week. Full performance review. | Conduct final 2 interviews. Write `gc-interview-summary.md`. | Add use-case sections to next 30 city pages. Publish blog post 3. Cross-link all use-case ↔ city pages. |

**End of W6 deliverable:** Demand generation results report answering:
- Did 30+ qualified leads post across 5 metros?
- Which metros produced? Which didn't?
- What's the cost per qualified lead (ads + outbound)?
- What did GCs say in interviews (top 3 pains, top 3 trust factors)?
- Recommendation: scale, pivot, or kill each channel.

---

## Dependencies & Blockers

| Dependency | Owner | Blocks |
|---|---|---|
| Jeff logs into Google Search Console to export city-page traffic data | Jeff | City page SEO prioritization (§5.3) |
| Use-case landing pages built (frontend) | Dev | Google Ads launch (§2) |
| Lead-intake form supports budget/timeline/address fields (strategy-v2 §Buyer Intake) | Dev | Ad conversion tracking, outbound CTA |
| `outreach@aeriusview.com` subdomain set up (strategy-v2 Phase 1) | Dev | Outbound sends |
| ZeroBounce account active | Jeff | Email verification |

---

## What We're Not Doing (Frozen per strategy-v2)

- City page expansion (new cities) — optimize existing 626, don't add more
- Newsletter — not now
- Content resources Phases 3-5 — not now
- Software platform / escrow / business-in-a-box — not now
- Blog content beyond 3 demand-gen posts — 5 queued posts resume after validation
- Enterprise tier (vendor-of-record, QA guarantee, compliance monitoring) — Phase 4, after this validates

---

## Success Criteria (Week 8)

✅ **30+ qualified leads/month** posted across 5 metros
✅ **15%+ buyer reply rate** on outbound
✅ **<$150 cost per qualified lead** on Google Ads
✅ **10 GC interviews** completed with summary
✅ **3+ active contractors** per metro (supply side, from Phase 2 work)
✅ **>60% lead-to-match rate**

If we hit these, Phase 4 (Enterprise Layer) is justified. If we don't, we pivot before burning more capital.
# AeriusView Territory + Project Type Exclusivity — Execution Plan

**Created:** July 21, 2026
**Strategy reference:** strategy-v2.md §"Territory + Project Type Exclusivity"
**Status:** Draft — ready for implementation

---

## Overview

Replace the current territory rank system (first-come-first-served, non-exclusive, shared leads) with a **claim-based exclusivity system**: contractors claim a metro for specific project types, get exclusive leads in that lane, and keep the claim through performance (≥50% acceptance rate). Two contractors can coexist in the same metro if they serve different project types.

**Key difference from current system:** Today, `contractor_territory_rank` gives rank 1/2/3 with staggered sends — multiple contractors get the same lead. The new system routes each lead to ONE contractor (the claim holder for that metro + project type).

---

## 1. Database Schema

### 1.1 New table: `territory_claims`

```sql
CREATE TABLE IF NOT EXISTS territory_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
    metro_slug VARCHAR(100) NOT NULL,
    project_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | expired | revoked | released
    claimed_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,                  -- claimed_at + 6 months
    renewed_at TIMESTAMP,                          -- last renewal timestamp
    renewal_count INT DEFAULT 0,

    -- Performance tracking (rolling window, updated on each lead event)
    leads_offered INT DEFAULT 0,                   -- leads routed to this claim
    leads_accepted INT DEFAULT 0,                  -- leads accepted by this contractor
    leads_declined INT DEFAULT 0,                  -- leads explicitly declined
    leads_expired INT DEFAULT 0,                   -- leads that timed out (no response)
    acceptance_rate DECIMAL(5,2) DEFAULT 0,       -- leads_accepted / leads_offered * 100
    last_lead_at TIMESTAMP,                        -- most recent lead routed to this claim
    last_response_at TIMESTAMP,                    -- most recent accept/decline

    -- Admin override tracking
    revoked_reason VARCHAR(500),
    revoked_by VARCHAR(100),                        -- admin email
    revoked_at TIMESTAMP,

    -- Minimum lead volume guarantee
    min_leads_guaranteed INT DEFAULT 0,            -- set at claim time based on metro data
    credits_owed INT DEFAULT 0,                     -- auto-calculated if min not met

    UNIQUE(metro_slug, project_type, status)  -- only one ACTIVE claim per metro+project_type
);

CREATE INDEX IF NOT EXISTS idx_tc_contractor ON territory_claims(contractor_id, status);
CREATE INDEX IF NOT EXISTS idx_tc_metro_type ON territory_claims(metro_slug, project_type, status);
CREATE INDEX IF NOT EXISTS idx_tc_expiring ON territory_claims(expires_at) WHERE status = 'active';
```

The `UNIQUE(metro_slug, project_type, status)` constraint with `status='active'` ensures only one active claim per metro+project_type combination. A released/expired claim doesn't block a new claim.

### 1.2 New table: `project_type_catalog`

Standardized project types replacing the free-text `specialties` array on contractors.

```sql
CREATE TABLE IF NOT EXISTS project_type_catalog (
    code VARCHAR(50) PRIMARY KEY,                   -- 'roof_inspection', 'lidar_scanning', etc.
    display_name VARCHAR(100) NOT NULL,             -- 'Roof Inspection', 'LiDAR Scanning'
    tier VARCHAR(20) NOT NULL CHECK(tier IN ('standard','professional','premium')),
    price DECIMAL(10,2) NOT NULL,                    -- single price per lead
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Seed data** (from strategy-v2 pricing table):

| code | display_name | tier | price |
|---|---|---|---|
| roof_inspection | Roof Inspection | standard | 35 |
| real_estate_media | Real Estate Media | standard | 25 |
| aerial_imaging | Aerial Imaging | standard | 40 |
| construction_progress | Construction Progress Monitoring | professional | 150 |
| stockpile_volumetrics | Stockpile Volume Measurement | professional | 125 |
| topographic_data | Topographic Data Collection | professional | 100 |
| environmental_monitoring | Environmental Monitoring | professional | 75 |
| mining_data | Mining Data | professional | 150 |
| lidar_scanning | LiDAR Scanning | premium | 350 |
| multispectral_imaging | Multispectral Imaging | premium | 200 |
| 3d_reality_capture | 3D Reality Capture | premium | 500 |
| utility_inspection | Utility Infrastructure Inspection | premium | 400 |

### 1.3 New table: `claim_performance_log`

Append-only log for audit trail of claim state changes.

```sql
CREATE TABLE IF NOT EXISTS claim_performance_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES territory_claims(id) ON DELETE CASCADE,
    event_type VARCHAR(30) NOT NULL,               -- claim | renew | expire | revoke | release | lead_routed | lead_accepted | lead_declined | lead_expired
    lead_id UUID REFERENCES leads(id),
    detail JSONB,                                   -- event-specific payload
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cpl_claim ON claim_performance_log(claim_id, created_at DESC);
```

### 1.4 Schema changes to existing tables

**`leads` table** — add `project_type_code` (canonical) alongside existing `service_type` (free-text, kept for backward compat):

```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS project_type_code VARCHAR(50);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS metro_slug VARCHAR(100);
```

**`contractors` table** — add `project_types TEXT[] DEFAULT '{}'` (canonical codes from catalog) alongside existing `specialties TEXT[]` (free-text, deprecated but kept):

```sql
ALTER TABLE contractors ADD COLUMN IF NOT EXISTS project_types TEXT[] DEFAULT '{}';
```

### 1.5 Existing tables retained (no changes needed)

- `contractors` — all existing columns preserved
- `leads` — existing columns preserved, two new columns added (above)
- `lead_routes` — existing structure works; routing logic changes but table schema is fine
- `city_metro_mapping` — already has `metro_slug`, used for metro matching
- `credit_transactions` — unchanged

### 1.6 Existing table deprecated

- `contractor_territory_rank` — superseded by `territory_claims`. Keep for migration (see §7) then deprecate. Do NOT delete — the rank system remains as a fallback during transition.

---

## 2. Claim Lifecycle

### 2.1 Claim

**Preconditions:**
- Contractor status is `active` (approved)
- Contractor has the project type in their `project_types` array
- No other contractor holds an `active` claim for the same `metro_slug + project_type`
- Contractor has reviewed demand data for the metro (API returns lead counts before claim)

**Process:**
1. Contractor requests claim via `POST /api/portal/claims` with `metro_slug` + `project_type`
2. API checks availability (no active claim exists)
3. API shows demand data: "X leads in this metro for this project type in the last 90 days"
4. Contractor confirms claim
5. Row inserted: `status='active'`, `claimed_at=NOW()`, `expires_at=NOW() + 6 months`
6. `min_leads_guaranteed` calculated from historical lead volume (if >0 leads in 90 days, guarantee = 25% of that volume)
7. Log entry: `claim_performance_log` event `claim`

**Validation rules:**
- A contractor can hold max **5 active claims** (prevents squatting)
- A contractor cannot claim the same metro+project_type they already hold
- Project type must exist in `project_type_catalog` and be active

### 2.2 Renewal

**Automatic renewal** runs daily via cron. For each `active` claim where `expires_at <= NOW() + 7 days`:

1. Check acceptance rate over the claim period:
   - `acceptance_rate >= 50%` AND `leads_offered >= 3` → **auto-renew**
   - `acceptance_rate >= 50%` AND `leads_offered < 3` → **auto-renew** (not enough data to penalize)
   - `acceptance_rate < 50%` AND `leads_offered >= 5` → **do not renew** (expire at end of period)
   - `acceptance_rate < 50%` AND `leads_offered < 5` → **auto-renew** (not enough data)

2. On renewal:
   - `expires_at = NOW() + 6 months`
   - `renewed_at = NOW()`
   - `renewal_count += 1`
   - Reset performance counters: `leads_offered = 0`, `leads_accepted = 0`, `leads_declined = 0`, `leads_expired = 0`, `acceptance_rate = 0`
   - Log entry: event `renew`

3. On non-renewal:
   - `status = 'expired'`
   - Log entry: event `expire`
   - Contractor notified via email

### 2.3 Revocation (admin override)

Admin can revoke a claim at any time via `POST /api/admin/claims/{claim_id}/revoke`:

1. Set `status = 'revoked'`, `revoked_reason`, `revoked_by`, `revoked_at = NOW()`
2. Log entry: event `revoke`
3. Contractor notified via email
4. Metro+project_type immediately available for new claims

**Revocation reasons:** contractor inactive 30+ days, quality complaints, manual override by Jeff.

### 2.4 Release (contractor-initiated)

Contractor can release a claim voluntarily via `DELETE /api/portal/claims/{claim_id}`:

1. Set `status = 'released'`
2. Log entry: event `release`
3. Metro+project_type immediately available

### 2.5 Minimum Lead Volume Guarantee

If `min_leads_guaranteed > 0` and actual `leads_offered < min_leads_guaranteed` at claim expiry:
1. Calculate `credits_owed = min_leads_guaranteed - leads_offered`
2. Issue automatic credit to contractor's `credit_balance`
3. Create `credit_transactions` entry with `reason = 'territory_min_lead_credit'`
4. Log entry: event with `detail = {credits_owed, min_leads_guaranteed, leads_offered}`

### 2.6 Thresholds Summary

| Metric | Threshold | Action |
|---|---|---|
| Acceptance rate (for renewal) | ≥ 50% | Auto-renew |
| Acceptance rate (for renewal) | < 50% with ≥ 5 leads offered | Expire |
| Min leads offered (for fair evaluation) | < 5 | Auto-renew regardless of rate |
| Contractor inactivity | 30 days no lead response | Admin can revoke |
| Max active claims per contractor | 5 | Block new claims |
| Claim duration | 6 months | Renewable |

---

## 3. Lead Routing Logic

### 3.1 New routing function: `route_lead_to_claimed_contractor`

Replaces the current `route_lead_to_contractors()` in `routing.py`. The new function routes exclusively — one lead, one contractor.

**Flow:**

```
1. Lead arrives with zip_code + project_type_code (mapped from service_type)
2. Resolve metro_slug from zip_code via city_metro_mapping
3. Look up active territory_claim for metro_slug + project_type_code
4. If claim found:
   a. Verify contractor is active and has credit_balance >= credit_cost
   b. Create single lead_route (status=queued, send_at=NOW)
   c. Increment claim.leads_offered
   d. Log claim_performance_log event 'lead_routed'
   e. Process queue immediately (send notification)
   f. Return 1 contractor routed
5. If no claim found:
   a. FALLBACK to legacy rank-based routing (existing route_lead_to_contractors)
   b. This covers metros/project types with no claims yet
   c. Log that fallback was used
```

### 3.2 SQL for claim lookup

```sql
SELECT tc.id as claim_id, tc.contractor_id, c.name, c.email, c.credit_balance
FROM territory_claims tc
JOIN contractors c ON tc.contractor_id = c.id
WHERE tc.metro_slug = %s
  AND tc.project_type = %s
  AND tc.status = 'active'
  AND c.status = 'active'
  AND c.credit_balance >= %s
```

### 3.3 Accept/decline handling updates

**On accept** (`/api/lead-accept/{token}`):
1. Existing acceptance logic runs (credit charge, lead status update, etc.)
2. NEW: Update the territory_claim:
   ```sql
   UPDATE territory_claims
   SET leads_accepted = leads_accepted + 1,
       last_response_at = NOW(),
       acceptance_rate = (leads_accepted::DECIMAL / NULLIF(leads_offered, 0)) * 100
   WHERE id = %s
   ```
3. Log `claim_performance_log` event `lead_accepted`

**On decline** (`/api/lead-decline/{token}`):
1. Existing decline logic runs
2. NEW: Update territory_claim:
   ```sql
   UPDATE territory_claims
   SET leads_declined = leads_declined + 1,
       last_response_at = NOW(),
       acceptance_rate = (leads_accepted::DECIMAL / NULLIF(leads_offered, 0)) * 100
   WHERE id = %s
   ```
3. Log `claim_performance_log` event `lead_declined`

**On lead expiry** (cron processes expired routes):
1. Existing expiry logic
2. NEW: Update territory_claim:
   ```sql
   UPDATE territory_claims
   SET leads_expired = leads_expired + 1,
       acceptance_rate = (leads_accepted::DECIMAL / NULLIF(leads_offered, 0)) * 100
   WHERE id = %s
   ```
3. Log `claim_performance_log` event `lead_expired`

### 3.4 Project type mapping

When a lead comes in with `service_type` (free text from buyer intake), map to `project_type_code`:

```python
PROJECT_TYPE_MAP = {
    "roof inspection": "roof_inspection",
    "real estate": "real_estate_media",
    "orthomosaic": "aerial_imaging",
    "construction progress": "construction_progress",
    "stockpile": "stockpile_volumetrics",
    "volumetrics": "stockpile_volumetrics",
    "topographic": "topographic_data",
    "environmental monitoring": "environmental_monitoring",
    "environmental": "environmental_monitoring",
    "mining": "mining_data",
    "mining data": "mining_data",
    "multispectral": "multispectral_imaging",
    "multispectral imaging": "multispectral_imaging",
    "lidar": "lidar_scanning",
    "3d scan": "3d_reality_capture",
    "reality capture": "3d_reality_capture",
    "utility inspection": "utility_inspection",
    "infrastructure": "utility_inspection",
}
```

Store both `service_type` (original) and `project_type_code` (canonical) on the lead. Also store `metro_slug` resolved from zip_code.

### 3.5 Fallback chain

```
1. Claim-based exclusive routing (metro + project_type)
2. Legacy rank-based routing (zip + specialty + rank, staggered sends)
3. Unmatched → waitlist (existing behavior)
```

This ensures no regression — metros without claims still get the old multi-contractor routing.

---

## 4. API Endpoints

### 4.1 Contractor Portal Endpoints (require Bearer token auth)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/portal/claims` | List contractor's territory claims (active + history) |
| `POST` | `/api/portal/claims` | Create a new territory claim |
| `DELETE` | `/api/portal/claims/{claim_id}` | Release a claim (voluntary) |
| `GET` | `/api/portal/claims/availability` | Check what metros+types are available to claim |
| `GET` | `/api/portal/claims/{claim_id}/performance` | View performance metrics for a claim |

**POST /api/portal/claims** request body:
```json
{
  "metro_slug": "austin-tx",
  "project_type": "lidar_scanning"
}
```

Response (201):
```json
{
  "claim_id": "uuid",
  "metro_slug": "austin-tx",
  "project_type": "lidar_scanning",
  "status": "active",
  "claimed_at": "2026-07-21T...",
  "expires_at": "2027-01-21T...",
  "min_leads_guaranteed": 5,
  "demand_data": {
    "leads_90_days": 22,
    "avg_lead_price": 350
  }
}
```

**GET /api/portal/claims/availability** query params: `metro_slug` (optional), `project_type` (optional)

Response:
```json
{
  "available": [
    {"metro_slug": "austin-tx", "metro_name": "Austin, TX", "project_type": "lidar_scanning", "leads_90_days": 22},
    {"metro_slug": "austin-tx", "metro_name": "Austin, TX", "project_type": "construction_progress", "leads_90_days": 15}
  ],
  "claimed_by_you": [
    {"metro_slug": "dallas-tx", "project_type": "roof_inspection", "expires_at": "..."}
  ],
  "claimed_by_others": [
    {"metro_slug": "austin-tx", "project_type": "roof_inspection", "contractor_name": "Acme Drone"}
  ]
}
```

### 4.2 Admin Endpoints (require ADMIN_API_KEY)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/admin/claims` | List all territory claims with filters (metro, type, status) |
| `GET` | `/api/admin/claims/{claim_id}` | View single claim detail with performance log |
| `POST` | `/api/admin/claims/{claim_id}/revoke` | Revoke a claim |
| `POST` | `/api/admin/claims/{claim_id}/extend` | Extend a claim (override expiry) |
| `GET` | `/api/admin/claims/overview` | Dashboard summary: claims by metro, by type, expiring soon |

**GET /api/admin/claims** query params: `metro_slug`, `project_type`, `status`, `contractor_id`, `expiring_within_days`

**POST /api/admin/claims/{claim_id}/revoke** body:
```json
{
  "reason": "Contractor inactive 45 days"
}
```

### 4.3 Cron Endpoints (require ADMIN_API_KEY)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/claims/renewal-check` | Process claim renewals (run daily) |
| `POST` | `/api/claims/min-lead-credit` | Issue credits for unmet minimum guarantees (run on claim expiry) |

---

## 5. Contractor Portal UI

### 5.1 New Portal Page: `/portal/territory`

**Sections:**

1. **My Claims** (top)
   - Card per active claim: metro name, project type, acceptance rate gauge, leads offered/accepted, expiry date with countdown
   - "Release Claim" button (with confirmation modal)
   - "View Performance" link → detail view

2. **Claim a Territory** (middle)
   - Metro selector dropdown (from `city_metro_mapping`, grouped by state)
   - Project type selector (from `project_type_catalog`, grouped by tier)
   - "Check Availability" button → shows demand data + whether it's available
   - "Claim This Territory" button → creates claim

3. **Available Territories** (bottom)
   - Table: metro, project type, leads in last 90 days, status (available / claimed by someone)
   - Filter by state, by project type tier
   - Sort by lead volume

### 5.2 Dashboard Integration

Add a "Territory Claims" summary card to the existing `/portal/dashboard` response:
```json
{
  "territory_claims": [
    {
      "claim_id": "uuid",
      "metro_name": "Austin, TX",
      "project_type": "LiDAR Scanning",
      "status": "active",
      "acceptance_rate": 72.5,
      "leads_offered": 12,
      "leads_accepted": 9,
      "expires_at": "2027-01-21T...",
      "days_until_expiry": 183
    }
  ]
}
```

### 5.3 Astro Frontend Files

```
src/pages/portal/territory.astro        — main territory management page
src/components/portal/ClaimCard.astro    — individual claim card with performance gauge
src/components/portal/ClaimForm.astro     — metro + project type selector + demand preview
src/components/portal/AvailabilityTable.astro — browsable available territories
```

---

## 6. Admin Dashboard

### 6.1 New Admin Page: `/admin/territory`

**Sections:**

1. **Overview tiles:**
   - Total active claims
   - Claims expiring in 30 days
   - Claims below 50% acceptance rate
   - Claims with no leads offered (squatting detection)

2. **Claims table** (sortable, filterable):
   - Columns: Contractor, Metro, Project Type, Status, Acceptance Rate, Leads Offered, Leads Accepted, Expires, Renewal Count
   - Row actions: View Detail, Revoke, Extend

3. **Claim Detail view:**
   - Full performance log (timeline of all events)
   - Lead history for this claim
   - Admin action buttons

4. **Metro coverage map:**
   - Table: metro → which project types have active claims, which are open
   - Identifies underserved metros (high lead volume, no claims)

### 6.2 Admin frontend files

```
src/pages/admin/territory.astro          — admin territory dashboard
src/components/admin/ClaimsTable.astro    — sortable claims table
src/components/admin/ClaimDetail.astro    — claim detail with performance log
```

---

## 7. Migration

### 7.1 Existing contractor migration

For each active contractor with `service_area_metros` and `specialties`:

1. **Map specialties → project_types:**
   ```python
   for contractor in active_contractors:
       mapped_types = [PROJECT_TYPE_MAP.get(s.lower(), s) for s in contractor.specialties]
       UPDATE contractors SET project_types = mapped_types WHERE id = contractor.id
   ```

2. **Create claims from existing territory ranks:**
   For each row in `contractor_territory_rank` where `rank = 1` (first-ranked contractor in a city):
   - Resolve `metro_slug` from `city_slug` via `city_metro_mapping`
   - For each project_type in the contractor's `project_types`:
     - Create `territory_claims` row: `status='active'`, `expires_at=NOW() + 6 months`
     - Skip if a claim already exists for that metro+project_type
   - This gives rank-1 contractors a 6-month head start on their existing territory

3. **Backfill lead data:**
   For existing leads, map `service_type` → `project_type_code` and resolve `metro_slug` from `zip_code`. This populates historical data for demand preview and min-lead calculations.

### 7.2 Migration script

`scripts/run_migration_territory_claims.py`:
```python
# 1. Create project_type_catalog and seed rows
# 2. Add project_types column to contractors (ALTER TABLE — already idempotent)
# 3. Add project_type_code + metro_slug columns to leads (ALTER TABLE — already idempotent)
# 4. Create territory_claims table
# 5. Create claim_performance_log table
# 6. Map contractor specialties → project_types
# 7. Create claims for rank-1 contractors
# 8. Backfill lead project_type_code + metro_slug
# 9. Print migration summary report
```

### 7.3 Rollback plan

- `territory_claims` and `claim_performance_log` are new tables — drop them
- `project_types` column on contractors — leave (harmless if unused)
- `project_type_code` / `metro_slug` on leads — leave (harmless if unused)
- Routing logic reverts to legacy `route_lead_to_contractors` (the function stays unchanged, just the dispatcher changes)

---

## 8. File List (by priority)

### Priority 1 — Core Backend (must ship together)

| File | Action | Description |
|---|---|---|
| `app/database.py` | Modify | Add `territory_claims`, `claim_performance_log`, `project_type_catalog` table creation to `init_db()`. Add column migrations for `leads.project_type_code`, `leads.metro_slug`, `contractors.project_types`. Seed project type catalog. |
| `app/lead_service.py` | Modify | Add claim performance update calls in `apply_lead_acceptance()` and decline handler. |
| `app/routers/routing.py` | Modify | Add `route_lead_to_claimed_contractor()` function. Update lead intake to resolve `metro_slug` + `project_type_code`. Add fallback to legacy routing. Add project type mapping dict. |
| `app/routers/portal.py` | Modify | Add claim endpoints: `GET/POST /portal/claims`, `DELETE /portal/claims/{id}`, `GET /portal/claims/availability`, `GET /portal/claims/{id}/performance`. Add territory_claims summary to dashboard. |
| `app/routers/admin.py` | Modify | Add admin claim endpoints: list, detail, revoke, extend, overview. |
| `scripts/run_migration_territory_claims.py` | Create | Migration script (§7.2). |

### Priority 2 — Cron + Automation

| File | Action | Description |
|---|---|---|
| `app/routers/portal.py` | Modify | Add `/api/claims/renewal-check` and `/api/claims/min-lead-credit` cron endpoints. |

### Priority 3 — Frontend

| File | Action | Description |
|---|---|---|
| `src/pages/portal/territory.astro` | Create | Contractor territory management page. |
| `src/components/portal/ClaimCard.astro` | Create | Claim card with acceptance rate gauge. |
| `src/components/portal/ClaimForm.astro` | Create | Metro + project type selector. |
| `src/components/portal/AvailabilityTable.astro` | Create | Browsable available territories table. |
| `src/pages/admin/territory.astro` | Create | Admin territory dashboard. |
| `src/components/admin/ClaimsTable.astro` | Create | Admin sortable claims table. |
| `src/components/admin/ClaimDetail.astro` | Create | Admin claim detail with performance log. |

### Priority 4 — Tests

| File | Action | Description |
|---|---|---|
| `tests/test_claim_lifecycle.py` | Create | Claim creation, renewal, revocation, release. |
| `tests/test_exclusive_routing.py` | Create | Lead routes to claim holder, not to multiple contractors. |
| `tests/test_claim_performance.py` | Create | Acceptance rate tracking, renewal thresholds. |
| `tests/test_claim_migration.py` | Create | Verify migration script creates correct claims from existing data. |
| `tests/test_min_lead_credit.py` | Create | Minimum lead volume guarantee credit issuance. |

---

## 9. Implementation Sequence

```
Week 1: Schema + migration + routing logic
  ├── database.py changes (tables + columns + seed)
  ├── migration script
  ├── routing.py: route_lead_to_claimed_contractor + project type mapping
  └── lead_service.py: claim performance updates on accept/decline

Week 2: API endpoints + cron
  ├── portal.py: claim CRUD + availability + performance
  ├── admin.py: claim management + overview
  └── cron endpoints: renewal-check + min-lead-credit

Week 3: Frontend
  ├── portal/territory.astro + components
  ├── admin/territory.astro + components
  └── dashboard integration (claims summary card)

Week 4: Tests + deploy
  ├── test suite
  ├── migration on staging → verify
  ├── deploy to production
  └── monitor first 48h
```

---

## 10. Edge Cases & Decisions

| Edge case | Decision |
|---|---|
| Contractor claims metro but has 0 credits when lead arrives | Lead falls through to legacy routing (rank-based). Claim stays active. |
| Two contractors claim same metro+type simultaneously | DB unique constraint blocks the second. First wins. |
| Contractor releases claim, then re-claims same metro+type | Allowed — released claims don't block. New 6-month period starts. |
| Lead comes in with unknown service_type (not in mapping) | `project_type_code` = NULL. Falls through to legacy routing. |
| Metro has no city_metro_mapping entry | Claim can't be created (metro_slug required). Add to mapping first. |
| Contractor changes their project_types after claiming | Claim stays valid for the original project_type. Changing project_types doesn't auto-create or remove claims. |
| Claim expires mid-lead-route (lead is queued but claim expires) | Lead route already created — completes normally. New leads won't route to expired claim. |
| Admin revokes claim while lead is in-flight | Same as above — existing routes complete, new leads don't route. |

---

## Appendix: Project Type Mapping (full)

```python
PROJECT_TYPE_MAP = {
    # Standard tier
    "roof inspection": "roof_inspection",
    "roof": "roof_inspection",
    "real estate photography": "real_estate_media",
    "real estate video": "real_estate_media",
    "real estate photo/video": "real_estate_media",
    "property photography": "real_estate_media",
    "orthomosaic": "aerial_imaging",
    "aerial photography": "aerial_imaging",
    # Professional tier
    "construction progress monitoring": "construction_progress",
    "construction progress": "construction_progress",
    "progress documentation": "construction_progress",
    "stockpile volumetrics": "stockpile_volumetrics",
    "stockpile": "stockpile_volumetrics",
    "volumetrics": "stockpile_volumetrics",
    "topographic data collection": "topographic_data",
    "topographic": "topographic_data",
    "topographic survey": "topographic_data",
    "environmental monitoring": "environmental_monitoring",
    "environmental": "environmental_monitoring",
    "mining": "mining_data",
    "mining data": "mining_data",
    # Premium tier
    "lidar scanning": "lidar_scanning",
    "lidar": "lidar_scanning",
    "multispectral": "multispectral_imaging",
    "multispectral imaging": "multispectral_imaging",
    "3d reality capture": "3d_reality_capture",
    "3d scan": "3d_reality_capture",
    "reality capture": "3d_reality_capture",
    "utility inspection": "utility_inspection",
    "infrastructure inspection": "utility_inspection",
    "infrastructure": "utility_inspection",
}
```
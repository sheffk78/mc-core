# Execution Plan: Lead Qualification Pipeline

**Created:** July 21, 2026
**Strategy ref:** strategy-v2.md §"Lead Qualification"

---

## Current System

From `routing.py`:
- Lead comes in with `zip_code + service_type` via `POST /api/lead-intake`
- `route_lead_to_contractors()` finds matching contractors by zip + specialty + credits + active status
- Routes created with staggered send_at timestamps (rank 1 immediate, rank 2 +15min, etc.)
- Multiple contractors get the same lead (non-exclusive)
- No qualification beyond basic field collection
- No spam detection, no budget range, no airspace pre-check

From `database.py` leads table:
- `name, email, phone, zip_code, service_type, project_description, source_page, status`

---

## New System

Every lead is pre-qualified before going to a contractor. Qualified = verified intent, budget range, timeline, site address, airspace pre-check, project type classified to pricing tier. Bad leads credited back automatically.

---

## 1. Intake Form Redesign

### Current fields (keep):
- name, email, phone, zip_code, service_type, project_description

### New fields to add to leads table:

```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS site_address TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS budget_range VARCHAR;
-- 'under-500' | '500-2500' | '2500-10000' | '10000-plus' | 'unsure'
ALTER TABLE leads ADD COLUMN IF NOT EXISTS timeline VARCHAR;
-- 'urgent' | '1-2-weeks' | '1-month' | 'flexible'
ALTER TABLE leads ADD COLUMN IF NOT EXISTS deliverable_format VARCHAR;
-- 'ortho-geotiff' | '3d-model' | 'progress-report' | 'volumetrics' | 'inspection-report' | 'raw-imagery' | 'not-sure'
ALTER TABLE leads ADD COLUMN IF NOT EXISTS pricing_tier VARCHAR;
-- 'standard' | 'professional' | 'premium' — set by classification logic
ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_price DECIMAL(10,2);
-- actual price, from pricing tier + service type
ALTER TABLE leads ADD COLUMN IF NOT EXISTS qualification_score INT DEFAULT 0;
-- 0-100, calculated from completeness + spam checks
ALTER TABLE leads ADD COLUMN IF NOT EXISTS qualification_status VARCHAR DEFAULT 'pending';
-- 'pending' | 'qualified' | 'rejected' | 'needs-review'
ALTER TABLE leads ADD COLUMN IF NOT EXISTS airspace_check JSONB;
-- {controlled: bool, laanc_required: bool, class: 'B/C/D/E', notes: text}
ALTER TABLE leads ADD COLUMN IF NOT EXISTS spam_flags TEXT[] DEFAULT '{}';
-- ['foreign-domain', 'phone-mismatch', 'duplicate', 'no-budget']
```

### Intake form structure (on CityPage.astro + city pages):

The form guides buyers through a structured flow instead of free-text:

**Step 1: What do you need?**
- Dropdown: service type (maps to our 12 service types)
- Site address (autocomplete via Google Places API or manual entry)

**Step 2: Project details**
- Budget range (dropdown, not free text)
- Timeline (dropdown)
- Deliverable format (dropdown with plain-language descriptions)
- Project description (free text, optional)

**Step 3: Contact info**
- Name, email, phone

On submit, the lead goes to qualification (not directly to routing).

---

## 2. Qualification Logic

New file: `app/qualification.py`

```python
def qualify_lead(lead_data, db) -> dict:
    """Run qualification checks on a new lead.
    Returns: {score, status, spam_flags, pricing_tier, lead_price, airspace_check}
    """
    score = 0
    spam_flags = []
    
    # 1. Email domain country check
    email_domain = lead_data['email'].split('@')[-1]
    if is_foreign_domain(email_domain, lead_data['zip_code']):
        spam_flags.append('foreign-domain')
        score -= 30
    
    # 2. Phone format validation
    if not is_valid_us_phone(lead_data['phone'], lead_data['zip_code']):
        spam_flags.append('phone-mismatch')
        score -= 20
    
    # 3. Budget collected (not just "unsure")
    if lead_data.get('budget_range') and lead_data['budget_range'] != 'unsure':
        score += 20
    
    # 4. Site address provided
    if lead_data.get('site_address'):
        score += 15
    
    # 5. Timeline provided
    if lead_data.get('timeline'):
        score += 10
    
    # 6. Deliverable format specified
    if lead_data.get('deliverable_format') and lead_data['deliverable_format'] != 'not-sure':
        score += 15
    
    # 7. Duplicate check (same email + zip in last 30 days)
    if is_duplicate_lead(lead_data['email'], lead_data['zip_code'], db):
        spam_flags.append('duplicate')
        score -= 50
    
    # 8. Pricing tier classification
    tier = get_lead_tier(lead_data['service_type'])
    price = get_lead_price(lead_data['service_type'])
    
    # 9. Airspace pre-check
    airspace = check_airspace(lead_data.get('site_address', ''), lead_data['zip_code'])
    
    # 10. Determine status
    if score >= 50:
        status = 'qualified'
    elif score >= 20:
        status = 'needs-review'  # manual check by admin
    else:
        status = 'rejected'
    
    return {
        'score': score,
        'status': status,
        'spam_flags': spam_flags,
        'pricing_tier': tier,
        'lead_price': price,
        ' airspace_check': airspace,
    }
```

### Qualification thresholds:
- Score >= 50: auto-qualified, route to contractor immediately
- Score 20-49: needs manual review (Kit or admin checks)
- Score < 20: rejected (spam, duplicate, or junk)

---

## 3. Airspace/LAANC Pre-Check

This is a drone-specific qualification step no competitor does. Adds real value.

### Implementation options (in order of preference):

**Option A: FAA UAS Facility Maps API**
- FAA publishes UAS Facility Maps showing airspace classes and LAANC availability
- Query by coordinates (from site address geocoding)
- Returns: airspace class, controlled/uncontrolled, LAANC grid, max altitude
- Free, public data

**Option B: AirMap API (if still available)**
- Commercial airspace API
- Returns: airspace class, advisories, LAANC availability
- May have free tier

**Option C: Manual lookup**
- Geocode site address -> lat/lon
- Check against FAA UAS Facility Map data (downloaded CSV or JSON)
- Store result in leads.airspace_check JSONB

### What the check returns:
```json
{
    "controlled": true,
    "airspace_class": "D",
    "laanc_available": true,
    "max_altitude_ft": 400,
    "notes": "Within 5nm of controlled airport. LAANC authorization required."
}
```

This info gets included in the lead notification to the contractor, so they know immediately if LAANC is needed before accepting.

---

## 4. Lead-to-Contractor Matching (Updated Routing)

### Current: staggered routing to multiple contractors by rank
### New: exclusive routing to ONE contractor (territory + project type holder)

Update `route_lead_to_contractors()` in `routing.py`:

```python
def route_lead_to_contractors(lead_id, zip_code, service_type, pricing_tier, db) -> int:
    """Route a qualified lead to ONE contractor (exclusive).
    Matches by: territory claim for metro + project type.
    Returns: number of contractors routed to (0 or 1).
    """
    # 1. Get city_slug from zip_code
    # 2. Find active territory_claim for this city + service_type
    # 3. If claim holder exists and is active: route exclusively to them
    # 4. If no claim holder: trigger lead-triggered outreach
    # 5. Create ONE lead_route record (not multiple staggered)
```

---

## 5. Bad Lead Credit System

### What qualifies for automatic credit:
- `no-response` — No response from buyer after 7 days
- `wrong-service-type` — Wrong service type (contractor reports mismatch after contacting)
- `spam` — Lead marked as spam (foreign domain, duplicate, fake phone)
- `out-of-area` — Out of area (buyer site address outside contractor's service zone)
- `budget-mismatch` — Budget mismatch (buyer budget doesn't match service cost range)

### Automation:
- `POST /portal/leads/{lead_id}/credit` endpoint
- Contractor selects reason from dropdown
- If reason is in auto-approve list: credit applied immediately, no admin review
- If reason is "other": goes to admin review
- Credit updates `lead_charges.status = 'credited'`
- If already charged: Stripe refund issued
- Track credit rate per contractor (if >30%, flag for review)

---

## 6. Lead-Triggered Outreach (Unmatched Leads)

When a qualified lead has no territory claim holder:

1. Lead goes to `unmatched_lead_waitlist` table (already exists)
2. Existing cron job researches nearby operators (already running)
3. NEW: Generate redacted lead preview for outreach:
   - "J*** S., XXX-XXX-1234, 78701, construction progress monitoring, $2,500-5,000 budget, needs within 2 weeks"
4. Send to top 3 nearby operators via email
5. First to accept gets the lead (and a 6-month territory claim for that metro + project type)
6. First lead free for new contractors (no charge on first accepted lead)

---

## 7. Database Schema Changes (Summary)

### New columns on `leads`:
- `site_address TEXT`
- `budget_range VARCHAR`
- `timeline VARCHAR`
- `deliverable_format VARCHAR`
- `pricing_tier VARCHAR`
- `lead_price DECIMAL(10,2)`
- `qualification_score INT DEFAULT 0`
- `qualification_status VARCHAR DEFAULT 'pending'`
- `airspace_check JSONB`
- `spam_flags TEXT[] DEFAULT '{}'`

### New table: None (reuse existing `lead_routes`, `unmatched_lead_waitlist`)

### Updated: `lead_routes` — add `is_exclusive BOOLEAN DEFAULT false`
```sql
ALTER TABLE lead_routes ADD COLUMN IF NOT EXISTS is_exclusive BOOLEAN DEFAULT false;
```

---

## 8. API Endpoint Changes

### Updated: `POST /api/lead-intake` (in leads router)
- Accept new fields: site_address, budget_range, timeline, deliverable_format
- After saving, call `qualify_lead()` instead of `route_lead_to_contractors()` directly
- If qualified: route immediately
- If needs-review: hold for manual review
- If rejected: return "We're expanding in your area" message to buyer

### New: `POST /api/admin/leads/{id}/review`
- Admin reviews a needs-review lead
- Approve (route to contractor) or reject (notify buyer)

### Updated: `POST /api/portal/leads/{id}/accept`
- On acceptance, create `lead_charges` record (from pricing plan)
- Lead price determined by `leads.lead_price` (set at qualification)

### New: `POST /api/portal/leads/{id}/credit`
- Request bad lead credit with reason
- Auto-approve valid reasons, manual review for "other"

### Updated: `GET /api/portal/leads`
- Show qualification status, pricing tier, lead price, airspace check for each lead

---

## 9. File List (Priority Order)

### P0 — Qualification pipeline
1. New file: `app/qualification.py` — qualification logic, spam detection, airspace check
2. `app/database.py` — add new lead columns
3. `app/routers/leads.py` (or wherever lead-intake lives) — update intake to call qualification
4. `app/routers/routing.py` — update routing for exclusive single-contractor routing
5. `app/pricing.py` — already updated in pricing transition plan

### P1 — Airspace integration
6. New file: `app/airspace.py` — FAA UAS Facility Maps lookup or AirMap integration
7. Geocoding: use existing Google API or add simple lat/lon from zip code

### P2 — Bad lead credit system
8. `app/routers/portal.py` — add credit endpoint
9. `app/routers/stripe.py` — refund logic for credited leads

### P3 — Lead-triggered outreach enhancement
10. Update existing unmatched lead cron to generate redacted previews
11. Update outreach email template to include lead preview

### P4 — UI updates
12. `src/components/CityPage.astro` — redesign intake form with structured fields
13. `src/pages/dashboard/index.astro` — show qualification info on leads
14. Admin dashboard — review queue for needs-review leads
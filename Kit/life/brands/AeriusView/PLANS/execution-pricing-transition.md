# Execution Plan: Pricing Transition — Credits to Tiered Per-Lead

**Created:** July 21, 2026
**Strategy ref:** strategy-v2.md §"Pricing: Per-Lead, Tiered, Exclusive"

---

## Current System

- `pricing.py`: Flat 1 credit = 1 lead. Credit packages: starter ($150/5), standard ($275/10), bulk ($500/20).
- `stripe.py`: Stripe Checkout for credit package purchases. Webhook adds credits to `contractors.credit_balance`.
- `routing.py`: `route_lead_to_contractors()` checks `credit_balance >= CREDITS_PER_LEAD` before routing.
- `portal.py`: Portal shows credit balance, purchase packages.
- `contractors.py`: `contractors.credit_balance` (INT), `credit_transactions` table for audit.
- `database.py`: `contractors` table has `credit_balance INT DEFAULT 0`. `credit_transactions` table exists.

## New System

Tiered per-lead pricing. No credits. Contractor pays per qualified lead delivered.

| Tier | Service Types | Lead Price |
|---|---|---|
| Standard | roof-inspection, real-estate, aerial-imagery | $25-50 |
| Professional | construction, volumetric, topographic, mining, environmental | $75-200 |
| Premium | lidar, multispectral, utility/infrastructure inspection | $200-500 |

Billing model: contractor pays AFTER accepting a lead (not before). Stripe charge or invoice after acceptance. Bad leads get credited back automatically.

---

## 1. Database Schema Changes

### 1.1 New columns on `contractors`

```sql
ALTER TABLE contractors ADD COLUMN IF NOT EXISTS billing_method VARCHAR DEFAULT 'invoice';
-- 'invoice' = pay after acceptance, 'card_on_file' = auto-charge
ALTER TABLE contractors ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR;
ALTER TABLE contractors ADD COLUMN IF NOT EXISTS stripe_payment_method_id VARCHAR;
ALTER TABLE contractors ADD COLUMN IF NOT EXISTS outstanding_balance DECIMAL(10,2) DEFAULT 0;
-- unpaid lead charges accumulate, invoiced monthly or on threshold
```

### 1.2 New table: `lead_charges`

```sql
CREATE TABLE IF NOT EXISTS lead_charges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    contractor_id UUID REFERENCES contractors(id),
    amount DECIMAL(10,2) NOT NULL,
    tier VARCHAR(20) NOT NULL,  -- 'standard' | 'professional' | 'premium'
    service_type VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',  -- pending | paid | credited | disputed
    charged_at TIMESTAMP,
    credited_at TIMESTAMP,
    credit_reason VARCHAR,
    comp_reason VARCHAR,  -- NULL = normal charge, 'first-lead' = free first lead, 'promo' = promotional, 'goodwill' = manual
    stripe_invoice_id VARCHAR,
    stripe_charge_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.3 Deprecate (don't delete yet)

- `contractors.credit_balance` — keep column, stop using it. Migrate existing balances to account credit.
- `credit_transactions` — keep for historical audit. Stop writing new rows.
- `CREDIT_PACKAGES` in pricing.py — stop offering purchases.

### 1.4 New columns on `leads`

```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS pricing_tier VARCHAR(20);
-- 'standard' | 'professional' | 'premium' — set at qualification time
ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_price DECIMAL(10,2);
-- actual price charged, based on tier + service type
```

---

## 2. Pricing Module Changes (`pricing.py`)

Replace the entire pricing logic:

```python
# Tiered pricing by service type
TIERED_PRICES = {
    "standard": {
        "roof_inspection": 35,
        "real_estate_media": 25,
        "aerial_imaging": 40,
    },
    "professional": {
        "construction_progress": 150,
        "stockpile_volumetrics": 125,
        "topographic_data": 100,
        "mining_data": 150,
        "environmental_monitoring": 75,
    },
    "premium": {
        "lidar_scanning": 350,
        "multispectral_imaging": 200,
        "utility_inspection": 400,
        "3d_reality_capture": 500,
    },
}

# Reverse lookup: service_type -> tier
SERVICE_TIER = {}
for tier, services in TIERED_PRICES.items():
    for service in services:
        SERVICE_TIER[service] = tier

def get_lead_price(service_type: str) -> float:
    """Get the dollar price for a lead based on service type."""
    tier = SERVICE_TIER.get(service_type, "standard")
    return TIERED_PRICES.get(tier, {}).get(service_type, 40)

def get_lead_tier(service_type: str) -> str:
    """Get the pricing tier for a service type."""
    return SERVICE_TIER.get(service_type, "standard")

def get_lead_credit_cost(service_type: str) -> int:
    """Deprecated — kept for backward compat. Returns 0 (no credits)."""
    return 0
```

---

## 3. Stripe Integration Changes (`stripe.py`)

### 3.1 Remove credit package purchases

Remove `PurchaseRequest` and `POST /portal/credits/purchase` endpoint.

### 3.2 Add payment method on file

```python
@router.post("/portal/payment-method/setup")
async def setup_payment_method(contractor_id: str = Depends(require_auth), db=Depends(get_db)):
    """Create a Stripe Setup Intent for saving a payment method."""
    # Create Setup Intent, return client_secret
    # On confirmation, save payment_method_id to contractors table
```

### 3.3 Add lead charge endpoint

```python
@router.post("/portal/leads/{lead_id}/charge")
async def charge_for_lead(lead_id: str, contractor_id: str = Depends(require_auth), db=Depends(get_db)):
    """Charge contractor for an accepted lead."""
    # Look up lead_charges record
    # If billing_method == 'card_on_file': create PaymentIntent, charge
    # If billing_method == 'invoice': add to outstanding_balance, create Stripe invoice monthly
```

### 3.4 Add bad lead credit endpoint

```python
@router.post("/portal/leads/{lead_id}/credit")
async def credit_bad_lead(lead_id: str, reason: str, contractor_id: str = Depends(require_auth), db=Depends(get_db)):
    """Credit back a bad lead charge. Automated for qualifying reasons."""
    # Valid reasons: 'no-response', 'wrong-service-type', 'spam', 'out-of-area', 'budget-mismatch'
    # Update lead_charges.status = 'credited', refund if charged
```

### 3.5 Webhook update

Update `stripe_webhook` to handle `invoice.paid` and `payment_intent.succeeded` in addition to `checkout.session.completed`.

---

## 4. API Endpoint Changes

### 4.1 `routing.py` — `route_lead_to_contractors()`

Remove credit balance check:
```python
# OLD:
# AND credit_balance >= %s
# NEW:
# No credit check. Lead is routed exclusively to ONE contractor (territory claim holder).
```

Route to ONE contractor (territory + project type holder), not staggered to multiple.

### 4.2 `portal.py` — Dashboard endpoints

- `GET /portal/dashboard` — replace credit_balance with outstanding_balance + lead history + charges
- `GET /portal/leads` — show lead price for each lead
- `POST /portal/leads/{lead_id}/accept` — on acceptance, create lead_charge record
- `POST /portal/leads/{lead_id}/credit` — request bad lead credit

### 4.3 New endpoint: `GET /portal/billing`

Returns: outstanding balance, charge history, payment method status.

---

## 5. Contractor Portal UI (`dashboard/index.astro`)

### Remove
- Credit balance display
- "Buy Credits" button + package selection
- Credit transaction history

### Add
- Outstanding balance display (if any)
- Payment method on file status (add/update card)
- Lead history with price per lead shown
- "Request Credit" button on each lead (with reason dropdown)
- Billing history (invoices/charges)

### `/surveyors.astro` (public page)

### Remove
- "Buy credits" pricing table (starter/standard/bulk)
- "1 credit = 1 lead" explanation

### Add
- Tiered pricing display:
  - "Standard leads: $25-50" (roof inspections, real estate, basic imaging)
  - "Professional leads: $75-200" (progress monitoring, stockpile, topographic)
  - "Premium leads: $200-500" (LiDAR, 3D scanning, utility inspection)
- "Pay per qualified lead. No subscription. No credits. Bad leads credited automatically."
- "Exclusive — you're the only contractor who gets each lead."

---

## 6. Lead Billing Flow

1. Lead comes in, gets qualified, classified to tier + price
2. Lead routed to ONE contractor (territory + project type holder)
3. Contractor receives notification with lead details + price shown
4. Contractor accepts or declines
5. If accepted: `lead_charges` record created with status='pending'
   - If card_on_file: auto-charge immediately, status='paid'
   - If invoice: add to outstanding_balance, invoice monthly or when threshold hit ($100)
6. Contractor can request credit within 7 days if lead is bad
7. Valid credit reasons (auto-approved): no-response, wrong-service-type, spam, out-of-area, budget-mismatch
8. Credit updates lead_charges.status='credited', refunds if already charged

---

## 7. Migration Plan

### For existing contractors (currently 1):
1. Convert existing credit_balance to account credit (dollar equivalent at their purchase price)
2. Send email: "We're switching to pay-per-lead. Your remaining credits are now $X account credit. You'll be billed per lead going forward."
3. New billing starts on next lead acceptance
4. Account credit applied to first charges until depleted

### Stripe migration:
1. Create new Stripe products/prices for each tier (or use inline pricing)
2. Keep old credit package prices active for 30 days (in case of pending purchases)
3. Deactivate old prices after migration complete

---

## 8. File List (Priority Order)

### P0 — Core pricing change
1. `app/pricing.py` — replace credit system with tiered pricing
2. `app/database.py` — add lead_charges table, new contractor columns, new lead columns
3. `app/routers/routing.py` — remove credit check, route to single contractor
4. `app/routers/stripe.py` — remove credit purchases, add payment method + lead charge + credit endpoints
5. `app/routers/portal.py` — update dashboard endpoints, add billing endpoint

### P1 — UI updates
6. `src/pages/dashboard/index.astro` — remove credits UI, add billing/charges UI
7. `src/pages/surveyors.astro` — replace credit packages with tiered pricing display

### P2 — Migration + cleanup
8. Migration script: convert credit_balance to account credit
9. Email template: pricing transition notification to existing contractors
10. `app/routers/admin.py` — add billing overview to admin dashboard
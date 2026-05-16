# Sender Readiness Checklist — Ambassador Outreach

Must be complete before ANY outreach email is sent. All 5 items must be ✅.

---

## 1. Email Authentication

- [ ] **SPF record** published for truejoybirthing.com (or the sending domain) authorizing Brevo's sending IPs
  - Check: `dig TXT truejoybirthing.com` — look for `v=spf1 include:spf.brevo.com ...`
  - If missing: add SPF record via DNS

- [ ] **DKIM record** published for Brevo's signing key
  - Brevo provides the DKIM CNAME/TXT record during domain setup
  - Check: `dig TXT brevo._domainkey.truejoybirthing.com`
  - If missing: complete Brevo domain authentication flow

- [ ] **DMARC record** published (preferably `p=none` or `p=quarantine` to start)
  - Check: `dig TXT _dmarc.truejoybirthing.com`
  - Minimum: `v=DMARC1; p=none; rua=mailto:support@truejoybirthing.com`
  - Preferred: `v=DMARC1; p=quarantine; rua=mailto:support@truejoybirthing.com; pct=100`

## 2. Sender Identity

- [ ] **From name:** Shelbi Kohler, CD(DONA)
- [ ] **From email:** Must be a truejoybirthing.com address (e.g., shelbi@truejoybirthing.com or support@truejoybirthing.com)
- [ ] **Reply-to:** Set to a real monitored inbox
- [ ] **Physical mailing address:** Must appear in every email footer (required by CAN-SPAM)
  - Address to use: ____________________  (Jeff to confirm)
  - Can be PO Box — must be real and deliverable

## 3. Opt-Out Handling

- [ ] **Opt-out mechanism:** Every email includes clear unsubscribe link or "reply STOP to opt out"
- [ ] **Opt-out honored within 10 business days** (CAN-SPAM requirement)
- [ ] **Suppression list maintained** in Brevo — anyone who opts out is never emailed again
- [ ] **Process for handling replies:** Someone monitors the reply inbox and processes opt-outs promptly

## 4. First Batch Controls

- [ ] **First batch: 5–10 emails maximum** (not per city — total across all cities)
- [ ] **Each recipient manually approved** — not just the template, but the specific recipient list
- [ ] **Sending throttled:** Spread over 2-3 hours, not batch-sent
- [ ] **Bounce rate monitor:** If >5%, pause and investigate before continuing
- [ ] **Spam complaint monitor:** If any spam complaint arrives, pause immediately and report

## 5. Content Compliance

- [ ] **No purchased/rented lists** — all emails from public business sources only
- [ ] **Subject line truthful** — no misleading or deceptive headers
- [ ] **Health claims disclaimer** — no claims the app provides medical advice or guarantees outcomes
- [ ] **Clear identification** — email clearly states it's from True Joy Birthing
- [ ] **Transactional/relationship framing** — one-to-one outreach, not bulk advertising
- [ ] **Texas practitioners only** (for now) — verified as active businesses in-state

---

## Auto-Pause Rules

| Metric | Threshold | Action |
|---|---|---|
| Bounce rate | > 5% | Auto-pause, report to Jeff |
| Spam complaint | Any | Auto-pause immediately |
| Lead quality | < 30% verified emails | Pause collection, reassess sources |
| Similar-city page similarity | > 65% (D1 check) | Pause deployment, flag for review |

---

## Status

- [ ] SPF configured
- [ ] DKIM configured
- [ ] DMARC configured
- [ ] Physical address confirmed by Jeff
- [ ] Reply inbox monitored
- [ ] Suppression list active in Brevo
- [ ] First batch recipient list approved by Jeff
- [ ] Ready to send: ☐
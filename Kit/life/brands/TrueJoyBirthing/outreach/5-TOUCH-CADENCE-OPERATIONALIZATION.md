# TJB 5-Touch Professional Outreach â Cadence Operationalization

**Date:** 2026-09-18
**Author:** Content/skill subagent (Jeff directive 2026-09-18)
**Status:** OPERATIONAL PLAN â recorded for the next outreach run. No live infra created (per "do not deploy" hard rule); tag-create calls are documented as the run's prerequisite.

---

## 1. Purpose

Wire the 5-touch provider-outreach sequence (spec: `projects/tjb-alignment-review/findings/09-outreach-reframe.md`, added 2026-09-18) into TJB's actual outreach pipeline so multi-touch follow-ups are **planned and executable**, not a single first-touch-and-stop.

The sequence is foot-in-the-door (FITD): Email 1 verifies the listing (tiny ask) â Email 2 introduces the free tool â Email 3 social-proof + first direct CTA â Email 4 ambassador invite (long-tail nurture) â Email 5 come-back reminder (final touch). Reply at any point stops the sequence and routes to Shelbi.

---

## 2. Operational home (file paths)

This is where the cadence actually lives today. The next run reads/writes these.

| Layer | Path | Role |
|---|---|---|
| Sequence spec | `Kit/life/brands/TrueJoyBirthing/projects/tjb-alignment-review/findings/09-outreach-reframe.md` | Email 1â5 copy, triggers, day-counts, psychology |
| This doc | `Kit/life/brands/TrueJoyBirthing/outreach/5-TOUCH-CADENCE-OPERATIONALIZATION.md` | Cadence wiring / mapping (operational home record) |
| Cron schedule | `Kit/life/brands/TrueJoyBirthing/TRUEJOYBIRTHING-CRON-JOBS.md` â **TJB G57** (Doula/Midwife Outreach Bot, Mon/Wed/Fri 06:30 MT) + **Catch-Up Queue Builder** (daily 16:05 UTC) + **Catch-Up Sweep** (daily 17:15 UTC) | When cadence fires |
| Queue builder | `~/.hermes/scripts/tjb-outreach-catchup.py` | Builds `~/.hermes/state/tjb-outreach-catchup-queue.json` (cities needing first-touch) |
| Sweep | `~/.hermes/scripts/tjb-outreach-catchup-sweep.sh` â `tjb-batch-outreach.py catchup --catchup --limit 2` | Sends â¤2 cities/day, â¤15 first-touch emails/day, mid-city resume via `~/.hermes/state/tjb-outreach-catchup-progress.json` |
| Send + gate | `~/.hermes/scripts/tjb-outreach-send.py` (Gate 0c: 30-day dup window, ever-contacted, 4-touch cap, opt-out blocklist, bounce) | Per-send quality + safety gate |
| Send transport | `~/.hermes/scripts/mail_client.py` (VPS `mail.agentictrust.app`, sender `shelbi@truejoybirthing.com`) â per `OUTREACH-SENDING-POLICY.md` | Actual email delivery (VPS, NOT MailerCloud SMTP) |
| Send log | `~/.hermes/logs/tjb-outreach-send-log.jsonl` | Source of truth for "last touch date" + which email number |
| Opt-out blocklist | `~/.hermes/logs/tjb-opt-out-blocklist.jsonl` (auto-fed by reply handling) | Stop condition |
| MailerCloud list | **`wHHZHw` â "TJB Provider Outreach - Engaged"** (22 contacts, verified 2026-09-18 via `POST /lists/search`) | Canonical registry + per-provider touch-state tags |
| MailerCloud facts | `Kit/life/brands/TrueJoyBirthing/mailercloud-integration.md` (raw `Authorization` header, no Bearer; curl not urllib; tags/custom-fields must pre-exist) | API contract |

> **No new cron job.** The cadence rides the existing G57 + Catch-Up schedule (Jeff hard rule: default NO new crons). If a dedicated multi-touch sweep is later wanted, document the recommendation â do not create one here.

---

## 3. Mapping: sequence stages â MailerCloud lists/tags

The "TJB Provider Outreach - Engaged" list (`wHHZHw`) is the **canonical registry** for the multi-touch sequence. Each provider who enters outreach is added to this list; their current touch and status are tracked by **account-level tags** (MailerCloud tags are account-global per `mailercloud-integration.md`). The *send transport* stays the existing VPS `mail_client.py` path; MailerCloud holds the **cadence/touch-state**, not the SMTP send.

### Tag schema (pre-create before first use)

| Tag | Meaning | Set when |
|---|---|---|
| `outreach-e1` | Email 1 sent (community verification) | After E1 send logged |
| `outreach-e2` | Email 2 sent (free tool intro) | After E2 send logged |
| `outreach-e3` | Email 3 sent (social proof + CTA) | After E3 send logged |
| `outreach-e4` | Email 4 sent (ambassador invite) | After E4 send logged |
| `outreach-e5` | Email 5 sent (come-back reminder, final) | After E5 send logged |
| `outreach-replied` | Provider replied to any email | On reply detection (stops sequence) |
| `outreach-optout` | Provider opted out ("stop") | On opt-out (removed from all future) |
| `outreach-downloaded` | Detected app download / profile created | On download signal (routes to ambassador) |
| `outreach-ambassador` | Invited/accepted ambassador program | When E4 sent OR on download (route to `wHHZHH` Ambassadors) |

Naming follows the existing TJB tag convention (lowercase, hyphenated: `ambassador`, `applied`, `confidence-session`).

### Prerequisite: create the tags (run-once, before next outreach run)

Tags must pre-exist before any upsert references them (verified 400s in `mailercloud-integration.md`). Create with the verified `POST /tags` endpoint (from `skills/mailercloud-control/SKILL.md`):

```bash
# Auth: raw Authorization header, NO "Bearer". Use curl (Cloudflare blocks urllib on cloudapi.mailercloud.com).
KEY=$(grep '^MAILERCLOUD_API_KEY=' ~/.hermes/.env | tail -1 | sed 's/^MAILERCLOUD_API_KEY=//' | sed "s/^[\"']//;s/[\"']$//")
for t in outreach-e1 outreach-e2 outreach-e3 outreach-e4 outreach-e5 outreach-replied outreach-optout outreach-downloaded outreach-ambassador; do
  curl -s -X POST https://cloudapi.mailercloud.com/v1/tags \
    -H "Authorization: $KEY" -H "Content-Type: application/json" \
    -d "{\"name\":\"$t\"}"
done
```

After creation, confirm with `POST /tags/search`. Then the cadence controller tags contacts on `wHHZHw` as each touch lands.

---

## 4. Day-counts between touches

| Stage | Email | Gap from prior | Condition | App mention |
|---|---|---|---|---|
| 1 | Email 1 â Community verification | Day 0 (entry) | Always (provider enriched + email verified + city page live) | None |
| 2 | Email 2 â Free tool intro | **+5â7 days** after E1 | Regardless of reply (acknowledge reply if present) | Yes, utility-frame, no link |
| 3 | Email 3 â Social proof + FOMO | **+10â14 days** after E2 | **Only if no reply** to E1/E2 | Yes, with download link (first direct CTA) |
| 4 | Email 4 â Ambassador invite | **+4â6 weeks** after E3 | Only if no reply + no app download | Implied (ambassador frame) |
| 5 | Email 5 â Come-back reminder | **+8â10 weeks** after E3 (final) | Only if no reply + no download | Yes, "moms find someone else" stakes |

**Stop conditions (sequence halts, contact exits active outreach):**
- Reply to any email â tag `outreach-replied`, route to Shelbi's inbox, no further automated sends.
- Opt-out ("stop") â tag `outreach-optout`, add to `~/.hermes/logs/tjb-opt-out-blocklist.jsonl`, removed from all future sequences.
- App download detected â tag `outreach-downloaded`; route to ambassador program (skip E4's "invite" framing since already engaged; add to `wHHZHH` Ambassadors).

After Email 5 with no reply/download, the provider stays on the city page but exits active outreach (tag `outreach-e5` is terminal).

---

## 5. Next-run execution plan (so all 5 touches fire)

The existing catch-up scripts currently handle **first-touch only** (they find cities with no first-touch send and ship E1). Multi-touch requires extending the cadence controller to also drive E2âE5. The next run should:

1. **Prereq:** create the 9 tags (Â§3) on MailerCloud; confirm `wHHZHw` is the registry list.
2. **On each cadence fire (G57 Mon/Wed/Fri + daily Catch-Up Sweep):** read `~/.hermes/logs/tjb-outreach-send-log.jsonl` for each provider on `wHHZHw`, compute days-since-last-touch from the log timestamp + the provider's highest `outreach-eN` tag.
3. **Select next email** by the Â§4 matrix:
   - No `outreach-e1` â send E1, tag `outreach-e1`.
   - Has `outreach-e1`, â¥5â7d elapsed, no `outreach-replied`/`outreach-optout` â send E2, tag `outreach-e2`.
   - Has `outreach-e2`, â¥10â14d elapsed, no reply â send E3, tag `outreach-e3`.
   - Has `outreach-e3`, â¥4â6wk elapsed, no reply + no download â send E4, tag `outreach-e4` (or route to ambassador on download).
   - Has `outreach-e3`, â¥8â10wk elapsed, no reply + no download â send E5, tag `outreach-e5` (terminal).
4. **Apply the send gate** (`tjb-outreach-send.py` Gate 0c) + budget caps (â¤15 emails/day, â¤2 cities/day) before every touch â the same gates that protect first-touch.
5. **Humanize each email** per `skills/humanize-content/SKILL.md`: Passes 1, 3, 4 only (clean prose, no intentional typos â Pass 6 email rule). Pull **real per-city anchors** (actual hospitals, named peers, local specifics) from the strengthened Pass 6 Pillar 2 so each touch is genuinely local, not templated.
6. **Log + tag:** after a successful VPS send, append to `tjb-outreach-send-log.jsonl` AND upsert the contact on `wHHZHw` with the new `outreach-eN` tag (and `outreach-replied`/`outreach-optout`/`outreach-downloaded` as events occur).

**Implementation note:** extending `tjb-batch-outreach.py` / a new `tjb-outreach-cadence.py` to read the send-log + MailerCloud tags and emit the correct next touch is the concrete build. That code change is **out of scope for this content/skill task** (no deploy) â this doc is the wired plan the next run executes against.

---

## 6. Content guardrails (from strengthened Pass 6, 2026-09-18)

- Emails use **humanize Passes 1, 3, 4** (no typos / imperfect grammar in email â variance lives in web/long-form, never in outbound email).
- Each touch must open with a **real, city-specific anchor** (named hospital, real peer, local fact) â this is the primary anti-template defense and satisfies Google helpful-content review.
- **Policy-safe:** never spam-pattern stuff; present any human variance as natural; the goal is to pass helpful-content review, not game a detector.

---

*Operationalization recorded 2026-09-18. Reflects Jeff's 2026-09-18 directive to run the full 5-touch sequence with multi-touch follow-ups actually planned.*

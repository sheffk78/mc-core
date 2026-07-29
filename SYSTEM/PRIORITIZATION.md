# Prioritization Framework — How Kit Decides What to Work On
<!-- ROUTING: Load when deciding what to prioritize for the session -->

_Created: 2026-04-26. Jeff delegates priority-setting to Kit. This file is Kit's decision framework._

---

## Core Principle

Kit sets day-to-day priorities. Jeff reviews and adjusts weekly (or daily if he wants). Kit doesn't ask "what should I work on?" — he tells Jeff "here's what I'm working on and why" and Jeff corrects course if needed.

---

## Priority Matrix

Tasks fall into four tiers. Kit works top-to-bottom, always.

### Tier 1: Revenue-Blocking (Do Now)
Anything where money is on the table right now:
- Broken checkout, payment, or signup flow
- Site down or returning errors
- A blocked task where Jeff's action is the only unblock
- A launch that's ready to ship but waiting on one small thing

**Rule:** If Tier 1 exists, Kit works it until it's done or genuinely blocked. No context-switching to lower tiers.

### Tier 2: Revenue-Enabling (Do This Week)
Work that directly enables revenue but isn't urgent this minute:
- Feature sprints that close gaps between marketing promises and product reality
- Content or outreach that fills the pipeline
- SEO/visibility work that drives inbound
- Ambassabor/affiliate program setup

**Rule:** Kit picks the highest-impact Tier 2 task and makes meaningful progress every session. He doesn't spread thin across five tasks — he finishes or substantially advances one, then rotates.

### Tier 3: Infrastructure & Hygiene (Keep the Lights On)
Work that prevents future problems but doesn't move revenue today:
- MC hygiene and process improvements
- Documentation updates
- Cron health and monitoring
- Code quality improvements that aren't blocking anything

**Rule:** Tier 3 gets done in the margins — between Tier 1 and 2 work, or during sessions where higher tiers are genuinely blocked. No more than 20% of a session on Tier 3.

### Tier 4: Nice-to-Have (Defer)
- Exploratory research
- Non-urgent brand polish
- Ideas without clear next steps
- Tasks that have been open >14 days with no movement

**Rule:** Kit doesn't start Tier 4 work. He keeps it on the board and surfaces it in weekly reviews. If it sits for 30+ days with no movement, he proposes archiving it.

---

## Brand Rotation Rule

Each session, Kit checks: "Which brand has had zero output in the last 48 hours?" That brand gets the next slot, unless a Tier 1 task exists on another brand.

If all brands have had recent output, Kit follows the priority matrix above (revenue impact first, brand second).

**Target:** Every brand gets at least one meaningful action per 48-hour window, unless Jeff explicitly deprioritizes it.

---

## Due Date Management

Every new task gets a default due date:
- **Critical/High:** 7 days from creation
- **Normal:** 14 days from creation
- **Low:** 21 days from creation

Kit can extend a due date by up to 7 days without asking. Beyond that, he flags it for Jeff's review.

Overdue tasks are automatically promoted one priority tier. If a task is overdue by 7+ days, Kit proposes either completing it this session or archiving it.

---

## Daily Review (For Jeff)

**Time:** 5 minutes, ideally morning
**Format:** Kit posts a daily review to Discord #general with:

```
📋 DAILY REVIEW — {date}

**Working on:** {one-line description of today's top task}
**Why:** {revenue impact or strategic reason}
**Expected output:** {what done looks like}

**Board status:** {X open, Y in_progress, Z blocked}
**Stale items:** {list any tasks >48h with no update}

**Asks for Jeff:** {0-2 items that need Jeff's input}
```

Jeff can:
- Reprioritize (reply with "X before Y")
- Approve (thumbs up or no response = proceed)
- Add tasks
- Ask questions

**No response within 2 hours = approval to proceed.**

---

## Weekly Review (For Jeff)

**Time:** 15-20 minutes, Sunday evening or Monday morning
**Format:** Kit prepares, Jeff reviews and adjusts

Kit posts:
```
📋 WEEKLY REVIEW — Week of {date}

**Shipped this week:**
- {completed items with impact notes}

**Carried over:**
- {items that didn't finish, with reason}

**Proposed focus for next week:**
- {3-5 ranked priorities}

**Board cleanup:** {archiving X stale items, propose Y for deletion}

**Decisions needed:**
- {1-3 strategic questions where Jeff's input changes the direction}
```

Jeff:
- Confirms or reorders next week's priorities
- Makes decisions on strategic questions
- Approves or modifies archiving proposals

---

## How Kit Decides (Decision Log)

When Kit picks a task that might not be obviously the top priority, he writes a one-line reason in the daily note. This creates an audit trail Jeff can review.

Examples:
- "Picked TrustOffice feature sprint over WingPoint outreach because feature gap = churn risk for existing users"
- "Picked WingPoint affiliate program over TJB comments because affiliate program = direct revenue, TJB comments = brand awareness"
- "Picked TrustMinutes site fix over TrustOffice audit trail because site down = zero conversions"

---

## Amendment Process

Jeff can change this framework at any time. Changes go here with a date and his initials. Kit proposes changes via `pending_review` tasks tagged `framework`.

**Current amendments:** (none yet)
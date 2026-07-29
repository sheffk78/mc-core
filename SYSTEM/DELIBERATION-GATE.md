# DELIBERATION GATE — Protocol for Significant Decisions
<!-- ROUTING: Load before significant decisions, architecture changes, or strategic pivots -->

_Load on demand: when making non-trivial decisions (new features, architecture, $50+ spend, strategy pivots)._

---

## When Deliberation Triggers

| Decision Type | Deliberate? | Why |
|---|---|---|
| Bug fix with clear root cause | No | Just fix it |
| Content draft, social post | No | Ship at 80%, iterate |
| Routine task, well-established lane | No | Execute, don't deliberate |
| **New feature direction** | **Yes** | High-impact, reversible but costly |
| **Architecture change** | **Yes** | Structural, hard to undo |
| **$50+ spend decision** | **Yes** | Financial commitment |
| **Strategy pivot** | **Yes** | Direction change |
| **Brand direction change** | **Yes** | Voice/identity risk |
| **Major code deployment** | **Yes** | Production risk |

## How It Works

1. **Kit frames the question.** A concise writeup: what's the decision, what are the options, what are the tradeoffs, and Kit's recommendation.

2. **Kit spawns 2-3 sub-agents via `delegate_task`.** Each gets the same question independently — no context from each other's answers. Independence comes from different prompt framing, not different model architectures.

3. **Kit synthesizes.** Where perspectives agree = high confidence. Where they disagree = surface the disagreement with Jeff's input needed.

4. **Kit decides or escalates.** Within delegated authority: proceed with the direction supported by deliberation. Strategic decisions: surface to Jeff with the deliberation summary.

## Implementation

```python
# Quick panel (2 perspectives, medium tasks)
delegate_task(tasks=[
    {"goal": "Analyze from a risk-first perspective...", "context": "..."},
    {"goal": "Analyze from an opportunity-first perspective...", "context": "..."},
])

# Full panel (3 perspectives, important tasks)
delegate_task(tasks=[
    {"goal": "Analyze risks and failure modes..."},
    {"goal": "Analyze opportunities and upside..."},
    {"goal": "Analyze feasibility and execution constraints..."},
])
```

## Deliberation Output Format

```
DECISION: [one-line question]
KIT RECOMMENDATION: [Kit's initial take]

DELIBERATION RESULTS:
┌─────────┬────────────────────┬─────────────────────────┐
│ Model   │ Verdict            │ Key Insight              │
├─────────┼────────────────────┼─────────────────────────┤
│ [name]  │ [Yes/No/Conditional] │ [1-line key point]       │
│ [name]  │ [Yes/No/Conditional] │ [1-line key point]       │
│ [name]  │ [Yes/No/Conditional] │ [1-line key point]       │
└─────────┴────────────────────┴─────────────────────────┘

AGREEMENT: [X/3 lean direction]
DISAGREEMENT: [surface key disagreement]
ACTION: [what Kit is doing, or what needs Jeff's call]
```

## Boil the Lake

When executing after deliberation, complete the work:
- Fix *all* related bugs, not just the reported one
- Add edge cases and error handling
- Write tests for the fix

"Ship the shortcut" is legacy thinking from when human engineering time was the bottleneck.

## Task Delegation Protocol

**When a skill exists for a task OR instructions are clear enough for a subagent to follow:**

1. Load the relevant skill via `skill_view(name="...")` — this is NOT optional
2. Delegate to a subagent with: skill content, full context, appropriate toolsets
3. Kit reviews, validates, and delivers results

**What to delegate:** Content generation, file operations, SEO tasks, research with skills, complex builds, code edits, batch operations (>3 tool calls).

**What NOT to delegate:** Tasks requiring user interaction (Kit handles), tasks faster inline, tasks requiring web browsing (delegate with web toolset).
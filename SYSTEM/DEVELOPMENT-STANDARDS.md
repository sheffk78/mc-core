# Kit Development Standards
<!-- ROUTING: Coding standards and review process -->

**How you build. What "done" means. The bar every change clears before it reaches a user.**

Read alongside the Charter (`SYSTEM/AGENTS.md (charter folded in)`). Where this document and the Charter conflict, the Charter wins.

---

## The Code Bar

Every line of code you write or merge meets these:

- **Readable first.** A new engineer should understand it without explanation. No clever tricks, no minimized variable names, no hidden side effects.
- **Typed where the stack supports it.** TypeScript, Pyright/mypy, Sorbet — whatever applies. Untyped code is provisional and gets typed when touched.
- **Tested.** Unit tests for logic. Integration tests for contracts. End-to-end tests for user-facing flows. (See Testing below.)
- **Linted and formatted.** No style debates in PRs. Tooling decides.
- **Documented when non-obvious.** If a future engineer or AI would ask "why?", leave a comment that answers.
- **Secure by default.** Never trust user input. Never log secrets. Never disable a security check to make a test pass.
- **Boring where possible.** Reach for novel patterns only when a boring one will not do. The next person to touch this code is the one who matters.

---

## Subagent Review

You do not ship code reviewed only by yourself.

For meaningful changes:

1. **Generate or draft** the change.
2. **Adversarial review.** Spawn a subagent via `delegate_task` with the diff and an adversarial prompt: *"Find what's wrong with this diff. Where will it break? What edge cases did the author miss? What's the worst-case failure?"* Do not ask for approval — ask for problems.
3. **Synthesize.** Real critiques are addressed. Spurious ones are noted and dismissed with reasoning. The exchange is logged in the PR description.

This is non-negotiable on:

- Anything touching authentication, authorization, payments, or user data
- Database migrations (especially destructive ones)
- Public API changes
- Performance-critical paths
- Anything you do not fully understand yet
- Anything that, if wrong, would be expensive to detect later

For everything else, single-model self-review is acceptable but a quick adversarial pass is encouraged.

---

## Testing — Three Layers, All Required

### Layer 1: Developer testing
Unit + integration tests run in CI. They must pass. No `skip` decorators left in. No commented-out tests.

### Layer 2: Human-simulation testing
Every user-facing change is exercised through a real browser by an automated agent. **Playwright is the default**; Cypress is acceptable. The script does what a person would do — navigate, click, fill forms, scroll, wait for animations, verify the visible state.

This includes:

- The happy path on the change
- One realistic failure path (bad input, network error, missing permission)
- Mobile viewport (375px wide minimum)
- Keyboard-only navigation through the affected component
- Screen-reader semantic check (axe-core or equivalent — no new violations)

### Layer 3: Holistic human review
Before declaring done, you load the change in a real browser and look at it. Does it feel right? Is the timing of the animation actually pleasant? Does the empty state make sense? Is anything visually off — a misaligned border, an icon at the wrong baseline, a button a half-shade too dark? You catch what tests cannot.

**If any layer fails, the change is not done.** No partial credit.

---

## The Anti-Slop Standard

Our work does not look or read like default AI output. Users can tell. Hold this line.

### Visual red flags to actively eliminate

- Generic purple-to-blue gradient backgrounds with no brand reason
- Glassmorphism applied to everything that holds still
- Sparkle, star, or magic-wand iconography to denote "AI" or "smart"
- Tailwind/Bootstrap defaults left unmodified
- Animations that exist only to fill time (slow fades, bouncing entrances) with no narrative purpose
- Decorative emoji as visual filler in body copy (✨🚀💫)
- Centered single-column layouts where content should be denser
- Lorem ipsum left in production
- Stock photography of diverse people in glass-walled offices smiling at laptops
- Three-card grids beneath every hero, regardless of whether the content is actually parallel

### Copy red flags

- *"Unleash the power of…"*, *"Welcome to the future of…"*, *"Revolutionize your…"*
- Em-dashes used as a tic rather than for rhythm
- Three-item lists where every item shares the same syntactic structure
- *"I'd be happy to help you with…"* or other AI-assistant cadence in product copy
- Empty hedging — *"perhaps,"* *"you might want to,"* *"it could be that"*
- Marketing voice when plain voice would do
- Headers that summarize the paragraph that follows

### The test

Would a sharp human writer or designer leave this in? If they would cut it, you cut it.

### The only exception

Interfaces consumed by other AI agents may prioritize machine-readability and structure over polish. For everything humans see, the standard above applies without exception.

---

## Deployment Standards

- **Branches and PRs.** No direct commits to main. Every change goes through a PR, including yours.
- **Preview deployments.** Every PR gets a preview URL. Human-simulation tests run against it before merge.
- **Feature flags for risk.** Anything with non-trivial blast radius is wrapped in a feature flag. Roll out 5% → 25% → 100% with monitoring at each step.
- **Reversibility.** Every deploy can be rolled back in under a minute. Database migrations have a tested rollback plan written before the migration runs.
- **Smoke test post-deploy.** After production deploy, you run a brief smoke test (key flows still work) and confirm error rates and latency are flat for at least 15 minutes before considering the deploy complete.
- **No Friday afternoon production deploys** unless you are around to watch them and roll back if needed.

---

## The Quality Gate — "Done" Means All Of:

A change is not done until:

- [ ] Unit + integration tests pass in CI
- [ ] Lint and type-check clean
- [ ] Subagent adversarial review consulted (where required) and addressed
- [ ] Human-simulation E2E test added or updated and passing
- [ ] Accessibility check passes — no new violations
- [ ] Lighthouse / Core Web Vitals not regressed beyond agreed thresholds
- [ ] Manually reviewed in a browser at desktop and mobile widths
- [ ] Deployed to staging and exercised by hand
- [ ] Deployed to production
- [ ] Production monitoring confirms healthy for at least 15 minutes
- [ ] Action notification written and sent

If any of these is skipped, you note why in writing on the PR.

---

## Hermes Integration Notes

- **Subagent review** above is satisfied by spawning a dedicated reviewer subagent via `delegate_task`.
- **Tool selection** defaults to the Kit Toolbox (`SYSTEM/TOOLS/SELECTION-GUIDE.md`). When swapping tools, log the reason in the toolchain changelog.
- **Model config** — see `SYSTEM/ROUTER-RULES.md` for current model configuration.
- **Cost discipline** — see `SYSTEM/ROUTER-RULES.md` for cost details and fallback chain.

---

## Changelog

*(empty — append entries as standards evolve)*

---
name: humanize-content
description: "Post-processing pipeline that makes AI-generated content pass AI-slop detection (Google scaled-content enforcement, GPTZero-class detectors). Loads whenever drafting, reviewing, or publishing generated content for any brand site/blog/email. Runs a 7-pass humanization checklist over AI text, then scores it with a deterministic tell-scanner."
user_invocable: true
command: humanize
---

# Humanize Content — AI-slop-resistance pipeline

**Why this exists:** Google's 2026 enforcement (S-CTS system + scaled content abuse policy) grades *coordination and templating across properties*, not AI authorship per se — "not anti-AI, anti-crap." Sites publishing templated AI pages at scale lost 50–80% of organic traffic in the March 2026 core update. Separately, text-level detectors key on surface statistics (perplexity, burstiness, stylometry) and discourse structure. This skill handles both layers.

**The single most important finding from the detection literature:** surface rewrites (word swaps, fixing em dashes) moved detector accuracy by only ~1.6 points in a 61,608-text study. Structural tells are the durable fingerprint: uniform sentence rhythm, tidy resolution, vague reference, performed emotion. Word fixes are pass 1; structure is where passing actually happens.

**Hard integrity rule (never violate):** never invent facts, numbers, quotes, or sources to sound human. False specificity is worse than no specificity — it is itself an AI tell (confident hallucination) and a trust risk on brand content.

**Brand-voice precedence (load order rule):** load the brand's `BRAND-VOICE.md` BEFORE running any pass. Brand voice is the authority on what the text should sound like; this skill removes AI tells so the text passes detection. Never strip legitimate brand-voice markers (e.g., TJB's warm/nurturing register, WingPoint's teaching cadence) — soften only the AI-generic phrasing around them. Where the two conflict, brand voice wins for word choice; this skill wins for structure, punctuation rates, and rhythm.

---

## Pipeline: 7 passes, in order

Run on any draft before publish. Passes 1–2 are mechanical, 3–6 are LLM rewrite work, 7 is the gate. For scale (batch/city pages), spawn one subagent per batch chunk with the prompts in `references/rewrite-prompts.md`.

### Pass 1 — Strip the AI register (word level)
Kill the model's default voice. Full lists: `references/ai-tells.md`.
- **Preserve SEO while stripping:** keep target keywords and keyword density roughly where they started — strip the AI vocabulary AROUND the keyphrases, never the keyphrases themselves.
- Remove AI vocabulary: delve, leverage (verb), robust, comprehensive, pivotal, crucial, foster, facilitate, showcase, testament, tapestry, vibrant, seamless, landscape (abstract), journey, harness, unlock, elevate, realm, "in today's…", "ever-evolving", nestled, breathtaking.
- Remove stock transitions: Furthermore, Moreover, Additionally, In conclusion, "It's important to note that", "Let's dive in". Replace with nothing (assert directly) or "And"/"Which means…".
- Hedge surgery: delete "generally speaking", "in many cases", "typically", "often" unless accuracy requires the hedge. If uncertainty is real, state it human-style: "I'm not sure this holds past the first year, but…"
- Kill chatbot artifacts: "I hope this helps", "You're absolutely right", "Want me to…", knowledge-cutoff disclaimers, speculative gap-fill ("she likely grew up…").
- Punctuation ceiling: ≤1 em dash per 300 words (0 is safer); semicolons ~never (except city/state lists); no mid-sentence colons ("The problem: nobody tests this" → full sentence). Curly quotes → straight quotes in web content.

### Pass 2 — Fix the formatting tells
- No list items with bold "**Label:**" headings repeated 3+ times — convert to prose or plain list.
- Headings in sentence case, not Title Case And Title Case.
- No decorative emojis in headings/lists.
- No heading immediately restated by the first sentence under it.
- Don't end sections on generic optimism ("The future looks bright…"); end on the last concrete fact.
- Kill the forced rule-of-three ("innovation, inspiration, and industry insights") unless the three items are genuinely distinct.

### Pass 3 — Break the rhythm (burstiness — the biggest single lever)
Human writing alternates hard between short and long sentences. AI is metronomic (~15–20 words, low variance). Detection literature: human burstiness 0.6–1.2, GPT output 0.2–0.4.
- One sentence ≤6 words per ~150 words ("That number still bugs me.").
- Never three consecutive sentences within 5 words of the same length.
- Long sentences allowed only when the thought genuinely needs the connective tissue.
- Paragraph lengths must vary too — a page of five 90-word paragraphs is a template signature. Split one, merge two, leave a one-line paragraph.

### Pass 4 — Structure the way humans structure
Discourse features alone detected AI text at 93.2% F1 in the StoryScope study. Six audits:
1. **Theme explicitness** — AI states its lesson ("This shows why planning matters"). Humans imply it or arrive late. Cut stated morals.
2. **Structural tidiness** — AI opens every thread and closes every thread. Humans digress, leave something open, circle back late. Let one aside breathe.
3. **Emotion mode** — AI performs emotion through the body ("my hands shook as I signed"). Humans *name the feeling* plainly ("that stung", "I still don't love how that went"). The largest measured gap (81% vs 38%).
4. **Reference specificity** — name real things: the county office, the actual fee, the software, the street, the month. Vague allusion is a fingerprint.
5. **Reader engagement** — acknowledge the reader exists ("you've probably hit this too"), occasionally address them directly.
6. **Shape convergence** — compare against the last 3 pieces from the same brand/site. If this has the same skeleton (same section order, same intro formula, same closer), restructure. **This is the pass that matters most at portfolio scale** — Google's cluster detection hunts shared templates across properties.

### Pass 5 — Insert experience (the substance layer)
Detectors and readers both flag "no visible human behind this." Before writing, collect real anchors — client outcomes, actual prices paid, dates, city-office names, real mistakes and what they cost. Then:
- **Author entity:** published informational pieces carry a named author + linked bio with real credentials (and the brand's reviewer/author strip where the template has one). Google's March 2026 update raised entity-signal weight ~3.4×; authorship is both a trust signal and a humanization signal — the same action serves both.
- First-person where natural (blog, email, guides) — target ≥1 first-person marker per 1000 words minimum, far more in personal content.
- Numbers with units and context ($4,200, 11 days, 3 of 14 pages) — ≥1 per 1000 words minimum on informational content.
- Mixed feelings and unresolved tension kept in ("I think this is mostly good, but it bothers me").
- Genuine asides/self-correction ("(I keep wanting to say 'almost' here, but it really was certain.)").
- Dated, era-bound references (real current events, prices, tools of this year).
- If no real experience exists for the topic: use a specific sourced example from research, labeled as such — never fabricated experience.

### Pass 6 â Intentional humanization (PRIORITY signal â Jeff directive 2026-09-18)
**Reframe (2026-09-18, Jeff):** Humanization is no longer a cautious tiered afterthought â it is now a **PRIORITY signal**, the *primary* anti-AI-template defense. The old framing ("deliberate errors are the weakest lever, apply sparingly") is retired. Controlled human variance **plus** deep per-city customization make generated content read as written-by-a-person, and the per-city pillar is the stronger of the two against Google's cross-property cluster detection.

**Pillar 1 â Natural human variance (apply by default, not "if you dare").** A perfectly clean page is itself a tell. Real writers are imperfect; controlled variance is now expected texture:
- **Default-on textures:** a sentence starting with "And"/"But"; a casual comma splice; a fragment ("Which worked, mostly."); a parenthetical aside; colloquial phrasing ("cheaper than hiring it out", "which, honestly, surprised me"); inconsistent capitalization of a non-brand term in informal register.
- **Occasional imperfect grammar / typos:** one benign imperfection per ~500â1000 words is now *normal human texture*, not a risk to avoid. Aim for the density a real local writer produces â not zero (robotic), not stuffed (a pattern in its own right).
- **Never on data:** errors in numbers, names, legal citations, prices, URLs, alt text, schema markup, CTAs, or anything a scanner/customer parses. A typo in a phone number or statute citation costs more than slop detection ever will. Variance lives in prose, never in data.

**Pillar 2 â Deep per-city customization (the PRIMARY defense).** The strongest signal against Google's scaled-content / cluster detection, because it is *un-replicable across properties* and *genuinely useful to the reader* (exactly what helpful-content review rewards). For every city/page, bake in real, verifiable local texture:
- **Real local providers & hospitals:** name the actual hospitals, birth centers, and (where publicly listed) practices for the city â pulled from real city data, never invented (see integrity rule). A named real anchor beats any word-level trick.
- **Named specifics:** real street names, the county office, hospital NICU level, local fee amounts, state Medicaid posture, named peer providers on the same city page. Each city page needs facts that cannot appear on any sibling page.
- **Local texture:** the rhythm of the place â local phrasing, a landmark, a seasonal reference a resident would recognize. This is what makes two "city" pages feel written by two different people.
- **Why this beats word-level tricks:** surface rewrites moved detector accuracy only ~1.6 points in the 61,608-text study; structural + local-anchor variance is where passing actually happens. Per-city customization also serves E-E-A-T (entity signals weigh ~3.4Ã post-March-2026) and the helpful-content bar at once.

**Policy safety (non-negotiable):** the goal is to *pass Google helpful-content review*, not to game a detector. Present every imperfect construction as natural human variance inside otherwise accurate, useful prose â **never** as a detectable pattern. **Never spam-pattern stuffing:** do not inject imperfections at a uniform cadence, do not repeat the same "imperfection" template across pages (that is itself a cluster signature), and never sacrifice clarity or accuracy for the sake of variance. A page that genuinely helps a real person in {City} is the only acceptable output.

*This reframe reflects Jeff's explicit 2026-09-18 directive: humanization elevated from cautious add-on to PRIORITY signal, with deep per-city customization as the primary anti-AI-template defense.*

### Pass 7 — Gate with the scanner
```bash
python3 skills/humanize-content/scripts/scan_ai_tells.py draft.md
```
- **HIGH RISK (exit 1):** must rework — don't publish. Fix flagged items, re-run.
- **RISKY:** fix HIGH items; judge MEDs by context (list-heavy reference pages legitimately read tidier than blog posts).
- **PASS/PASSABLE:** ship.
- `--json` for pipelines: gate on `verdict` field. Batch mode: scan every file in the batch, none may be HIGH RISK, and across the batch check shape convergence (Pass 4.6) — near-identical burstiness/paragraph structure across pages is a cluster signature even when each page passes alone.

## Standing integration rules (Kenneth directive 2026-09-04)

**1. Forward — baked into every content-producing skill.** From now on, any skill or workflow that creates publishable text (blog articles, webpage copy, guides, landing pages, social posts, email newsletters) runs this pipeline as its final step before publish. The scanner gate is the last check, same class as a build test. Content skills should reference this skill in their own checklists so the pass is never optional or forgotten.

**2. Backward — opportunistic, piggybacked on other work.** NEVER run a mass "re-humanize all content" project. Instead: whenever we touch an existing page for any other reason — a SiteGuru audit recommends changes, an SEO fix, a factual update, a redesign — that edit session ALSO humanizes the page's text as part of the same change. One touch, two improvements. Scope: humanize the full page text during that touch (body copy; leave legal instruments and structured data alone). This steadily converts the backlog at zero extra scheduling cost.

**2b. Enforcement depth rule (2026-09-04 lesson):** skill wiring + cron prompt lines are NOT enforcement. Any pipeline with a state machine / gate executor must have the humanize check IN THE GATE CODE (fail-closed), or a non-compliant subagent ships anyway. Reference implementation: `preflight-stage-gate.py` in the TJB city orchestrator (H-HUMANIZE + H-SHAPE, live-verified 2026-09-04).

**Trigger map:**

| Work type | Humanize scope |
|---|---|
| New blog article / page copy / guide | Full pipeline, passes 1–7, before publish |
| SiteGuru (or any audit) recommends page changes | Full-page humanize bundled into that same edit |
| Factual update / refresh of existing page | Full-page humanize bundled into the same edit |
| New email newsletter / broadcast | Passes 1, 3, 4 only â clean prose, no intentional typos/imperfections (Pass 6 email rule: variance lives in web/long-form, never in email) |
| Social short-form | Passes 1 and 3, plus pass 4 digression if room |
| Legal/trust documents, compliance pages | Skip — formal register is correct; humanize the marketing around them |

## What NOT to do

- Don't stuff typos everywhere (Pass 6 Pillar 1 misuse) â reads as sloppy, hurts trust content, does nothing to strong detectors.
- Don't strip ALL polish from legal/trust document copy, compliance pages, or anything a customer files — those registers are *supposed* to be formal; humanize the marketing around them, not the instrument.
- Don't fabricate experience, data, or quotes (see integrity rule).
- Don't apply to client-facing deliverables where the client contract specifies polished copy.
- Don't chase a specific detector's score — write for human readers + Google's actual policy (value + non-templated). Detector scores drift; substance doesn't.
- Don't run humanization before fact-checking — humanizing fabricated content just launders it.

## Scale mode (city pages, programmatic SEO, batches)

This is where Google's enforcement actually bites. For any batch:
1. **Vary the template itself, not just the words:** rotate section order, intro strategies (question / anecdote / direct answer / data-first), and which modules appear (FAQ on some pages, cost breakdown on others).
2. **Unique anchors per page:** ≥3 page-specific facts that can't appear on sibling pages (county office name, local fee, state filing time, a local landmark, a real quote from a local source).
3. **Stagger publishing velocity** — 50 identical pages on one day is a cluster signature regardless of content quality.
4. Scan every page with the scanner (`--json`), plus a cross-page pass: if two pages share >70% paragraph-length shape and section sequence, rebuild one.
5. Prefer fewer, better pages. 30 pages with real local anchors beat 300 templated ones under this enforcement regime.
6. **Author/reviewer entity on every page** (brand byline standard — e.g., TJB city pages' E-E-A-T byline): same reviewer strip across the batch is fine (it's a template element, not a content template), but every page must carry it. Entity signals weigh ~3.4× more post-March-2026.

## Quick reference: what detectors actually measure

| Signal | AI fingerprint | Human | Fix pass |
|---|---|---|---|
| Burstiness (sentence-length variance) | 0.2–0.4 | 0.6–1.2 | 3 |
| Perplexity (word predictability) | 2–3x lower than human | — | 1 |
| Em dash rate | 3–5x human baseline | rare | 1 |
| Semicolon / mid-clause colon | elevated | near-zero | 1 |
| Discourse structure | tidy, resolved, restated | digressive | 4 |
| Specificity (named entities, numbers) | vague | anchored | 5 |
| Stated lessons/theme | 77% of AI paragraphs | 52% | 4 |
| Cross-page similarity | templated | varied | 6 / scale mode |

Full tell catalog: `references/ai-tells.md`. Subagent prompts per pass: `references/rewrite-prompts.md`.
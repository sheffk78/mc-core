# TOOLS/markdown-search.md

Fast local markdown search. **Prefer `qmd search` over `read` whenever you don't already know the exact file path.**

- **Version:** qmd 1.1.0 (Bun)
- **Collections:** `workspace` (skills, brand docs, daily notes, root files) · `life` (PARA knowledge graph)

```bash
qmd search "revenue metrics"                    # BM25, instant — default
qmd search "mission control" -c workspace
qmd search "brand voice" -n 10 --json
qmd search "competitor analysis" -c life

qmd get "qmd://workspace/MEMORY.md"
qmd get "#abc123"                                # by doc ID from search results
qmd ls workspace
```

**Performance hierarchy:**
- `qmd search` — instant, use by default
- `qmd vsearch` — semantic, ~1 min cold start, only when keyword fails
- `qmd query` — hybrid + rerank, slow and often times out, **avoid**

**Index maintenance (manual until cron lands):** run `qmd update` after any significant batch of file edits. `qmd embed` updates embeddings (slow, only needed for `vsearch`). Open `pending_review` task tracks cron automation.

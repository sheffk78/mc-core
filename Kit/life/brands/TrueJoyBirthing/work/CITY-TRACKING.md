# TJB City Tracking System

**File:** `Kit/life/brands/TrueJoyBirthing/city-priority-list.csv`

This is THE master list of all 1,143 cities in the TJB pipeline. It is the single source of truth for what exists, what needs work, and what's next.

## Columns

| Column | Values | Meaning |
|---|---|---|
| `build_status` | `built`, `not-built` | Does a page exist on truejoybirthing.com? |
| `upgrade_status` | `Denver-level`, `needs-upgrade`, (blank) | For built pages: is it finished to Denver standard? |

## Upgrade Status Meanings

| Status | Definition | Action |
|---|---|---|
| **Denver-level** | Has ALL: city-specific silhouette hero, custom support scene, hospital photos, provider headshots, OG image matching canonical template | None — page is complete. Move to next. |
| **needs-upgrade** | Built page but missing some/all Denver-level features (generic hero, no support scene, no hospital photos, all monograms) | This session's backlog. Pick 3 per batch. |
| *(blank)* | `not-built` — no page exists yet | Future work — not in this batch. |

## Workflow

1. **Always check this list first** when picking the next city to work on.
2. Filter `upgrade_status = needs-upgrade` — that's the current backlog.
3. Pick 3 cities per session, sorted by priority (highest population + tier first).
4. After completing each city, update its row to `Denver-level`.
5. Update `build_status` if a city goes from not-built to built.
6. Commit the CSV after every session so this is always current.

## Current Backlog

As of June 9, 2026, there are **49 cities** needing upgrade to Denver level.

Top priority (highest-value metro + tier):
1. Dallas, TX (rank 316 tier sweet-spot — largest DFW city)
2. Round Rock, TX (rank 320 — high-growth Austin suburb)
3. McKinney, TX (not in top 500 by CSV rank but Collin County growth market — manually added)
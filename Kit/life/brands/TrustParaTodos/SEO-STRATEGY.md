# Trust Para Todos — SEO Strategy & Opportunity Assessment
**Date:** August 13, 2026
**Domain:** trustparatodos.com

---

## 1. Executive Summary

**The Spanish-language trust market is wide open.** No competitor has built a productized, Spanish-first online trust creation platform. The existing players are either (a) local attorneys with basic bilingual pages, or (b) legal directories like abogado.com that explain concepts but don't sell a service. TrustParaTodos occupies a unique position: $997 complete package, 100% online, Spanish-first, with notary and EIN included.

**But the site is technically invisible to Google.** Only 2 pages are indexed. No Google Search Console, no GA4, no backlinks, no content beyond 9 static pages. This is a greenfield site that needs foundational SEO work before any ranking strategy can work.

---

## 2. SiteGuru Audit Results (August 13, 2026)

**Health score: 87** — good foundation, fixable issues.

### SiteGuru Todo List (5 items)

| # | Type | Severity | Issue | Status |
|---|---|---|---|---|
| 1 | Tech | Medium | Trailing slashes may cause duplicate content | ✅ FIXED — `trailingSlash: 'always'` in astro.config |
| 2 | Content | Medium | 4 pages have short meta descriptions | ✅ FIXED — expanded all 4 (evaluacion, contacto, testimonios, legal) |
| 3 | Content | Medium | 1 page missing H1 (/evaluacion) | ✅ FIXED — added visually-hidden H1 |
| 4 | Opportunity | High | Domain ranking 0/100 — no backlinks | 🔲 Phase 3 — authority building |
| 5 | Opportunity | Medium | Backlink spam score 65% | 🔲 Monitor — likely from domain history, disavow if needed |

### What passed clean
- ✅ All 9 page titles — proper length (46-60 chars), all server-rendered
- ✅ Structured data — zero issues (Organization + Service JSON-LD on all pages)
- ✅ Sitemap — valid, 9 pages, no errors/missing/redirected URLs
- ✅ Broken links — none
- ✅ Orphan pages — none
- ✅ SSL/HTTPS — passing
- ✅ WWW redirect — passing
- ✅ Favicon — passing
- ✅ 404 handling — passing
- ✅ robots.txt — passing
- ✅ Canonical URLs — properly set on all pages
- ✅ OG tags + Twitter cards — present on all pages
- ✅ hreflang tags — present (es, en, x-default)

### What's still missing (not flagged by SiteGuru but critical)
- \u2705 **Google Search Console connected** — verified in SiteGuru as of Aug 14
- \u2705 **Google Analytics 4 connected** — verified in SiteGuru as of Aug 14
- ⏳ **Data pending** — 0 clicks/sessions expected for 24-48h while Google processes
- ❌ **Only 9 pages** — need 40+ for keyword coverage (Phase 2)
- ❌ **No blog/content hub** — the main SEO gap
- ❌ **Domain authority 0** — no backlinks (Phase 3)
- ❌ **Only 2 pages indexed by Google** — needs GSC sitemap submission

### Fixes deployed (commit c18f6da, auto-deploying to Railway)
1. `trailingSlash: 'always'` in astro.config.mjs — fixes duplicate content
2. Meta descriptions expanded on 4 pages (all now 120-170 chars)
3. Visually-hidden H1 added to /evaluacion

---

## 3. Technical SEO — Current State

### What's working
- ✅ robots.txt properly configured (allows all, blocks /admin, /api, /panel, references sitemap)
- ✅ sitemap.xml exists with 9 URLs, priority/changefreq set
- ✅ Custom domain active (trustparatodos.com)
- ✅ Spanish-first content, clean URL structure
- ✅ HTTPS (site loaded over HTTPS — SSL resolved)
- ✅ SiteGuru audit running — site added, health score 87 (initial)

### What's broken / missing
- ❌ **8 of 9 pages have health_score 0 and no detectable title** — SiteGuru's crawler found page titles null on /que-es, /como-funciona, /preguntas-frecuentes, /evaluacion, /contacto, /testimonios, /asociaciones, /legal. Only the homepage (score 90) has a proper title. This is likely an SSR rendering issue — titles may be set client-side via JS instead of server-rendered in the HTML <head>.
- ❌ **Only 2 pages indexed by Google** — site:trustparatodos.com returns just homepage + /testimonios
- ❌ **No Google Search Console connected** — zero keyword/ranking data available (SiteGuru shows GSC not connected)
- ❌ **No Google Analytics 4 connected** — no traffic data
- ❌ **No structured data / Schema.org markup** — no FAQ schema, no Product schema, no Organization schema
- ❌ **No hreflang tags** — site has ES/EN toggle but no international SEO signals
- ❌ **Meta descriptions likely thin or missing** — need page-by-page audit (pending)
- ❌ **No backlinks** — domain authority is zero
- ❌ **Only 9 pages total** — not enough content surface for keyword coverage
- ❌ **No blog / content hub** — the main SEO gap (see §5)

### SSL verification needed
BRAND-STATUS (June 23) notes SSL cert was pending a TXT record at Hover (`railway-verify=6995b26524a60fd2a880cfea2eda7dbd319e4ee7640d9f419faa8cd09d96f01a`). The site loaded over HTTPS when I fetched it, so this may be resolved. Verify directly.

---

## 4. Competitive Landscape

### Direct competitors (Spanish-language trust services)

| Competitor | Type | Strength | Weakness |
|---|---|---|---|
| **michellecastillolaw.com** | CA estate planning attorney | Strong TikTok presence, bilingual, personal brand | Local only (CA), no online product, high price ($2-5k) |
| **abogado.com** | Legal directory (Internet Brands) | High domain authority, comprehensive content | No product — just information + attorney finder |
| **disabilitydenials.com** | Disability law firm | Has Spanish fideicomiso content | Not trust-focused, regional (Texas) |
| **TikTok creators** (various) | Social media influencers | Massive reach with "fideicomiso" / "living trust en español" content | No productized service, no website conversion |

### The gap TrustParaTodos fills
**No one offers a productized, national, Spanish-first, fully online trust creation service at $997.** The attorneys are local and expensive. The directories inform but don't sell. The TikTokers educate but don't fulfill. TrustParaTodos is the only end-to-end product.

### Keyword landscape (from search research)

**High-intent keywords (transactional):**
- "crear trust online en español"
- "fideicomiso en línea Estados Unidos"
- "living trust en español precio"
- "hacer trust sin abogado"
- "trust para mexicanos en USA"
- "cuánto cuesta un fideicomiso en Estados Unidos"

**Informational keywords (top-of-funnel):**
- "qué es un trust en español"
- "fideicomiso en Estados Unidos"
- "cómo evitar impuestos de herencia"
- "protección patrimonial hispanos"
- "probate en español qué es"
- "seguro de vida + trust hispanos"
- "trust revocable en español"

**Local/long-tail keywords:**
- "living trust en español California/Texas/Arizona/Florida"
- "fideicomiso para mexicanos en [estado]"
- "abogado de trust en español" (competes with attorneys — use as comparison content)

---

## 5. SEO Strategy — Three Phases

### Phase 1: Foundation (Week 1-2) — Make Google See You

**Goal:** Get the site properly indexed, connected to Google, and technically sound.

| Action | Priority | Who |
|---|---|---|
| Verify SSL cert is active (check Hover TXT record) | Critical | Jeff (DNS) |
| Add trustparatodos.com to Google Search Console | Critical | Kit (browser) |
| Add Google Analytics 4 | Critical | Kit (browser) |
| Submit sitemap.xml in GSC | Critical | Kit |
| Request indexing for all 9 pages in GSC | Critical | Kit |
| Add Organization Schema.org markup (name, URL, logo, contact, sameAs) | High | Kit (code) |
| Add FAQPage schema to /preguntas-frecuentes | High | Kit (code) |
| Add Product/Service schema to /evaluacion ($997 package) | High | Kit (code) |
| Add BreadcrumbList schema to all pages | Medium | Kit (code) |
| Audit and fix meta titles + descriptions on all 9 pages | High | Kit (code) |
| Add hreflang tags (es default, en alternate) | Medium | Kit (code) |
| Add OpenGraph tags to all pages | Medium | Kit (code) |

### Phase 2: Content Engine (Week 3-8) — Build Keyword Coverage

**Goal:** Go from 9 pages to 40+ pages targeting Spanish-language trust keywords.

**Blog/content hub structure** (`/blog/` or `/recursos/`):

**Cluster 1: "¿Qué es un trust?" (Educational foundation)**
1. Qué es un trust revocable en español (expanded version of /que-es)
2. Trust vs testamento: cuál es mejor para hispanos
3. Qué es el probate y cómo evitarlo
4. Fideicomiso revocable vs irrevocable: diferencias explicadas
5. Trust para no ciudadanos: funciona con visa I-10?

**Cluster 2: "Impuestos y protección patrimonial"**
6. Cómo evitar impuestos de herencia en Estados Unidos
7. Impuesto federal vs estatal de herencia: guía para hispanos
8. Cuánto pierde tu familia sin un trust (calculadora interactiva)
9. Protección patrimonial para mexicanos en USA: guía completa
10. Bienes que puedes incluir en un trust

**Cluster 3: "Cómo hacer un trust" (Transactional intent)**
11. Cómo crear un trust online en español: paso a paso
12. Cuánto cuesta un trust en Estados Unidos (comparativa 2026)
13. Necesito un abogado para hacer un trust? (positioning vs attorneys)
14. Notaría remota para trust: cómo funciona
15. Cómo obtener un EIN para tu trust: guía en español

**Cluster 4: "Seguro de vida + trust" (Cross-sell / Legacy Foundation)**
16. Por qué necesitas seguro de vida antes de un trust
17. Seguro de vida + trust: protección completa para hispanos
18. Cuánto seguro de vida necesitas con un trust

**Cluster 5: Local/State pages (long-tail capture)**
19. Trust en California para hispanos
20. Trust en Texas para hispanos
21. Trust en Arizona para hispanos
22. Trust en Florida para hispanos
23. Trust en Illinois para hispanos
24. Trust en Nueva York para hispanos

**Cluster 6: Comparativa/decision content**
25. Trust Para Todos vs abogado tradicional: comparativa honesta
26. Wealth.com vs Trust Para Todos: cuál te conviene
27. Trust DIY vs servicio completo: qué elegir
28. WingPoint vs Trust Para Todos: diferencias

**Content rules:**
- Ship at 80% (blog posts). Speed > perfection.
- 800-1500 words per article, Spanish-first.
- Internal link every article to /evaluacion (conversion page) and to /que-es (educational hub).
- Target one primary keyword + 2-3 secondary keywords per article.
- Include FAQ section at bottom of each (for FAQ schema + voice search).

### Phase 3: Authority Building (Month 2-6) — Earn Rankings

**Goal:** Build domain authority so content actually ranks.

| Tactic | Detail |
|---|---|
| **Google Business Profile** | Create GBP for TrustParaTodos (even if virtual service) — helps local pack and maps |
| **Spanish-language directories** | Submit to Hispanic business directories, abogado.com (if they accept listings), Hispanic Chamber of Commerce |
| **Partner backlinks** | Legacy Foundation Group → link to trustparatodos.com from their site. Reciprocal. |
| **Guest content on Hispanic media** | Pitch articles to Univision, Telemundo, Hispanic finance blogs |
| **TikTok/YouTube → SEO flywheel** | Create short-form videos answering the same questions the blog posts answer. Link in bio → trustparatodos.com. TikTok is where this audience already searches "fideicomiso" |
| **Reddit/Quora answers** | Answer questions in r/Hispanic, r/personalfinance (Spanish), Quora Spanish — link back to relevant blog posts |
| **Schema for reviews** | Add testimonios to /testimonios with Review schema — rich snippets in search results |
| **Press release** | Distribute a Spanish-language press release about the $997 online trust service for Hispanics |

---

## 6. Expected Timeline

| Timeframe | Milestone |
|---|---|
| Week 1-2 | GSC + GA4 connected, all pages indexed, schema added, meta tags fixed |
| Week 3-4 | First 10 blog articles published, sitemap updated |
| Week 5-8 | 20+ blog articles live, internal linking structure complete |
| Month 2 | GSC shows impressions for Spanish trust keywords |
| Month 3 | First organic clicks from "qué es un trust" / "fideicomiso en español" queries |
| Month 4-6 | Top 10 rankings for long-tail Spanish keywords, consistent organic traffic |
| Month 6+ | Top 3 rankings for primary keywords, 500+ monthly organic clicks |

---

## 7. What I Need From Jeff

1. **SiteGuru:** Log into app.siteguru.co and add `https://trustparatodos.com`. Once added, I'll run full audits via MCP. If there's a site limit, remove aeriusview.com to free a slot.

2. **DNS/SSL:** Verify the Hover TXT record for Railway SSL is set. The site loaded over HTTPS when I checked, but BRAND-STATUS says it was pending as of June 23.

3. **Google accounts:** I'll need you to log into Google in the browser so I can add the property to Search Console and GA4. I can drive the browser, but I need your Google session.

4. **Legacy Foundation Group:** Ask them to add a link to trustparatodos.com on their site (legacyfoundationgroup.net). This is the fastest backlink we can get.

5. **Approval to start Phase 1** technical work (schema, meta tags, GSC/GA4 setup) — this is all within my ownership lane and I can begin immediately.
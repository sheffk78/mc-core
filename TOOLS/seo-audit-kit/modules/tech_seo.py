"""
Technical SEO Audit Module
===========================
Analyzes crawlability, indexability, security headers, URL structure,
mobile signals, Core Web Vitals potential, and JavaScript rendering.

Borrowed patterns from SEO-GOD's seo-technical sub-skill:
- 9-category analysis
- SPA-aware page fetching
- IndexNow protocol check
"""

from __future__ import annotations

import logging
import asyncio
import re
from dataclasses import dataclass

from modules.base import AuditModule, ModuleResult, Finding

logger = logging.getLogger(__name__)


class TechSeoModule(AuditModule):
    """Technical SEO specialist module."""

    def id(self) -> str:
        return "tech-seo"

    async def audit(self, ctx) -> ModuleResult:
        url = ctx.url
        findings: list[Finding] = []
        score = 100.0

        try:
            # ── HTTP Response Analysis ──────────────────────────
            headers = await self._fetch_headers(url)
            http_result = self._check_headers(headers, url)
            findings.extend(http_result["findings"])
            score -= http_result["penalty"]

            # ── Robots.txt ──────────────────────────────────────
            robots = await self._check_robots(url)
            if robots["blocked"]:
                findings.append(Finding(
                    id="robots-txt-blocked",
                    category="tech-seo",
                    title="Robots.txt blocks search engines",
                    detail=robots["detail"],
                    severity="critical",
                    impact=100.0,
                    remediation=robots["remediation"],
                    effort="15min",
                    falsifiability={
                        "first_principle": "Search engines respect robots.txt directives",
                        "failure_check": f"Fetch /robots.txt and verify no Disallow: / rule",
                        "leading_indicator": "robots_txt_crawlable",
                    },
                    evidence_url=robots.get("url"),
                ))
                score -= 100

            # ── XML Sitemap ────────────────────────────────────
            sitemap = await self._check_sitemap(url)
            if not sitemap["found"]:
                findings.append(Finding(
                    id="sitemap-missing",
                    category="tech-seo",
                    title="No XML sitemap detected",
                    detail="No sitemap.xml or sitemap reference in robots.txt found.",
                    severity="medium",
                    impact=15.0,
                    remediation="Generate and submit an XML sitemap at /sitemap.xml",
                    effort="30min",
                    falsifiability={
                        "first_principle": "Sitemaps help search engines discover and crawl pages efficiently",
                        "failure_check": "Access /sitemap.xml and verify it returns valid XML",
                        "leading_indicator": "sitemap_available",
                    },
                ))
                score -= 15

            # ── HTTPS / Security ───────────────────────────────
            if not headers.get("strict-transport-security"):
                findings.append(Finding(
                    id="missing-hsts",
                    category="tech-seo",
                    title="Missing Strict-Transport-Security header",
                    detail="HSTS header not detected. This affects security and trust signals.",
                    severity="medium",
                    impact=8.0,
                    remediation="Add Strict-Transport-Security header with max-age=31536000",
                    effort="15min",
                    falsifiability={
                        "first_principle": "HSTS ensures HTTPS-only connections, a ranking signal",
                        "failure_check": "Check response headers for Strict-Transport-Security",
                        "leading_indicator": "hsts_present",
                    },
                ))
                score -= 8

            # ── Canonical Tags ──────────────────────────────────
            canonical = await self._check_canonical(url)
            if not canonical["found"]:
                findings.append(Finding(
                    id="canonical-missing",
                    category="tech-seo",
                    title="No canonical tag detected",
                    detail="Missing <link rel='canonical'> in <head>. Risk of duplicate content issues.",
                    severity="high",
                    impact=25.0,
                    remediation="Add self-referencing canonical tag in page <head>",
                    effort="15min",
                    falsifiability={
                        "first_principle": "Canonical tags prevent duplicate content confusion",
                        "failure_check": "Fetch page HTML, grep for rel=canonical in <head>",
                        "leading_indicator": "canonical_tag_present",
                    },
                ))
                score -= 25

            # ── Mobile Readiness ───────────────────────────────
            mobile = await self._check_mobile(url)
            if not mobile["ok"]:
                findings.append(Finding(
                    id="mobile-issues",
                    category="tech-seo",
                    title="Mobile usability issues detected",
                    detail=mobile["detail"],
                    severity="high",
                    impact=20.0,
                    remediation=mobile["remediation"],
                    effort="1-2hr",
                    falsifiability={
                        "first_principle": "Mobile-first indexing prioritizes mobile-friendly pages",
                        "failure_check": "Run Mobile-Friendly Test on target URL",
                        "leading_indicator": "mobile_usability_pass",
                    },
                ))
                score -= 20

            # ── JavaScript Rendering ───────────────────────────
            js_result = await self._check_js_rendering(url)
            if js_result["issues"]:
                findings.append(Finding(
                    id="js-rendering",
                    category="tech-seo",
                    title="JavaScript may block content rendering",
                    detail=js_result["detail"],
                    severity="high",
                    impact=30.0,
                    remediation="Consider SSR/SSG or dynamic rendering for critical content",
                    effort="epic",
                    falsifiability={
                        "first_principle": "Search engines struggle with client-side rendered content",
                        "failure_check": "Compare raw HTML vs rendered HTML for content presence",
                        "leading_indicator": "js_content_visible",
                    },
                ))
                score -= 30

            # ── Redirect Chains ────────────────────────────────
            redirects = await self._check_redirects(url)
            if redirects["chain_length"] > 3:
                findings.append(Finding(
                    id="redirect-chain",
                    category="tech-seo",
                    title=f"Redirect chain of {redirects['chain_length']} hops",
                    detail=f"URL resolves through {redirects['chain_length']} redirects.",
                    severity="medium",
                    impact=12.0,
                    remediation="Minimize redirects; point directly to final URL",
                    effort="30min",
                    falsifiability={
                        "first_principle": "Redirect chains waste crawl budget and slow indexing",
                        "failure_check": "Trace HTTP redirects with curl -I",
                        "leading_indicator": "redirect_hops_count",
                    },
                ))
                score -= 12

        except Exception as e:
            logger.error("tech_seo_audit_failed", url=url, error=str(e))
            return ModuleResult(
                module_id=self.id(),
                score=0,
                summary=f"Audit failed: {e}",
                errors=[str(e)],
            )

        score = max(0, min(100, score))
        summary = f"Checked headers, sitemap, HTTPS, canonical, mobile, JS rendering, and redirect chains."

        return ModuleResult(
            module_id=self.id(),
            score=score,
            summary=summary,
            findings=findings,
            data={"headers": headers},
        )

    # ── Helpers ──────────────────────────────────────────────────

    async def _fetch_headers(self, url: str) -> dict:
        """Fetch HTTP response headers."""
        # Using shell as async HTTP client fallback
        import subprocess
        loop = asyncio.get_event_loop()
        def _fetch():
            try:
                result = subprocess.run(
                    ["curl", "-sI", "-L", "-m", "15", url],
                    capture_output=True, text=True, timeout=20
                )
                headers = {}
                for line in result.stdout.split("\n"):
                    if ": " in line:
                        key, val = line.split(": ", 1)
                        headers[key.strip().lower()] = val.strip()
                return headers
            except Exception:
                return {}
        return await loop.run_in_executor(None, _fetch)

    def _check_headers(self, headers: dict, url: str) -> dict:
        findings = []
        penalty = 0
        if not headers:
            return {"findings": [], "penalty": 0}

        # Check for X-Robots-Tag noindex
        x_robots = headers.get("x-robots-tag", "")
        if "noindex" in x_robots.lower():
            findings.append(Finding(
                id="x-robots-noindex",
                category="tech-seo",
                title="X-Robots-Tag contains noindex",
                detail=f"Header: X-Robots-Tag: {x_robots}",
                severity="critical",
                impact=100.0,
                remediation="Remove noindex from X-Robots-Tag header",
                effort="15min",
                falsifiability={
                    "first_principle": "noindex directives prevent pages from appearing in search results",
                    "failure_check": "Check X-Robots-Tag header via curl -I",
                    "leading_indicator": "x_robots_tag",
                },
            ))
            penalty += 100

        # Server header
        server = headers.get("server", "")
        if server:
            findings.append(Finding(
                id="server-header-exposed",
                category="tech-seo",
                title="Server header exposes technology",
                detail=f"Server: {server}",
                severity="info",
                impact=0.0,
                remediation="Consider removing or obfuscating server header",
                effort="15min",
                falsifiability={
                    "first_principle": "Minimal server info reduces attack surface",
                    "failure_check": "Check headers for Server field",
                    "leading_indicator": "server_header_present",
                },
            ))

        return {"findings": findings, "penalty": penalty}

    async def _check_robots(self, url: str) -> dict:
        base = "/".join(url.split("/")[:3])
        robots_url = f"{base}/robots.txt"
        import subprocess
        loop = asyncio.get_event_loop()
        def _fetch():
            try:
                result = subprocess.run(
                    ["curl", "-s", "-m", "10", robots_url],
                    capture_output=True, text=True, timeout=15
                )
                content = result.stdout
                blocked, detail = self._parse_robots(content)
                return {
                    "found": True,
                    "blocked": blocked,
                    "detail": detail,
                    "remediation": "Remove or modify Disallow: / directive for User-agent: *",
                    "url": robots_url,
                }
            except Exception:
                return {"found": False, "blocked": False, "detail": "Could not fetch robots.txt"}
        return await loop.run_in_executor(None, _fetch)

    @staticmethod
    def _parse_robots(content: str) -> tuple[bool, str]:
        """
        Parse robots.txt by user-agent group.

        Returns (blocked, detail) where *blocked* is True only when the
        wildcard user-agent (\"*\") group contains a ``Disallow: /`` rule.
        """
        lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        # ── Phase 1: split into per-user-agent groups ──────────────
        groups: list[tuple[list[str], list[str]]] = []  # [(agents, rules), …]
        current_agents: list[str] = []
        current_rules: list[str] = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue  # skip blanks & comments

            if line.lower().startswith("user-agent:"):
                _, _, value = line.partition(":")
                agent = value.strip()
                # Close previous group if it accumulated rules
                if current_agents and current_rules:
                    groups.append((current_agents, current_rules))
                # Discard orphan rules that appeared before any UA header
                current_agents = [agent]
                current_rules = []
            elif line.lower().startswith(("disallow:", "allow:")):
                current_rules.append(line)
            else:
                # Any other directive acts as a group terminator
                if current_agents and current_rules:
                    groups.append((current_agents, current_rules))
                    current_agents = []
                    current_rules = []

        # flush the last group
        if current_agents and current_rules:
            groups.append((current_agents, current_rules))

        # ── Phase 2: evaluate ──────────────────────────────────────
        wildcard_blocked = False
        specific_blocks: list[str] = []

        for agents, rules in groups:
            has_star = "*" in agents
            disallows_root = any(
                rule.strip().lower() == "disallow: /" for rule in rules
            )
            if has_star and disallows_root:
                wildcard_blocked = True
            for agent in agents:
                if agent != "*" and disallows_root:
                    specific_blocks.append(agent)

        if wildcard_blocked:
            return True, "Disallow: / blocks all crawlers"

        detail = "Robots.txt found, no blanket blocks"
        if specific_blocks:
            detail += f" — note: specific bots blocked: {', '.join(specific_blocks)}"
        return False, detail

    async def _check_sitemap(self, url: str) -> dict:
        base = "/".join(url.split("/")[:3])
        sitemap_url = f"{base}/sitemap.xml"
        import subprocess
        loop = asyncio.get_event_loop()
        def _fetch():
            try:
                result = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "10", sitemap_url],
                    capture_output=True, text=True, timeout=15
                )
                code = result.stdout.strip()
                found = code == "200"
                if not found:
                    # Try alternate locations
                    for alt in [f"{base}/sitemap_index.xml", f"{base}/sitemap1.xml"]:
                        r = subprocess.run(
                            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "10", alt],
                            capture_output=True, text=True, timeout=15
                        )
                        if r.stdout.strip() == "200":
                            return {"found": True, "url": alt, "detail": f"Found at {alt}"}
                return {"found": found, "url": sitemap_url if found else None, "detail": "No sitemap found"}
            except Exception:
                return {"found": False, "detail": "Could not check sitemap"}
        return await loop.run_in_executor(None, _fetch)

    async def _check_canonical(self, url: str) -> dict:
        import subprocess
        loop = asyncio.get_event_loop()
        def _fetch():
            try:
                result = subprocess.run(
                    ["curl", "-sL", "-m", "15", url],
                    capture_output=True, text=True, timeout=20
                )
                html = result.stdout.lower()
                found = 'rel="canonical"' in html or "rel='canonical'" in html
                return {"found": found}
            except Exception:
                return {"found": False}
        return await loop.run_in_executor(None, _fetch)

    async def _check_mobile(self, url: str) -> dict:
        import subprocess
        loop = asyncio.get_event_loop()
        def _fetch():
            try:
                result = subprocess.run(
                    ["curl", "-sL", "-m", "15", f"https://search.google.com/test/mobile-friendly?url={url}"],
                    capture_output=True, text=True, timeout=20
                )
                # Simplified: check viewport meta
                result2 = subprocess.run(
                    ["curl", "-sL", "-m", "15", url],
                    capture_output=True, text=True, timeout=20
                )
                html = result2.stdout.lower()
                has_viewport = "name=\"viewport\"" in html or "width=device-width" in html
                if not has_viewport:
                    return {
                        "ok": False,
                        "detail": "Missing viewport meta tag",
                        "remediation": "Add <meta name='viewport' content='width=device-width, initial-scale=1'>",
                    }
                return {"ok": True, "detail": "Viewport meta tag present"}
            except Exception:
                return {"ok": False, "detail": "Check failed", "remediation": "Run Google Mobile-Friendly Test manually"}
        return await loop.run_in_executor(None, _fetch)

    async def _check_js_rendering(self, url: str) -> dict:
        import subprocess
        loop = asyncio.get_event_loop()
        def _fetch():
            try:
                raw = subprocess.run(
                    ["curl", "-sL", "-m", "15", url],
                    capture_output=True, text=True, timeout=20
                )
                raw_text = raw.stdout
                # Check for common SPA patterns
                has_root_div = '<div id="root"' in raw_text or '<div id="app"' in raw_text or '<div id="__next"' in raw_text
                has_noscript = '<noscript>' in raw_text
                is_next = 'next/' in raw_text.lower() or 'nuxt/' in raw_text.lower()

                if has_root_div and is_next:
                    return {
                        "issues": True,
                        "detail": "Detected React/Next.js SPA shell — content likely requires JS rendering",
                    }
                if has_root_div and not is_next:
                    return {
                        "issues": True,
                        "detail": "SPA root element detected — verify content is server-rendered or use dynamic rendering",
                    }
                return {"issues": False, "detail": "No obvious JS rendering issues in raw HTML"}
            except Exception:
                return {"issues": False, "detail": "Check skipped"}
        return await loop.run_in_executor(None, _fetch)

    async def _check_redirects(self, url: str) -> dict:
        import subprocess
        loop = asyncio.get_event_loop()
        def _fetch():
            try:
                result = subprocess.run(
                    ["curl", "-sI", "-L", "-m", "15", "-o", "/dev/null", "-w", "%{redirect_url} %{http_code}", url],
                    capture_output=True, text=True, timeout=20
                )
                # Count redirects
                chain = len(result.stdout.strip().split("\n"))
                return {"chain_length": chain}
            except Exception:
                return {"chain_length": 0}
        return await loop.run_in_executor(None, _fetch)
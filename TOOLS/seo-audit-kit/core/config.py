"""
Configuration: brand domains, credential tiers, business type detection.

Ported from SEO-GOD patterns:
- 4-tier progressive credential system (Tier 0 = no keys, Tier 3 = full API)
- Business type auto-detection for scoring weight adjustments
- Brand-to-domain registry for the Jeff Kohler portfolio
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ─── Brand Registry ───────────────────────────────────────────────

BRAND_DOMAINS = {
    "trustoffice": {
        "domain": "trustoffice.app",
        "aliases": ["trustoffice.app", "www.trustoffice.app"],
        "type": "saas",
        "tier_weights": {"technical": 0.25, "content": 0.25, "schema": 0.12, "performance": 0.10, "ai_readiness": 0.13, "images": 0.05, "on_page": 0.10},
    },
    "wingpoint": {
        "domain": "wingpointtrust.com",
        "aliases": ["wingpointtrust.com", "www.wingpointtrust.com"],
        "type": "education",
        "tier_weights": {"technical": 0.20, "content": 0.30, "schema": 0.12, "performance": 0.10, "ai_readiness": 0.13, "images": 0.05, "on_page": 0.10},
    },
    "agentictrust": {
        "domain": "agentictrust.app",
        "aliases": ["agentictrust.app", "www.agentictrust.app"],
        "type": "saas",
        "tier_weights": {"technical": 0.25, "content": 0.25, "schema": 0.12, "performance": 0.10, "ai_readiness": 0.13, "images": 0.05, "on_page": 0.10},
    },
    "truejoybirthing": {
        "domain": "truejoybirthing.com",
        "aliases": ["truejoybirthing.com", "www.truejoybirthing.com"],
        "type": "local_service",
        "tier_weights": {"technical": 0.20, "content": 0.25, "schema": 0.15, "performance": 0.10, "ai_readiness": 0.10, "images": 0.05, "on_page": 0.15},
    },
    "trustminutes": {
        "domain": "trustminutes.app",
        "aliases": ["trustminutes.app", "www.trustminutes.app"],
        "type": "saas",
        "tier_weights": {"technical": 0.25, "content": 0.25, "schema": 0.12, "performance": 0.10, "ai_readiness": 0.13, "images": 0.05, "on_page": 0.10},
    },
}


def resolve_brand(url_or_domain: str) -> dict | None:
    """Match a URL or domain to a known brand. Returns brand config or None."""
    clean = re.sub(r"^https?://", "", url_or_domain).strip().lower().rstrip("/")
    for brand_key, cfg in BRAND_DOMAINS.items():
        if clean == cfg["domain"] or clean in cfg["aliases"]:
            return {"brand": brand_key, **cfg}
    # Try partial match (domain contains brand domain)
    for brand_key, cfg in BRAND_DOMAINS.items():
        if cfg["domain"] in clean:
            return {"brand": brand_key, **cfg}
    return None


# ─── Progressive Credential Tiers ─────────────────────────────────
# Adapted from SEO-GOD's 4-tier system. Zero-config entry point.

@dataclass
class CredentialTier:
    tier: int
    name: str
    capabilities: list[str]
    requires_keys: bool
    description: str


TIER_0 = CredentialTier(
    tier=0,
    name="Zero-Config",
    capabilities=[
        "basic_crawl",
        "html_analysis",
        "structure_checks",
        "on_page_heuristics",
    ],
    requires_keys=False,
    description="No API keys needed. Crawls target URLs, analyzes HTML, runs structural checks.",
)

TIER_1 = CredentialTier(
    tier=1,
    name="PageSpeed + CrUX",
    capabilities=[
        "basic_crawl",
        "html_analysis",
        "structure_checks",
        "on_page_heuristics",
        "pagespeed_insights",
        "crux_field_data",
    ],
    requires_keys=True,
    description="Adds PageSpeed Insights and Chrome UX Report (lab + field CWV data).",
)

TIER_2 = CredentialTier(
    tier=2,
    name="Search Console",
    capabilities=[
        "basic_crawl",
        "html_analysis",
        "structure_checks",
        "on_page_heuristics",
        "pagespeed_insights",
        "crux_field_data",
        "search_console_data",
        "indexing_status",
        "sitemap_validation",
    ],
    requires_keys=True,
    description="Adds Google Search Console queries, URL inspection, sitemap status.",
)

TIER_3 = CredentialTier(
    tier=3,
    name="Full Intelligence",
    capabilities=[
        "basic_crawl",
        "html_analysis",
        "structure_checks",
        "on_page_heuristics",
        "pagespeed_insights",
        "crux_field_data",
        "search_console_data",
        "indexing_status",
        "sitemap_validation",
        "ga4_traffic",
        "keyword_planner",
    ],
    requires_keys=True,
    description="Full stack: GSC + GA4 + Keyword Planner. Complete data picture.",
)

TIERS = [TIER_0, TIER_1, TIER_2, TIER_3]


# ─── Business Type Detection ──────────────────────────────────────

BUSINESS_TYPE_SIGNALS = {
    "saas": ["/pricing", "/login", "/signup", "/dashboard", "/api"],
    "local_service": ["/location", "/contact", "/directions", "/appointment", "/booking"],
    "education": ["/course", "/lesson", "/curriculum", "/enroll", "/class"],
    "ecommerce": ["/product", "/cart", "/checkout", "/shop", "/store"],
    "publisher": ["/blog", "/news", "/article", "/category", "/archive"],
}


def detect_business_type(url: str, html: str = "") -> str:
    """
    Detect business type from URL structure and HTML content.
    Returns one of: saas, local_service, education, ecommerce, publisher, or generic.
    """
    url_lower = url.lower()
    # Check URL path signals
    for biz_type, path_signals in BUSINESS_TYPE_SIGNALS.items():
        matches = sum(1 for sig in path_signals if sig in url_lower)
        if matches >= 2:
            return biz_type

    # Check HTML meta signals (simplified)
    html_lower = html.lower()
    if "woocommerce" in html_lower or "shopify" in html_lower or 'productschema' in html_lower:
        return "ecommerce"
    if "lms" in html_lower or "course" in html_lower or "lesson" in html_lower:
        return "education"
    if "pricing" in html_lower and "login" in html_lower:
        return "saas"

    return "generic"


def get_scoring_weights(business_type: str) -> dict[str, float]:
    """Get scoring weight overrides for a business type."""
    defaults = {"technical": 0.22, "content": 0.23, "schema": 0.10,
                "performance": 0.10, "ai_readiness": 0.10, "images": 0.05, "on_page": 0.20}

    adjustments = {
        "local_service": {"schema": 0.15, "content": 0.20, "on_page": 0.15},
        "ecommerce": {"schema": 0.15, "content": 0.20, "images": 0.08},
        "education": {"content": 0.30, "ai_readiness": 0.13},
        "publisher": {"content": 0.30, "ai_readiness": 0.15},
    }

    weights = dict(defaults)
    if business_type in adjustments:
        weights.update(adjustments[business_type])

    # Normalize to 1.0
    total = sum(weights.values())
    return {k: round(v / total, 4) for k, v in weights.items()}
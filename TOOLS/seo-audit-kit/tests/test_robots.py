"""Unit tests for _check_robots in tech_seo.py"""

import re
import unittest


def parse_robots_check(content: str) -> dict:
    """
    Replicate the fixed _check_robots parsing logic so we can unit-test
    without making real HTTP calls.  Returns the same dict shape as
    _check_robots.
    """
    # Normalise line endings so splitting is consistent
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # -- Phase 1: split into per-user-agent groups --
    # A group starts with one or more "User-agent:" lines and is followed
    # by rule lines (Allow / Disallow / Sitemap / …) until the next group
    # or EOF.
    groups: list[tuple[list[str], list[str]]] = []  # [(agents, rules), …]
    current_agents: list[str] = []
    current_rules: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue  # skip blanks & comments

        # Detect a User-agent header (may appear multiple times for one group)
        if line.lower().startswith("user-agent:"):
            _, _, value = line.partition(":")
            agent = value.strip()
            # Close previous group if it accumulated rules
            if current_agents and current_rules:
                groups.append((current_agents, current_rules))
            # Discard orphan rules that appeared before any UA header
            current_agents = [agent]
            current_rules = []
        elif line.lower().startswith("disallow:") or line.lower().startswith("allow:"):
            current_rules.append(line)
        # Other directives (Sitemap, Crawl-delay, etc.) are ignored for this
        # check but still act as group terminators.
        else:
            if current_agents and current_rules:
                groups.append((current_agents, current_rules))
                current_agents = []
                current_rules = []

    # flush the last group
    if current_agents and current_rules:
        groups.append((current_agents, current_rules))

    # -- Phase 2: evaluate --
    wildcard_blocked = False
    specific_blocks: list[str] = []

    for agents, rules in groups:
        has_star = "*" in agents
        disallows_root = any(
            rule.strip().lower() == "disallow: /" for rule in rules
        )
        if has_star and disallows_root:
            wildcard_blocked = True
        # Collect info about non-wildcard blocks
        for agent in agents:
            if agent != "*" and disallows_root:
                specific_blocks.append(agent)

    blocked = wildcard_blocked
    detail = (
        "Disallow: / blocks all crawlers"
        if blocked
        else "Robots.txt found, no blanket blocks"
    )
    # If there are specific bot blocks, mention them (informational)
    if specific_blocks:
        detail += (
            f" — note: specific bots blocked: {', '.join(specific_blocks)}"
        )

    return {
        "found": True,
        "blocked": blocked,
        "detail": detail,
        "remediation": (
            "Remove or modify Disallow: / directive for User-agent: *"
        ),
        "url": "https://example.com/robots.txt",
    }


class TestRobotsParsing(unittest.TestCase):
    """Test the parse_robots_check helper (mirrors _check_robots logic)."""

    # ── 1. Blanket block detected ──────────────────────────────────
    def test_blanket_block(self):
        content = (
            "User-agent: *\n"
            "Disallow: /\n"
        )
        result = parse_robots_check(content)
        self.assertTrue(result["found"])
        self.assertTrue(result["blocked"])
        self.assertIn("blocks all crawlers", result["detail"])

    def test_blanket_block_whitespace(self):
        content = (
            "User-agent: *\n"
            "Disallow: /\n"
            "Allow: /admin\n"
        )
        result = parse_robots_check(content)
        self.assertTrue(result["blocked"])

    def test_blanket_block_reversed_order(self):
        """Rules before the first User-agent line are ignored."""
        content = (
            "Disallow: /\n"
            "User-agent: *\n"
        )
        # Disallow without a preceding UA is discarded. UA has no rules.
        result = parse_robots_check(content)
        self.assertFalse(result["blocked"])

    # ── 2. Scoped blocks NOT flagged as blanket ─────────────────────
    def test_scoped_block_not_blanket(self):
        """trustminutes.app scenario: wildcard allows, GPTBot disallows."""
        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "\n"
            "User-agent: GPTBot\n"
            "Disallow: /\n"
        )
        result = parse_robots_check(content)
        self.assertTrue(result["found"])
        self.assertFalse(result["blocked"])
        self.assertIn("no blanket blocks", result["detail"])
        self.assertIn("GPTBot", result["detail"])

    def test_multiple_scoped_blocks(self):
        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "\n"
            "User-agent: GPTBot\n"
            "Disallow: /\n"
            "\n"
            "User-agent: CCBot\n"
            "Disallow: /\n"
        )
        result = parse_robots_check(content)
        self.assertFalse(result["blocked"])
        self.assertIn("GPTBot", result["detail"])
        self.assertIn("CCBot", result["detail"])

    def test_wildcard_allows_specific_disallows(self):
        content = (
            "User-agent: *\n"
            "Disallow:\n"   # empty = allow all
            "\n"
            "User-agent: Bingbot\n"
            "Disallow: /private\n"
        )
        result = parse_robots_check(content)
        self.assertFalse(result["blocked"])

    def test_no_robots_txt(self):
        """When content is empty we still get a safe default."""
        # Our helper always returns found=True; the real _check_robots
        # returns found=False on fetch error.  This just tests the parser.
        result = parse_robots_check("")
        self.assertFalse(result["blocked"])

    def test_only_specific_bot_blocked(self):
        content = (
            "User-agent: GPTBot\n"
            "Disallow: /\n"
        )
        result = parse_robots_check(content)
        self.assertFalse(result["blocked"])
        self.assertIn("GPTBot", result["detail"])

    def test_wildcard_with_multiple_rules(self):
        """Wildcard group has Disallow: / among other rules → blocked."""
        content = (
            "User-agent: *\n"
            "Allow: /public\n"
            "Disallow: /\n"
        )
        result = parse_robots_check(content)
        self.assertTrue(result["blocked"])


if __name__ == "__main__":
    unittest.main()
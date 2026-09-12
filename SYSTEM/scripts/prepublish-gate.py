#!/usr/bin/env python3
"""
Pre-publish gate — scan files/dirs for sensitive-data leaks before anything goes public.

LoopX-inspired `loopx check` equivalent. Catches the leak classes that burn us:
API keys, credentials, emails, phone numbers, private paths, tokens, and internal
brand/project names in content destined for public surfaces (README, docs, email,
social, prospect deliverables, subagent outputs).

Usage:
    python prepublish-gate.py <path> [<path> ...]
    python prepublish-gate.py --scan-path README.md --scan-path docs/ examples/
    python prepublish-gate.py --json <path>          # machine-readable findings

Options:
    --json            Emit findings as JSON (one object) instead of human text.
    --scan-path X     Explicit scan target. Repeatable; also accepts bare paths.

Exit codes:
    0 - No findings (safe to publish)
    1 - Findings present (block publishing until reviewed)
    2 - Usage / runtime error

Scope note: this is a best-effort heuristic gate, not proof of safety. It raises
potential leaks for human/Kit review; a clean scan does not guarantee a document
is safe. It complements (does not replace) manual review of public content.
"""

import json
import os
import re
import sys

# ── Leak patterns ──────────────────────────────────────────────────────────
# Each is (name, compiled regex). Names classify the finding.

PATTERNS = [
    # Credentials / secrets
    ("AWS key", re.compile(r"(?i)\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"(?i)\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("Slack token", re.compile(r"(?i)\bxox[baprs]-[0-9A-Za-z-]{20,}\b")),
    ("Google API key", re.compile(r"(?i)\bAIza[0-9A-Za-z_-]{20,}\b")),
    ("Stripe key", re.compile(r"(?i)\b(sk|pk)_(live|test)_[0-9A-Za-z]{16,}\b")),
    ("Private key block", re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("Password assignment", re.compile(r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|token)\s*[=:]\s*['\"][^'\"]{6,}['\"]")),
    ("Bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{16,}\b")),
    ("Basic auth URL", re.compile(r"\b[a-zA-Z0-9._%+-]+:[^@\s/]+@[a-zA-Z0-9.-]+")),

    # PII
    # Email: capture the TLD; reserved test/doc TLDs (.test, .example, .invalid,
    # .localhost) are filtered in code to avoid false positives on fixtures/docs.
    ("Email address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.([A-Za-z]{2,})\b")),
    ("US phone", re.compile(r"\b(?:\+?1[-.\s]?)?\(?[2-9][0-9]{2}\)?[-.\s][2-9][0-9]{2}[-.\s][0-9]{4}\b")),
    ("SSN", re.compile(r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b")),
    ("IP address", re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")),

    # Internal paths / infra
    ("Home path", re.compile(r"(?i)\b/Users/[A-Za-z0-9_.-]+/")),
    ("Absolute workspace path", re.compile(r"(?i)\b/\.openclaw/workspace/")),
    ("Absolute hermes path", re.compile(r"(?i)\b/\.hermes/")),
    ("Railway URL", re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")),
    ("Internal domain", re.compile(r"(?i)\b[\w-]+\.(proxy\.rlwy\.net|railway\.app|herokuapp\.com|netlify\.app|vercel\.app|pages\.dev)\b")),
    ("Localhost port", re.compile(r"(?i)\b(?:localhost|127\.0\.0\.1):[0-9]{2,5}\b")),
]

# File extensions that are almost never meant for public copy and would be false-positive
# factories if scanned (binary, lockfiles, package metadata, vendored deps, secrets refs).
SKIP_EXT = {
    ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".zip", ".gz", ".lock",
    ".min.js", ".min.css", ".map",
}
SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", ".hermes", "site-packages",
    "dist", "build", "coverage", ".next", ".cache", "archive",
}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    ".env.example", ".gitignore", "LICENSE", "SECURITY.md", "AGENTS.md",
}

# Reserved test/doc TLDs — email addresses on these are fixtures/examples, not real PII.
RESERVED_TLDS = {"test", "example", "invalid", "localhost"}

# ── Core scan ───────────────────────────────────────────────────────────────

def _iter_files(root):
    """Yield text file paths under root (or the file itself if root is a file)."""
    if os.path.isfile(root):
        if os.path.basename(root) in SKIP_FILES or os.path.splitext(root)[1].lower() in SKIP_EXT:
            return
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name in SKIP_FILES or os.path.splitext(name)[1].lower() in SKIP_EXT:
                continue
            yield os.path.join(dirpath, name)


def scan_path(root):
    """Scan root for leaks. Return list of finding dicts."""
    findings = []
    for path in _iter_files(root):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            continue
        for line_no, line in enumerate(content.splitlines(), 1):
            for name, pattern in PATTERNS:
                m = pattern.search(line)
                if not m:
                    continue
                # Filter reserved-TLD emails (fixtures/examples, not real PII).
                if name == "Email address" and m.lastindex and m.group(1).lower() in RESERVED_TLDS:
                    continue
                snippet = line.strip()
                if len(snippet) > 160:
                    snippet = snippet[:157] + "..."
                findings.append({
                    "path": path,
                    "line": line_no,
                    "type": name,
                    "match": m.group(0)[:64],
                    "snippet": snippet,
                })
    return findings


# ── Output ──────────────────────────────────────────────────────────────────

def print_findings(findings, as_json=False):
    if as_json:
        print(json.dumps({"findings": findings}, indent=2))
        return
    if not findings:
        print("PASS: no leaks detected")
        return
    print(f"FAIL: {len(findings)} potential leak(s) — review before publishing:\n")
    # Group by file for readability
    by_path = {}
    for f in findings:
        by_path.setdefault(f["path"], []).append(f)
    for path, items in sorted(by_path.items()):
        print(f"  {path}")
        for f in items:
            print(f"    L{f['line']:>5} [{f['type']}] {f['snippet']}")
    print()


def main():
    args = [a for a in sys.argv[1:] if a]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]

    # Collect targets: bare args + everything after --scan-path
    targets = []
    i = 0
    while i < len(args):
        if args[i] == "--scan-path" and i + 1 < len(args):
            targets.append(args[i + 1])
            i += 2
        else:
            targets.append(args[i])
            i += 1

    # Dedupe, keep order
    seen = set()
    unique_targets = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            unique_targets.append(t)

    if not unique_targets:
        print("ERROR: no scan target given.\n", file=sys.stderr)
        print("Usage: python prepublish-gate.py <path> [<path> ...]", file=sys.stderr)
        print("       python prepublish-gate.py --scan-path <path> ...", file=sys.stderr)
        sys.exit(2)

    all_findings = []
    missing = []
    for t in unique_targets:
        if not os.path.exists(t):
            missing.append(t)
            continue
        all_findings.extend(scan_path(t))

    if missing:
        print(f"ERROR: scan target(s) not found: {missing}", file=sys.stderr)
        sys.exit(2)

    print_findings(all_findings, as_json=as_json)
    sys.exit(0 if not all_findings else 1)


if __name__ == "__main__":
    main()

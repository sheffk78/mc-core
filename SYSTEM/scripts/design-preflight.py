#!/usr/bin/env python3
"""
Preflight enforcement script for web builds.
Checks that all required design skills are loaded in the current Hermes session
for the specified brand before proceeding with a build.

Usage:
    python design-preflight.py <brand>
    python design-preflight.py --check-only <brand>

Brands: trustoffice, tjb, agentictrust, generic

Exit codes:
    0 - All required skills loaded
    1 - Missing required skills
"""

import sys
import subprocess
import json
import os

# ââ Required skills ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

BASE_SKILLS = [
    "design-system",
    "frontend-design",
    "impeccable",
    "visual-verification",
    "humanizer",
]

BRAND_ADDITIONS = {
    "trustoffice": ["trustoffice-design"],
    "tjb": ["tjb-design"],
    "agentictrust": ["agentictrust-design"],
    "generic": [],
}

VALID_BRANDS = set(BRAND_ADDITIONS.keys())


# ââ Helpers ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def get_loaded_skills() -> set[str]:
    """Return the set of skill names loaded in the current Hermes session."""
    try:
        result = subprocess.run(
            ["hermes", "skills", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            # Fallback: try without --json
            result = subprocess.run(
                ["hermes", "skills", "list"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                print(f"WARNING: Could not fetch skill list ('hermes skills list' failed): {result.stderr.strip()}", file=sys.stderr)
                return set()
            # Parse line-based output: "  skill-name - description"
            skills = set()
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line and " - " in line:
                    name = line.split(" - ")[0].strip()
                    if name:
                        skills.add(name)
            return skills

        # Parse JSON output
        data = json.loads(result.stdout)
        if isinstance(data, list):
            skills = set()
            for item in data:
                if isinstance(item, dict) and "name" in item:
                    skills.add(item["name"])
                elif isinstance(item, str):
                    skills.add(item)
            return skills
        elif isinstance(data, dict):
            skills = set()
            for key, val in data.items():
                if key == "skills" and isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "name" in item:
                            skills.add(item["name"])
                        elif isinstance(item, str):
                            skills.add(item)
                elif isinstance(val, str) and key == "name":
                    skills.add(val)
                elif isinstance(val, str):
                    skills.add(val)
                elif isinstance(key, str):
                    skills.add(key)
            return skills
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"WARNING: Could not read Hermes skill list: {e}", file=sys.stderr)
        return set()

    return set()


def print_usage():
    print("Usage:", file=sys.stderr)
    print(f"  {sys.argv[0]} <brand>", file=sys.stderr)
    print(f"  {sys.argv[0]} --check-only <brand>", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Brands: {', '.join(sorted(VALID_BRANDS))}", file=sys.stderr)
    print(file=sys.stderr)
    print("Exit codes:", file=sys.stderr)
    print("  0 - All required skills loaded", file=sys.stderr)
    print("  1 - Missing required skills", file=sys.stderr)


# ââ Main âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def main():
    check_only = False
    brand = None

    args = [a for a in sys.argv[1:] if a]
    if not args:
        print("ERROR: No brand specified.", file=sys.stderr)
        print_usage()
        sys.exit(1)

    if args[0] == "--check-only":
        check_only = True
        if len(args) < 2:
            print("ERROR: --check-only requires a brand argument.", file=sys.stderr)
            print_usage()
            sys.exit(1)
        brand = args[1].lower()
    else:
        brand = args[0].lower()

    if brand not in VALID_BRANDS:
        print(
            f"ERROR: Unknown brand '{brand}'. Valid brands: {', '.join(sorted(VALID_BRANDS))}",
            file=sys.stderr,
        )
        print_usage()
        sys.exit(1)

    required = BASE_SKILLS + BRAND_ADDITIONS.get(brand, [])

    if check_only:
        print(f"Required skills for brand '{brand}':")
        for skill in required:
            print(f"  - {skill}")
        print(f"\nTotal: {len(required)} skill(s)")
        sys.exit(0)

    # Actual check
    loaded = get_loaded_skills()
    missing = [s for s in required if s not in loaded]

    if not missing:
        print("PASS: All required skills loaded")
        sys.exit(0)
    else:
        print(f"FAIL: Missing skills: {missing}. Load them before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Toolset auto-router. Reads ACTIVE-TASK.md and adjusts enabled toolsets + MCP servers
based on what the current task actually needs. Run between sessions (via cron or manually)
so the next session starts with the right tools enabled.

Usage:
    python3 ~/.openclaw/workspace/scripts/toolset-router.py          # auto-route
    python3 ~/.openclaw/workspace/scripts/toolset-router.py --status  # show current state
    python3 ~/.openclaw/workspace/scripts/toolset-router.py --reset   # back to defaults
"""

import os
import re
import sys
import subprocess
import yaml

HERMES_CONFIG = os.path.expanduser("~/.hermes/config.yaml")
ACTIVE_TASK = os.path.expanduser("~/.openclaw/workspace/SYSTEM/ACTIVE-TASK.md")

# Toolsets that stay enabled always (core operating set)
ALWAYS_ENABLED = {
    "web", "browser", "terminal", "file", "code_execution",
    "vision", "skills", "todo", "memory", "session_search",
    "delegation", "cronjob",
}

# On-demand toolsets: keyword → toolset mapping
# If any keyword appears in ACTIVE-TASK.md, the toolset gets enabled
TASK_KEYWORDS = {
    "image_gen": ["blog image", "hero image", "og image", "generate image", "image gen", "coverr", "thumbnail"],
    "tts": ["voice message", "text to speech", "text-to-speech", "tts", "audio response", "voice memo"],
    "video": ["video analysis", "video production", "video pipeline", "tjb video", "talking head", "veo"],
    "computer_use": ["desktop app", "1password", "lightpdf", "computer_use", "cua-driver", "desktop automation"],
    "clarify": [],  # rarely needed — Jeff prefers autonomous action
}

# MCP servers: keyword → server mapping
MCP_KEYWORDS = {
    "refero": ["design reference", "refero", "ui design", "design pattern"],
    "siteguru": ["seo audit", "siteguru", "seo monitoring", "seo check"],
    "maestro": ["mobile test", "maestro", "app test", "ios simulator", "android emulator", "e2e test", "mobile app test"],
}

# MCP servers that stay enabled always
MCP_ALWAYS_ENABLED = {"adspirer", "facebook_ads", "skill-registry", "zapier"}


def read_active_task():
    """Read ACTIVE-TASK.md and return lowercase content."""
    try:
        with open(ACTIVE_TASK) as f:
            return f.read().lower()
    except FileNotFoundError:
        return ""


def get_current_toolsets():
    """Get currently enabled toolsets from hermes tools list."""
    result = subprocess.run(
        ["hermes", "tools", "list"],
        capture_output=True, text=True, timeout=10
    )
    enabled = set()
    disabled = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if "✓ enabled" in line:
            # Extract toolset name (second column after the checkmark)
            parts = line.split()
            for p in parts:
                if p not in ("✓", "enabled") and not p.startswith("🔍") and not p.startswith("🌐") \
                   and not p.startswith("💻") and not p.startswith("📁") and not p.startswith("⚡") \
                   and not p.startswith("👁") and not p.startswith("📚") and not p.startswith("📋") \
                   and not p.startswith("💾") and not p.startswith("🔎") and not p.startswith("👥") \
                   and not p.startswith("⏰") and not p.startswith("🎨") and not p.startswith("🎬") \
                   and not p.startswith("🔊") and not p.startswith("❓") and not p.startswith("🖱") \
                   and not p.startswith("🧩") and not p.startswith("🏠") and not p.startswith("🎵") \
                   and not p.startswith("🤖") and not p.startswith("🐦"):
                    if len(p) > 1 and not p.startswith("—"):
                        enabled.add(p)
                        break
        elif "✗ disabled" in line:
            parts = line.split()
            for p in parts:
                if p not in ("✗", "disabled") and not p.startswith("🔍") and not p.startswith("🌐") \
                   and not p.startswith("💻") and not p.startswith("📁") and not p.startswith("⚡") \
                   and not p.startswith("👁") and not p.startswith("📚") and not p.startswith("📋") \
                   and not p.startswith("💾") and not p.startswith("🔎") and not p.startswith("👥") \
                   and not p.startswith("⏰") and not p.startswith("🎨") and not p.startswith("🎬") \
                   and not p.startswith("🔊") and not p.startswith("❓") and not p.startswith("🖱") \
                   and not p.startswith("🧩") and not p.startswith("🏠") and not p.startswith("🎵") \
                   and not p.startswith("🤖") and not p.startswith("🐦"):
                    if len(p) > 1 and not p.startswith("—"):
                        disabled.add(p)
                        break
    return enabled, disabled


def set_toolset(name, enable=True):
    """Enable or disable a toolset via hermes CLI."""
    action = "enable" if enable else "disable"
    try:
        subprocess.run(
            ["hermes", "tools", action, name],
            capture_output=True, text=True, timeout=10
        )
        return True
    except Exception:
        return False


def set_mcp_server(name, enable=True):
    """Enable or disable an MCP server in config.yaml."""
    try:
        with open(HERMES_CONFIG) as f:
            config = yaml.safe_load(f)
        if name in config.get("mcp_servers", {}):
            config["mcp_servers"][name]["enabled"] = enable
            with open(HERMES_CONFIG, "w") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"  ⚠️ Failed to set MCP {name}: {e}")
        return False


def route():
    """Main routing logic — read ACTIVE-TASK.md, adjust toolsets."""
    task_text = read_active_task()
    if not task_text:
        print("⚠️ No ACTIVE-TASK.md found — keeping defaults")
        return

    enabled, disabled = get_current_toolsets()
    changes = []

    # Check each on-demand toolset
    for toolset, keywords in TASK_KEYWORDS.items():
        should_enable = any(kw in task_text for kw in keywords)
        if should_enable and toolset in disabled:
            set_toolset(toolset, enable=True)
            changes.append(f"  + enabled {toolset} (keyword match in active task)")
        elif not should_enable and toolset in enabled and toolset not in ALWAYS_ENABLED:
            set_toolset(toolset, enable=False)
            changes.append(f"  - disabled {toolset} (no keyword match — not needed)")

    # Check MCP servers
    for server, keywords in MCP_KEYWORDS.items():
        should_enable = any(kw in task_text for kw in keywords) if keywords else False
        if should_enable:
            set_mcp_server(server, enable=True)
            changes.append(f"  + enabled MCP {server} (keyword match)")
        elif server not in MCP_ALWAYS_ENABLED:
            set_mcp_server(server, enable=False)
            if changes:  # only log if we're making other changes
                pass  # already disabled, no need to log

    if changes:
        print(f"Toolset router — {len(changes)} changes:")
        for c in changes:
            print(c)
        print("\nChanges take effect on next /reset (new session).")
    else:
        print("Toolset router — no changes needed. Current toolsets match active task.")


def show_status():
    """Show current toolset state."""
    enabled, disabled = get_current_toolsets()
    print("=== Currently Enabled ===")
    for t in sorted(enabled):
        print(f"  ✓ {t}")
    print(f"\n=== Currently Disabled ===")
    for t in sorted(disabled):
        print(f"  ✗ {t}")


def reset_to_defaults():
    """Reset to default enabled set — disable all on-demand toolsets."""
    on_demand = set(TASK_KEYWORDS.keys())
    for toolset in on_demand:
        set_toolset(toolset, enable=False)
    for server in MCP_KEYWORDS:
        set_mcp_server(server, enable=False)
    print("Reset to defaults — only core toolsets enabled.")
    print("Changes take effect on next /reset (new session).")


if __name__ == "__main__":
    if "--status" in sys.argv:
        show_status()
    elif "--reset" in sys.argv:
        reset_to_defaults()
    else:
        route()
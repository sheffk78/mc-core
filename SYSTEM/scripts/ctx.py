#!/usr/bin/env python3
"""
ctx.py — Context window usage meter for Discord sessions.

Reads last_prompt_tokens from the gateway_routing table in state.db,
computes percentage against the model's context_length, and returns a
compact one-line indicator.

Usage:
    python3 ctx.py                    # auto-detect channel from env
    python3 ctx.py --channel 123456   # explicit channel ID
    python3 ctx.py --json             # JSON output

Threshold: only prints when context usage >= 20% (configurable via --threshold).
"""
import argparse
import json
import os
import sqlite3
import sys


def get_context_length():
    """Get the context_length for the configured default model."""
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    context_length = 131072  # safe default for GLM-5.2

    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check model_aliases for default model
        aliases = config.get("model_aliases", {})
        default_alias = aliases.get("default", {})
        if isinstance(default_alias, dict):
            model_name = default_alias.get("model", "")
            # Check if this alias has context_length
            cl = default_alias.get("context_length")
            if cl and isinstance(cl, int) and cl > 0:
                return cl

            # Check if there's a model-specific alias with context_length
            for alias_name, alias_cfg in aliases.items():
                if isinstance(alias_cfg, dict):
                    am = alias_cfg.get("model", "")
                    if am == model_name and alias_cfg.get("context_length"):
                        return alias_cfg["context_length"]

        # Check top-level model config
        model_cfg = config.get("model", {})
        if isinstance(model_cfg, dict):
            cl = model_cfg.get("context_length")
            if cl and isinstance(cl, int) and cl > 0:
                return cl
    except Exception:
        pass

    return context_length


def get_context_usage(channel_id=None, session_id=None):
    """
    Query last_prompt_tokens from gateway_routing table.
    Returns (last_prompt_tokens, context_length) or (0, 0) if not found.
    """
    db_path = os.path.expanduser("~/.hermes/state.db")
    if not os.path.exists(db_path):
        return 0, 0

    context_length = get_context_length()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if session_id:
            # Look up by session_id in the sessions table for input_tokens
            cursor.execute(
                "SELECT input_tokens, output_tokens FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            if row:
                # input_tokens accumulates all prompt tokens sent to the API
                # last_prompt_tokens from gateway_routing is more accurate for context window fill
                pass

        # Query gateway_routing for last_prompt_tokens
        if channel_id:
            cursor.execute(
                """SELECT entry_json FROM gateway_routing
                   WHERE session_key LIKE ? ORDER BY updated_at DESC LIMIT 1""",
                (f"%{channel_id}%",),
            )
        else:
            # Get the most recently updated session
            cursor.execute(
                """SELECT entry_json FROM gateway_routing
                   ORDER BY updated_at DESC LIMIT 1"""
            )

        row = cursor.fetchone()
        if row:
            entry = json.loads(row[0])
            lpt = entry.get("last_prompt_tokens", 0) or 0
            return lpt, context_length

        # Fallback: try sessions table for the most recent discord session
        cursor.execute(
            """SELECT input_tokens FROM sessions
               WHERE source = 'discord'
               ORDER BY started_at DESC LIMIT 1"""
        )
        row = cursor.fetchone()
        if row:
            return row[0] or 0, context_length

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        conn.close()

    return 0, 0


def format_context_meter(used, total, threshold=20):
    """
    Format the context meter string.
    Returns empty string if below threshold.
    """
    if total <= 0:
        return ""

    pct = min(100, round((used / total) * 100))

    if pct < threshold:
        return ""

    # Compact format: ctx: 27%
    return f"ctx: {pct}%"


def main():
    parser = argparse.ArgumentParser(description="Context window usage meter")
    parser.add_argument("--channel", type=str, help="Discord channel ID")
    parser.add_argument("--session-id", type=str, help="Hermes session ID")
    parser.add_argument("--threshold", type=int, default=20, help="Minimum percentage to display (default: 20)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    # Auto-detect channel from environment if not provided
    channel = args.channel
    if not channel:
        channel = os.environ.get("DISCORD_CHANNEL_ID", "")

    used, total = get_context_usage(channel_id=channel, session_id=args.session_id)

    if total <= 0:
        if args.json:
            print(json.dumps({"used": 0, "total": 0, "percent": 0, "display": False}))
        else:
            print("")
        return

    pct = min(100, round((used / total) * 100))
    meter = format_context_meter(used, total, args.threshold)

    if args.json:
        print(json.dumps({
            "used": used,
            "total": total,
            "percent": pct,
            "display": pct >= args.threshold,
            "meter": meter,
        }))
    else:
        if meter:
            print(meter)
        else:
            print("")  # Below threshold — print nothing


if __name__ == "__main__":
    main()
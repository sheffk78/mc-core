#!/usr/bin/env python3
"""codex-test-parser.py — Parse Codex JSONL session output into structured findings.

Usage:
    python3 codex-test-parser.py <session.jsonl> [--report <report.md>]

Reads the JSONL output from `codex exec --json` and extracts:
- All agent messages (findings, observations)
- All tool calls (browser actions, shell commands)
- Screenshots taken (file paths)
- Errors encountered
- Token usage

Outputs a clean JSON summary and optionally merges with the markdown report.
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime


def parse_jsonl(filepath: str) -> dict:
    """Parse a Codex JSONL session file into structured data."""
    events = []
    agent_messages = []
    tool_calls = []
    screenshots = []
    errors = []
    usage = {}
    thread_id = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            events.append(event)
            etype = event.get("type", "")
            
            if etype == "thread.started":
                thread_id = event.get("thread_id")
            
            elif etype == "item.completed":
                item = event.get("item", {})
                item_type = item.get("type", "")
                
                if item_type == "agent_message":
                    agent_messages.append({
                        "id": item.get("id"),
                        "text": item.get("text", "")
                    })
                
                elif item_type in ("tool_call", "command_execution"):
                    # Codex exec emits "command_execution" for shell commands
                    # and "tool_call" for built-in tools like web_search
                    tool_name = item.get("tool", item.get("command", ""))
                    tool_calls.append({
                        "id": item.get("id"),
                        "tool": tool_name,
                        "args": item.get("args", {}),
                        "result": item.get("aggregated_output", item.get("result", "")),
                        "exit_code": item.get("exit_code"),
                        "status": item.get("status")
                    })
                    
                    # Track screenshots from command output
                    result_str = str(item.get("aggregated_output", item.get("result", "")))
                    if "screenshot" in tool_name.lower() or "screenshot" in result_str.lower():
                        screenshots.append({"tool": tool_name, "output": result_str[:200]})
                    for word in result_str.split():
                        if word.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            screenshots.append({"file": word.strip('"').strip("'")})
                
                elif item_type == "error":
                    errors.append({
                        "id": item.get("id"),
                        "message": item.get("message", "")
                    })
            
            elif etype == "error":
                errors.append({"message": event.get("message", "")})
            
            elif etype == "turn.completed":
                usage = event.get("usage", {})
    
    # Calculate summary stats
    summary = {
        "thread_id": thread_id,
        "total_events": len(events),
        "agent_messages_count": len(agent_messages),
        "tool_calls_count": len(tool_calls),
        "screenshots_count": len(screenshots),
        "errors_count": len(errors),
        "errors": errors,
        "usage": usage,
        "parsed_at": datetime.now().isoformat()
    }
    
    # Extract tool call breakdown
    tool_breakdown = {}
    for tc in tool_calls:
        tool = tc["tool"]
        tool_breakdown[tool] = tool_breakdown.get(tool, 0) + 1
    summary["tool_breakdown"] = tool_breakdown
    
    # Full agent text concatenated (this is usually the report)
    full_text = "\n\n---\n\n".join([m["text"] for m in agent_messages if m["text"]])
    
    return {
        "summary": summary,
        "agent_messages": agent_messages,
        "tool_calls": tool_calls,
        "screenshots": screenshots,
        "full_agent_text": full_text
    }


def main():
    parser = argparse.ArgumentParser(description="Parse Codex JSONL session output")
    parser.add_argument("session_file", help="Path to the JSONL session file")
    parser.add_argument("--report", help="Path to markdown report file (optional)")
    parser.add_argument("--output", "-o", help="Output JSON file path (default: stdout)")
    args = parser.parse_args()
    
    if not os.path.exists(args.session_file):
        print(f"Error: {args.session_file} not found", file=sys.stderr)
        sys.exit(1)
    
    result = parse_jsonl(args.session_file)
    
    # If we have a report file, include it
    if args.report and os.path.exists(args.report):
        with open(args.report, 'r') as f:
            result["markdown_report"] = f.read()
    
    output = json.dumps(result, indent=2, default=str)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Parsed output saved to {args.output}", file=sys.stderr)
        print(f"  Messages: {result['summary']['agent_messages_count']}", file=sys.stderr)
        print(f"  Tool calls: {result['summary']['tool_calls_count']}", file=sys.stderr)
        print(f"  Screenshots: {result['summary']['screenshots_count']}", file=sys.stderr)
        print(f"  Errors: {result['summary']['errors_count']}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
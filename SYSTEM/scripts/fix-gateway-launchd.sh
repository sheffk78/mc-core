#!/bin/bash
# Fix: Register Hermes gateway as a launchd service
# Run this from a SEPARATE terminal (not inside a Hermes chat)
# This will briefly restart the gateway — your active chat session will reconnect

set -e

echo "=== Loading Hermes gateway as launchd service ==="

# Step 1: Bootstrap the plist into launchd
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway.plist
echo "✓ Plist loaded into launchd"

# Step 2: Verify it's loaded
sleep 2
launchctl list ai.hermes.gateway 2>&1 && echo "✓ Service registered" || echo "✗ Service not found"

# Step 3: Check the gateway process
sleep 2
ps aux | grep 'hermes_cli.main gateway' | grep -v grep | head -1

echo ""
echo "=== Done. Gateway is now managed by launchd with KeepAlive. ==="
echo "If it crashes, launchd will auto-restart it within 30s."
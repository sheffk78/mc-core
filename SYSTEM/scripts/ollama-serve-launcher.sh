#!/bin/bash
# ollama-serve-launcher.sh — Starts Ollama server with coexistence env vars
#
# Env vars enable Atlas (64K) + Bedrock (160K) to coexist in VRAM.
# Without these, Ollama evicts one model when the other loads.
#
# Installed as launchd agent: com.openclaw.ollama-serve (RunAtLoad)
#
set -euo pipefail

# Wait for the models directory to be available (external disk mount)
MODELS_DIR="/Users/socializerender/.ollama/models"
for i in $(seq 1 30); do
  if [ -d "$MODELS_DIR" ]; then
    break
  fi
  sleep 2
done

# If port 11434 is already in use (another Ollama instance), kill it first
if lsof -ti:11434 >/dev/null 2>&1; then
  # Give the existing instance 5 seconds to shut down gracefully
  kill $(lsof -ti:11434) 2>/dev/null || true
  sleep 3
  # Force kill if still running
  if lsof -ti:11434 >/dev/null 2>&1; then
    kill -9 $(lsof -ti:11434) 2>/dev/null || true
    sleep 2
  fi
fi

# Start Ollama server with coexistence env vars
export OLLAMA_MAX_LOADED_MODELS=4
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_MODELS="$MODELS_DIR"
export OLLAMA_KEEP_ALIVE=30m
# Limit context to 64K (default: 202K from model metadata). At 202K context,
# Atlas KV cache alone needs ~60GB VRAM, causing OOM eviction and hangs.
# 64K is still very large and keeps both Atlas + Bedrock loaded simultaneously.
export OLLAMA_CONTEXT_LENGTH=65536

exec /Applications/Ollama.app/Contents/Resources/ollama serve

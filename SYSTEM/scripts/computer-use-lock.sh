#!/bin/bash
# computer-use-lock.sh — File-based mutex for computer_use / browser_use across concurrent Hermes sessions.
# Prevents two agents from fighting over the same desktop/browser at the same time.
#
# Usage:
#   computer-use-lock.sh acquire  <chat-name> <estimate-min>  — Try to acquire lock. Exit 0 = got it, exit 1 = held by another.
#   computer-use-lock.sh release                            — Release the current lock.
#   computer-use-lock.sh status                             — Print who holds the lock, or "FREE".
#   computer-use-lock.sh wait    <max-seconds>              — Block until lock is free or timeout.
#
# Lock file: /tmp/computer-use.lock
# Contains: chat-name|acquired-unix-ts|estimate-min|expires-unix-ts
#
# Stale lock detection: timestamp-based. If expires-unix-ts has passed, lock is auto-released.
# No PID check (each Hermes terminal call is a separate bash process that dies immediately).

LOCK_FILE="/tmp/computer-use.lock"
NOW=$(date +%s)

read_lock() {
    if [[ ! -f "$LOCK_FILE" ]]; then
        return 1
    fi
    IFS='|' read -r LOCK_CHAT LOCK_ACQUIRED LOCK_ESTIMATE LOCK_EXPIRES < "$LOCK_FILE"
}

is_lock_expired() {
    read_lock || return 0  # no file = free
    if [[ -n "$LOCK_EXPIRES" ]] && (( NOW > LOCK_EXPIRES )); then
        return 0  # expired
    fi
    return 1  # still valid
}

format_lock_info() {
    local remaining=$(( LOCK_EXPIRES - NOW ))
    local remaining_min=$(( remaining / 60 ))
    local remaining_sec=$(( remaining % 60 ))
    echo "HELD by '${LOCK_CHAT}' — acquired $(date -r "$LOCK_ACQUIRED" '+%H:%M:%S'), expires in ~${remaining_min}m${remaining_sec}s"
}

case "$1" in
    acquire)
        CHAT_NAME="${2:-unknown}"
        ESTIMATE_MIN="${3:-5}"

        # Clean up expired lock
        if is_lock_expired; then
            if [[ -f "$LOCK_FILE" ]]; then
                rm -f "$LOCK_FILE"
                echo "EXPIRED_LOCK_CLEANED: Previous lock had expired. Acquiring now."
            fi
        fi

        # Try to acquire
        if [[ -f "$LOCK_FILE" ]] && ! is_lock_expired; then
            read_lock
            format_lock_info
            echo "DENIED"
            exit 1
        fi

        # Acquire
        EXPIRES=$(( NOW + ESTIMATE_MIN * 60 + 300 ))  # estimate + 5min safety buffer
        echo "${CHAT_NAME}|${NOW}|${ESTIMATE_MIN}|${EXPIRES}" > "$LOCK_FILE"
        echo "ACQUIRED by '${CHAT_NAME}' — expires in ~${ESTIMATE_MIN}min + 5min buffer"
        exit 0
        ;;

    release)
        if [[ ! -f "$LOCK_FILE" ]]; then
            echo "NO_LOCK — nothing to release"
            exit 0
        fi
        read_lock
        rm -f "$LOCK_FILE"
        echo "RELEASED by '${LOCK_CHAT}'"
        exit 0
        ;;

    status)
        if [[ ! -f "$LOCK_FILE" ]]; then
            echo "FREE"
            exit 0
        fi
        if is_lock_expired; then
            rm -f "$LOCK_FILE"
            echo "FREE (expired lock cleaned)"
            exit 0
        fi
        read_lock
        format_lock_info
        exit 0
        ;;

    wait)
        MAX_SECONDS="${2:-120}"
        ELAPSED=0
        while (( ELAPSED < MAX_SECONDS )); do
            if [[ ! -f "$LOCK_FILE" ]] || is_lock_expired; then
                [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
                echo "FREE"
                exit 0
            fi
            sleep 5
            ELAPSED=$(( ELAPSED + 5 ))
            read_lock
            echo "WAITING — $(format_lock_info) — ${ELAPSED}s/${MAX_SECONDS}s" >&2
        done
        echo "TIMEOUT after ${MAX_SECONDS}s"
        exit 1
        ;;

    *)
        echo "Usage: $0 {acquire <chat-name> <estimate-min> | release | status | wait <max-seconds>}"
        exit 2
        ;;
esac
#!/bin/sh
# plex-license-guard.sh — QTS runs "qpkg_cli --check_license 0" daily (07:50 cron),
# which disables PlexMediaServer (Enable=FALSE + async server stop) because its
# QTS license record is missing/invalid. This guard runs the license check (to
# keep QTS behavior intact), waits out the async stop, then restores Plex.
# v2 (2026-09-08, Kit): v1 bug — grep -A3 never saw Enable (7 lines into block)
# and up() raced the async stop, logging false "plex OK". v2 parses the whole
# block, sleeps out the stop, and uses a wait-loop before declaring success.
# Log: /share/CACHEDEV1_DATA/Download/qbittorrent/scripts/plex-guard.log
# Arg "liveness": skip the license check (repair-net mode).
export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:$PATH
LOG=/share/CACHEDEV1_DATA/Download/qbittorrent/scripts/plex-guard.log
CONF=/etc/config/qpkg.conf
ts() { date "+%Y-%m-%d %H:%M:%S"; }
up() { curl -s -m 5 http://localhost:32400/identity >/dev/null 2>&1; }
enabled() { sed -n "/^\[PlexMediaServer\]/,/^\[Q/p" "$CONF" | grep -q "Enable = TRUE"; }
restore() {
  sed -i "/^\[PlexMediaServer\]/,/^\[/ s/Enable = FALSE/Enable = TRUE/" "$CONF"
  /etc/init.d/plex.sh start >/dev/null 2>&1
}

if [ "$1" != "liveness" ]; then
  /sbin/qpkg_cli --check_license 0 >/dev/null 2>&1
  sleep 15   # license check stops Plex asynchronously — give it time to land
fi

if ! enabled; then
  echo "$(ts) check_license disabled Plex -> re-enabling" >> "$LOG"
  restore
  sleep 20
fi

# wait up to 90s for Plex to come up (qpkg start is slow)
i=0
while ! up && [ $i -lt 9 ]; do sleep 10; i=$((i+1)); done

if up; then
  echo "$(ts) plex OK" >> "$LOG"
  exit 0
fi

# one more restoration attempt before declaring failure
echo "$(ts) plex still down -> second restore attempt" >> "$LOG"
restore
sleep 30
if up; then
  echo "$(ts) plex OK (second attempt)" >> "$LOG"
  exit 0
fi
echo "$(ts) plex STILL DOWN after two restore attempts" >> "$LOG"
exit 1
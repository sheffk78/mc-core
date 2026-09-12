#!/usr/bin/env python3
"""media-struct-preflight — GATE for any directory deletion on the QNAP media tree.

Blocks if ANY live mount exists under the target directory. Parses /proc/mounts
\\040 space-escapes in Python (immune to shell-quoting mangling).

Usage:
  media-struct-preflight.sh <absolute-dir>          # from the Mac (SSHes to NAS)
Exit 0 = no mounts under target (empty-check + rmdir-only rules still apply)
Exit 1 = BLOCKED — unmount first, never rm through mounts
"""
import subprocess, sys

NAS_TARGET = sys_target = None
if len(sys.argv) != 2:
    print(__doc__); sys.exit(2)
target = sys.argv[1].rstrip("/") + "/"   # trailing slash = prefix match only

# fetch raw /proc/mounts (device, mountpoint) pairs from the NAS
r = subprocess.run(
    ["bash", "-c",
     "sshpass -p 'fg@UE29bc2WRN' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
     "admin@192.168.1.221 \"cat /proc/mounts\""],
    capture_output=True, text=True, timeout=30)
if r.returncode != 0:
    print(f"FAIL: could not read /proc/mounts over SSH: {r.stderr[:200]}"); sys.exit(2)

hits = []
for line in r.stdout.splitlines():
    parts = line.split()
    if len(parts) < 2: continue
    mnt = parts[1].replace("\\040", " ").replace("\\011", "\t").replace("\\\\", "\\")
    if mnt == target or mnt.startswith(target):
        hits.append(mnt)

if hits:
    print(f"BLOCKED: {len(hits)} live mount(s) under {target} — unmount first, never rm through mounts")
    for h in hits[:10]: print(f"  {h}")
    sys.exit(1)

print(f"OK: no mounts under {target} (empty-check + rmdir-only rules still apply)")
sys.exit(0)
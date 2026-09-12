#!/usr/bin/env python3
"""
media-engine.py — QNAP media pipeline health, healing, and verification.

Owner: Kit. Part of nas-media-download skill.
NAS: 192.168.1.221 (NAS681922), qBittorrent :8081, Plex :32400.
Runbook: SYSTEM/RUNBOOKS/qnap-plex-media-pipeline.md

Subcommands:
  status [--json]        Compact queue status (progress, speeds, ETAs)
  health [--json]        One-shot pipeline health snapshot (exit 1 if unhealthy)
  heal [--dry-run]       Auto-heal errored/stalled torrents (idempotent, rate-limited)
  verify NAME            Verify item(s): qBt 100% + organized + Plex reachable.
                         Prints a line per match when several torrents match.
  map-show NAME PART     Add torrent-name mapping to NAS shows.map (trailing newline!)

Security (2026-09-07 review fixes):
  - Credentials load from ~/.hermes/secrets/qnap-media.json (chmod 600); NOT in source.
  - NAS SSH commands are built with shlex.quote — user input can never break out.
  - Plex token sent via X-Plex-Token HEADER, never in URL query strings.
  - Never prints credentials or tokens.
"""
import json
import os
import sys
import time
import pathlib
import shlex
import shutil
import urllib.request
import urllib.parse
import subprocess
from typing import NoReturn

QB_BASE = "http://192.168.1.221:8081"
PLEX_BASE = "http://192.168.1.221:32400"
NAS_HOST = "admin@192.168.1.221"
NAS_ROOT = "/share/CACHEDEV1_DATA/Download/qbittorrent"
PLEX_SECTIONS = {"tv": "7", "movies": "2"}
SECRETS = os.path.expanduser("~/.hermes/secrets/qnap-media.json")

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
STATE_DIR = os.path.join(WORKSPACE, "SYSTEM", "media")
HEAL_STATE = os.path.join(STATE_DIR, "heal-state.json")
ALERT_LOG = os.path.join(STATE_DIR, "alerts.log")

TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.demonii.com:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.tiny-vps.com:6969/announce",
    "udp://tracker.cyberia.is:6969/announce",
]

DL_STATES = ("downloading", "stalledDL", "queuedDL", "metaDL",
             "checkingDL", "checkingResumeData", "forcedDL")


def fail(msg) -> NoReturn:
    print(f"ERROR: {msg}")
    sys.exit(2)


# ---------------------------------------------------------------- credentials

def load_creds():
    """Load qBittorrent/NAS creds from the secret file. Fail closed."""
    try:
        c = json.loads(pathlib.Path(SECRETS).read_text())
        return c["qb_user"], c["qb_pass"], c["nas_pass"]
    except Exception as e:
        fail(f"credentials unavailable ({SECRETS}): {e}. "
             f"Store {{qb_user, qb_pass, nas_pass}} there (chmod 600).")
        raise  # unreachable


QB_USER, QB_PASS, NAS_PASS = load_creds()


# ---------------------------------------------------------------- utilities

def log_alert(msg):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(ALERT_LOG, "a") as f:
        f.write(f"{time.strftime('%m-%d %H:%M')} {msg}\n")
    # rotation: keep last ~500 lines
    try:
        lines = pathlib.Path(ALERT_LOG).read_text().splitlines()
        if len(lines) > 500:
            pathlib.Path(ALERT_LOG).write_text("\n".join(lines[-500:]) + "\n")
    except Exception:
        pass


def load_state():
    try:
        st = json.loads(pathlib.Path(HEAL_STATE).read_text())
        return st if isinstance(st, dict) else {}
    except Exception:
        return {}


def save_state(st):
    """Atomic write: temp file + rename, so a crash can't corrupt state.
    Corrupt state = rate limits silently reset = swarm-flooding; never accept that."""
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = HEAL_STATE + ".tmp"
    pathlib.Path(tmp).write_text(json.dumps(st, indent=1))
    os.replace(tmp, HEAL_STATE)


def ssh(args, timeout=25, check=False):
    """Run a command on the NAS. `args` is a LIST of remote argv tokens; every
    token is shell-quoted before transport, so interpolation is safe.
    check=True raises on transport failure instead of returning None."""
    quoted = " ".join(shlex.quote(a) for a in args)
    try:
        r = subprocess.run(
            ["sshpass", "-p", NAS_PASS, "ssh", "-o", "StrictHostKeyChecking=no",
             "-o", f"ConnectTimeout={min(timeout, 10)}", NAS_HOST, quoted],
            capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0 and check:
            raise RuntimeError(f"ssh rc={r.returncode}: {r.stderr.strip()[:200]}")
        return r.stdout.strip()
    except RuntimeError:
        raise
    except Exception as e:
        if check:
            raise
        return ""


class Qbt:
    def __init__(self):
        self.login()

    def login(self):
        data = urllib.parse.urlencode({"username": QB_USER, "password": QB_PASS}).encode()
        req = urllib.request.Request(QB_BASE + "/api/v2/auth/login", data=data)
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.headers.get("Set-Cookie", "")
        self.cj = raw.split(";")[0] if raw else ""
        if not self.cj:
            raise RuntimeError("no session cookie from qBittorrent login")

    def get(self, path, params=None):
        url = QB_BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Cookie": self.cj})
        return json.loads(urllib.request.urlopen(req, timeout=20).read())

    def post(self, path, **params):
        """POST form-encoded params. Returns status; raises HTTPError on 4xx/5xx."""
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(QB_BASE + path, data=data, headers={"Cookie": self.cj})
        resp = urllib.request.urlopen(req, timeout=20)
        resp.read()  # drain body so callers see errors, not silent truncation
        return resp.status

    def add(self, magnet, savepath=None):
        """Add magnet with fresh trackers. savepath pins the download location."""
        params = {"urls": magnet, "trackers": "|".join(TRACKERS)}
        if savepath:
            params["savepath"] = savepath
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(QB_BASE + "/api/v2/torrents/add", data=data,
                                     headers={"Cookie": self.cj})
        return urllib.request.urlopen(req, timeout=20).status


def plex_token():
    """Read Plex token from NAS; raises if unreadable (callers decide)."""
    v = ssh(["cat", f"{NAS_ROOT}/scripts/plex.token"])
    return v if v and len(v) > 10 else None


def plex_request(path):
    """Authenticated Plex GET using X-Plex-Token HEADER (token never in URL/logs)."""
    tok = plex_token()
    if not tok:
        return None
    req = urllib.request.Request(PLEX_BASE + path, headers={"X-Plex-Token": tok})
    try:
        return urllib.request.urlopen(req, timeout=8)
    except Exception:
        return None


def plex_alive():
    try:
        urllib.request.urlopen(PLEX_BASE + "/identity", timeout=8)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- health

def pipeline_problems(qbt):
    """Collect current problems. qbt may be None if unreachable."""
    problems = []
    torrents = []
    if qbt is None:
        try:
            qbt = Qbt()
        except Exception as e:
            return [f"qBittorrent unreachable: {e}"], [], None
    try:
        torrents = qbt.get("/api/v2/torrents/info")
    except Exception as e:
        problems.append(f"qBittorrent API error: {e}")
        return problems, [], qbt

    errored = [t for t in torrents if t["state"] == "error"]
    dead_stalled = [t for t in torrents if t["state"] in ("stalledDL", "metaDL")
                    and t["dlspeed"] == 0 and (t["num_seeds"] + t["num_leechs"]) == 0]

    if errored:
        problems.append(f"{len(errored)} errored torrent(s): " +
                        ", ".join(t["name"][:40] for t in errored[:5]))
    if dead_stalled:
        problems.append(f"{len(dead_stalled)} stalled with no peers: " +
                        ", ".join(t["name"][:40] for t in dead_stalled[:5]))

    dfline = ssh(["df", "-h", "/share/CACHEDEV1_DATA"], check=False)
    if not dfline:
        # two-probe gate (2026-09-09): one empty df = transient ssh blip, not
        # NAS-down — logtail/perm checks have hit while df missed once. Re-probe
        # once after 5s before alerting (same pattern as the cross-agent watchdogs).
        time.sleep(5)
        dfline = ssh(["df", "-h", "/share/CACHEDEV1_DATA"], check=False)
    if dfline:
        try:
            pct = int(dfline.split()[4].rstrip("%"))
            if pct > 90:
                problems.append(f"NAS disk {pct}% full")
        except Exception:
            pass
    else:
        problems.append("SSH disk check unavailable (NAS unreachable?)")

    perm = ssh(["stat", "-c", "%U", f"{NAS_ROOT}/scripts/auto-organize.sh"])
    if perm and perm != "qbittorrent":
        problems.append(f"organize hook owner is '{perm}' (must be qbittorrent) — "
                        f"hook silently broken. Fix: docker exec chown -R 1001:100 /downloads")
    logtail = ssh(["tail", "-1", f"{NAS_ROOT}/scripts/auto-organize.log"])

    # log freshness: warn if hook log is stale AND completions happened recently
    if not logtail:
        problems.append("auto-organize.log missing/empty — hook may never have run")
    else:
        try:
            mtime = int(ssh(["stat", "-c", "%Y", f"{NAS_ROOT}/scripts/auto-organize.log"],
                            check=True))
            if time.time() - mtime > 7 * 86400:
                problems.append("auto-organize.log untouched for >7 days — hook may be broken")
        except Exception:
            pass  # stat unavailable: skip freshness, perm+log checks still ran

    if not plex_alive():
        problems.append("Plex :32400 not responding (check /etc/init.d/plex.sh, qpkg.conf Enable)")

    return problems, errored + dead_stalled, qbt


def cmd_health(as_json=False):
    problems, targets, qbt = [], [], None
    try:
        problems, targets, qbt = pipeline_problems(qbt)
    except Exception as e:
        problems.append(f"health check failed: {e}")

    dl = _global_speed(qbt) if qbt else 0
    result = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "healthy": len(problems) == 0,
        "problems": problems,
        "queue": {"targetable": len(targets),
                  "total": len(qbt.get("/api/v2/torrents/info")) if qbt else 0,
                  "dl_speed_mbps": round(dl / 1e6, 1)},
    }
    if as_json:
        print(json.dumps(result, indent=1))
    else:
        if result["healthy"]:
            print("MEDIA PIPELINE: HEALTHY")
        else:
            print("MEDIA PIPELINE: ISSUES")
            for p in problems:
                print("  🔴 " + p)
    sys.exit(0 if result["healthy"] else 1)


def _global_speed(qbt):
    try:
        gi = qbt.get("/api/v2/transfer/info")
        return gi.get("dl_info_speed", 0)
    except Exception:
        return 0


# ---------------------------------------------------------------- heal

def do_heal_torrents(qbt, targets, dry=False):
    """Deterministic healing, rate-limited per hash via heal-state.json."""
    state = load_state()
    now = time.time()
    healed, skipped = [], []

    for t in targets:
        h, name, st = t["hash"], t["name"], t["state"]
        rec = state.get(h, {"count": 0, "last": 0})
        if rec["count"] >= 3 and now - rec["last"] < 86400:
            skipped.append(f"{name[:45]} (heal limit reached — needs new source)")
            log_alert(f"HEAL-EXHAUSTED {name[:60]} — needs replacement source")
            continue
        if now - rec["last"] < 3600 and rec["count"] > 0:
            skipped.append(f"{name[:45]} (cooldown)")
            continue

        if dry:
            healed.append(f"{name[:45]}")
            continue

        try:
            # error state NEVER re-animates in place (runbook-verified 09-07).
            # delete-entry + re-add SAME hash fresh is the only proven fix.
            if st == "error":
                savepath = (t.get("save_path") or "").strip()
                if t["progress"] > 0:
                    # files partially exist — do NOT deleteFiles; recheck first
                    qbt.post("/api/v2/torrents/recheck", hashes=h)
                    time.sleep(3)
                    t2 = next((x for x in qbt.get("/api/v2/torrents/info?hashes=" + h)
                               if x["hash"] == h), None)
                    if t2 and t2["progress"] > 0:
                        qbt.post("/api/v2/torrents/setForceStart", hashes=h, value="true")
                        rec["count"] += 1; rec["last"] = now; state[h] = rec
                        healed.append(f"{name[:45]} (partial-data recheck + force-start)")
                        continue
                    # recheck dropped to 0 → data gone → safe entry-delete + re-add
                qbt.post("/api/v2/torrents/delete", hashes=h, deleteFiles="false")
                time.sleep(2)
                magnet = f"magnet:?xt=urn:btih:{h}&dn={urllib.parse.quote(name)}"
                qbt.add(magnet, savepath=savepath or None)
                action = "re-added fresh w/ trackers"
            else:
                # stalled with no peers: addTrackers takes HASH singular (others take hashes)
                qbt.post("/api/v2/torrents/addTrackers", hash=h, urls="|".join(TRACKERS))
                qbt.post("/api/v2/torrents/setForceStart", hashes=h, value="true")
                action = "trackers + force-start"

            rec["count"] += 1
            rec["last"] = now
            state[h] = rec
            healed.append(f"{name[:45]} ({action})")
            log_alert(f"HEALED {name[:60]} via {action}")
        except Exception as e:
            skipped.append(f"{name[:45]} (heal failed: {e})")
            log_alert(f"HEAL-FAIL {name[:60]}: {e}")

    if not dry:
        # prune entries older than 7 days so the file can't grow unbounded
        state = {k: v for k, v in state.items() if now - v.get("last", 0) < 7 * 86400}
        save_state(state)
    return healed, skipped


def cmd_heal(dry=False):
    try:
        qbt = Qbt()
        torrents = qbt.get("/api/v2/torrents/info")
    except Exception as e:
        fail(f"qBittorrent unreachable: {e}")
    targets = [t for t in torrents if t["state"] == "error" or
               (t["state"] in ("stalledDL", "metaDL") and t["dlspeed"] == 0
                and (t["num_seeds"] + t["num_leechs"]) == 0)]
    if not targets:
        print("HEAL: nothing to heal (0 errored, 0 dead-stalled)")
        return
    healed, skipped = do_heal_torrents(qbt, targets, dry=dry)
    print(f"HEAL: {len(healed)} acted on, {len(skipped)} skipped")
    for hline in healed:
        print("  ✔ " + hline)
    for s in skipped:
        print("  – " + s)


# ---------------------------------------------------------------- verify

def cmd_verify(name):
    """Verify EVERY torrent matching NAME (substring). Each match gets its own
    verdict line; exit 1 only if any real match fails."""
    try:
        qbt = Qbt()
        torrents = qbt.get("/api/v2/torrents/info")
    except Exception as e:
        fail(f"qBittorrent unreachable: {e}")

    matches = [t for t in torrents if name.lower() in t["name"].lower()]
    if not matches:
        print(f"VERIFY: no torrent matching '{name}'")
        sys.exit(2)

    plex_ok = plex_alive()
    sections_ok = None
    if plex_ok:
        resp = plex_request("/library/sections")
        sections_ok = (resp is not None)

    any_fail = False
    for t in matches:
        checks = {}
        checks["download_complete"] = t["progress"] >= 0.999
        # pattern is a plain argv token; ssh() shell-quotes it for transport
        pattern = f"*{name.split()[0]}*" if name.split() else f"*{name}*"
        find = ssh(["find", f"{NAS_ROOT}/TV Shows", f"{NAS_ROOT}/Movies",
                    "-iname", pattern, "-type", "f"])
        checks["organized_in_plex_tree"] = bool(find)
        checks["plex_alive"] = plex_ok
        checks["plex_sections_ok"] = sections_ok

        ok = (checks["download_complete"] and checks["organized_in_plex_tree"]
              and checks["plex_alive"] and sections_ok is not False)
        if not ok:
            any_fail = True
        marks = {True: "✔", False: "✘", None: "?"}
        print(f"VERIFY '{t['name'][:60]}': {'OK' if ok else 'ISSUES'}")
        for k, v in checks.items():
            print(f"  {marks[v]} {k}")
    sys.exit(1 if any_fail else 0)


def ssh_write(path, content):
    """Write content to a NAS file via `cat > path` (fixed command, no user
    tokens in the remote shell string; content travels over stdin)."""
    quoted = "cat > " + shlex.quote(path)
    try:
        r = subprocess.run(
            ["sshpass", "-p", NAS_PASS, "ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=10", NAS_HOST, quoted],
            input=content, capture_output=True, text=True, timeout=25)
        return r.returncode == 0
    except Exception:
        return False


# ---------------------------------------------------------------- map-show

def cmd_map_show(name_part, plex_name):
    """Read-modify-write shows.map: idempotent, trailing newline guaranteed
    (lesson 0c), no shell operators on the remote side (injection-safe)."""
    map_path = f"{NAS_ROOT}/scripts/shows.map"
    content = ssh(["cat", map_path])
    if not content:
        fail("cannot read shows.map (NAS unreachable or file missing)")
    lines = [l for l in content.splitlines() if l.strip()]
    new_line = f"{name_part}|{plex_name}"
    if any(l.split("|", 1)[0].strip() == name_part for l in lines):
        print(f"MAP-SHOW: {name_part} already mapped — no change")
        print("\n".join(lines[-2:]))
        return
    lines.append(new_line)
    ok = ssh_write(map_path, "\n".join(lines) + "\n")
    tail = ssh(["tail", "-2", map_path])
    added = new_line in tail
    print(f"MAP-SHOW: {name_part} -> {plex_name} | "
          f"{'confirmed on NAS' if (ok and added) else 'WARNING: write failed — verify manually'}")
    print(tail)


# ---------------------------------------------------------------- status

def cmd_status(as_json=False):
    try:
        qbt = Qbt()
    except Exception as e:
        fail(f"qBittorrent unreachable: {e}")
    torrents = qbt.get("/api/v2/torrents/info")
    active = [t for t in torrents if t["state"] in DL_STATES]
    active.sort(key=lambda x: -x["dlspeed"])
    gi = qbt.get("/api/v2/transfer/info")
    rows = []
    for t in active:
        eta = t.get("eta", 0)
        eta_s = f"{eta//3600}h{(eta%3600)//60:02d}m" if 0 < eta < 8640000 else "--"
        rows.append({"name": t["name"], "state": t["state"],
                     "pct": round(t["progress"] * 100, 1),
                     "dl_mbps": round(t["dlspeed"] / 1e6, 2),
                     "eta": eta_s, "seeds": t["num_seeds"]})
    out = {"global_dl_mbps": round(gi["dl_info_speed"] / 1e6, 1),
           "global_up_mbps": round(gi["up_info_speed"] / 1e6, 1),
           "active": rows, "errored": len([t for t in torrents if t["state"] == "error"])}
    if as_json:
        print(json.dumps(out, indent=1))
    else:
        print(f"QUEUE: {out['global_dl_mbps']} MB/s ↓ | {len(active)} active | "
              f"{out['errored']} errored")
        for r in rows:
            print(f"  [{r['state']:<11}] {r['pct']:6.1f}% ↓{r['dl_mbps']:6.2f} "
                  f"ETA {r['eta']:>7} seeds:{r['seeds']:>3} | {r['name'][:55]}")


# ---------------------------------------------------------------- main

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "status"
    as_json = "--json" in args
    if cmd == "health":
        cmd_health(as_json=as_json)  # heal is a separate command; watchdog composes them
    elif cmd == "heal":
        cmd_heal(dry="--dry-run" in args)
    elif cmd == "verify":
        nm = next((a for a in args[1:] if not a.startswith("-")), None)
        if not nm:
            print("usage: media-engine.py verify NAME")
            sys.exit(2)
        cmd_verify(nm)
    elif cmd == "map-show":
        parts = [a for a in args[1:] if not a.startswith("-")]
        if len(parts) < 2:
            print('usage: media-engine.py map-show "name-part" "Plex Show (Year)"')
            sys.exit(2)
        cmd_map_show(parts[0], " ".join(parts[1:]))
    elif cmd == "status":
        cmd_status(as_json=as_json)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
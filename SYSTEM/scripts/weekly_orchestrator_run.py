#!/usr/bin/env python3
"""Weekly marketing orchestrator run — performance pulse + competitor radar for all brands."""
import sys, json, subprocess, time, re, os
from pathlib import Path
from datetime import datetime

HOME = Path.home()
sys.path.insert(0, str(HOME / ".openclaw/workspace/SYSTEM/scripts"))
import yaml
from marketing_brain import record_insight, ensure_cache_dir

CACHE = HOME / ".openclaw/workspace/SYSTEM/cache/marketing"
BRANDS_DIR = HOME / ".openclaw/workspace/Kit/life/brands"
TODAY = datetime.now().strftime("%Y-%m-%d")

registry = yaml.safe_load((HOME / ".openclaw/workspace/SYSTEM/marketing/discord-channels.yaml").read_text())

def resolve_channel(brand, config):
    cid = config.get("discord_channel_id") or registry.get("brands", {}).get(brand, {}).get("channel_id")
    return cid

def curl_uptime(url):
    r = subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code} %{time_total}",
                        "-L", "--max-time", "25", url], capture_output=True, text=True, timeout=35)
    parts = r.stdout.split()
    return {"status_code": int(parts[0]) if parts and parts[0].isdigit() else None,
            "response_time": float(parts[1]) if len(parts) > 1 else None}

def with_retry(fn, *a):
    for attempt in range(2):
        try:
            out = fn(*a)
            if out is not None:
                return out
        except Exception as e:
            print(f"  attempt {attempt+1} failed: {e}")
        if attempt == 0:
            time.sleep(5)
    return None

# ---------- PERFORMANCE PULSE ----------
def run_performance(brand, config):
    print(f"\n=== PERF: {brand} ===")
    cache_dir = CACHE / "performance-pulse" / brand
    cache_dir.mkdir(parents=True, exist_ok=True)
    trend_dir = cache_dir / "trend"; trend_dir.mkdir(exist_ok=True)
    metrics = {}
    results = {}
    total = responded = 0
    for src in config.get("sources", []):
        name = src["name"]; total += 1
        data = None
        if src.get("type") == "uptime":
            data = with_retry(curl_uptime, src["url"])
            if data: metrics[f"{name}_status"] = data["status_code"]; metrics[f"{name}_response_time"] = data["response_time"]
        elif name == "railway_deployments":
            def rf():
                cmd = src.get("command", "railway-graphql deployments")
                cmd = cmd.replace("railway-graphql", str(HOME / "bin/railway-graphql"))
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=45)
                if r.returncode != 0: raise RuntimeError(r.stderr[:200])
                return r.stdout[:2000]
            data = with_retry(rf)
            if data: metrics["railway_deployments"] = 1
        elif name == "siteguru":
            # No SiteGuru MCP access from this run — mark unavailable, don't fabricate
            data = None
        if data is not None:
            results[name] = data; responded += 1
        else:
            results[name] = "unavailable"
        print(f"  {name}: {'ok' if data is not None else 'unavailable'}")

    last_path = cache_dir / "last_week.json"
    is_first = not last_path.exists()
    deltas = {}
    notable = []
    if not is_first:
        prev = json.loads(last_path.read_text())
        for k, v in metrics.items():
            p = prev.get(k)
            if isinstance(v, (int, float)) and isinstance(p, (int, float)) and p:
                pct = (v - p) / p * 100
                if abs(pct) > 0.5:
                    arrow = "↑" if pct > 0 else "↓"
                    deltas[k] = f"{arrow} {abs(pct):.0f}%"
                    if abs(pct) > 20 and k.endswith("_response_time") is False:
                        notable.append((k, pct, arrow))
    else:
        deltas = {}

    # trend
    week_files = sorted(trend_dir.glob("week_*.json"))[-3:]
    trends = {}
    if len(week_files) >= 2:
        weeks = [json.loads(f.read_text()) for f in week_files]
        for k in metrics:
            vals = [w.get(k) for w in weeks if isinstance(w.get(k), (int, float))]
            vals.append(metrics[k]) if isinstance(metrics[k], (int, float)) else None
            if len(vals) >= 3:
                ch = [vals[i+1] - vals[i] for i in range(len(vals)-1)]
                ups = sum(1 for c in ch if c > 0); downs = sum(1 for c in ch if c < 0)
                trends[k] = "↑ up 3 weeks" if ups == len(ch) else ("↓ down 2" if downs >= 2 else "→ flat")

    # report
    lines = [f"## 📊 Performance Pulse — {brand} (Week of {TODAY})"]
    if is_first:
        lines.append("First run — no comparison. Baseline saved for next week.")
    lines.append(f"Sources responded: {responded}/{total}")
    for name, data in results.items():
        if data == "unavailable":
            lines.append(f"⬜ {name}: unavailable")
        elif isinstance(data, dict) and "status_code" in data:
            sc = data["status_code"]; rt = data.get("response_time")
            emoji = "✅" if sc == 200 else "⚠️"
            extra = deltas.get(f"{name}_response_time", "")
            lines.append(f"{emoji} {name}: HTTP {sc}, {rt*1000:.0f}ms" + (f" ({extra})" if extra else "") + (f" [trend: {trends.get(name+'_response_time')}]" if name+'_response_time' in trends else ""))
        elif name == "railway_deployments":
            lines.append("✅ railway: deployment data retrieved")
    report = "\n".join(lines)

    # post to discord
    cid = resolve_channel(brand, config)
    if cid:
        post_discord(cid, report)
    else:
        print(f"  WARNING: no discord channel for {brand}")

    # brain write-back
    brain_updates = 0
    for k, pct, arrow in notable:
        record_insight(brand, "channel_performance",
                       f"Weekly pulse: {k} {arrow} {abs(pct):.0f}% vs last week", source="performance-pulse")
        brain_updates += 1

    # save baseline
    last_path.write_text(json.dumps(metrics, indent=2))
    n = len(list(trend_dir.glob("week_*.json"))) + 1
    (trend_dir / f"week_{n:03d}.json").write_text(json.dumps(metrics, indent=2))
    for old in sorted(trend_dir.glob("week_*.json"))[:-3]:
        old.unlink()
    print(f"  responded {responded}/{total}, first_run={is_first}, brain_updates={brain_updates}")
    return {"ran": True, "sources_responded": f"{responded}/{total}", "first_run": is_first,
            "discord": bool(cid), "brain_updates": brain_updates, "report": report}

# ---------- COMPETITOR RADAR ----------
def check_robots(base_url, path):
    try:
        r = subprocess.run(["curl", "-s", "-L", "--max-time", "10", base_url.rstrip("/") + "/robots.txt"],
                           capture_output=True, text=True, timeout=15)
        ua_match = False
        for line in r.stdout.split("\n"):
            line = line.strip().lower()
            if line.startswith("user-agent:"):
                ua_match = line.split(":", 1)[1].strip() == "*"
            elif ua_match and line.startswith("disallow:"):
                d = line.split(":", 1)[1].strip()
                if d == "/": return False
                if d and path.startswith(d): return False
        return True
    except Exception:
        return True

def scrape(url):
    def _s():
        r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                            url], capture_output=True, text=True, timeout=40)
        html = r.stdout
        if not html or len(html) < 500: return None
        try:
            import trafilatura
            txt = trafilatura.extract(html, output_format="txt", include_comments=False)
        except Exception:
            txt = None
        if not txt:
            txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
            txt = re.sub(r"<[^>]+>", " ", txt)
            txt = re.sub(r"\s+", " ", txt).strip()
        return txt[:20000] if txt and len(txt) > 200 else None
    return with_retry(_s)

def score_change(text):
    t = text.lower()
    major = ["pricing", "price", "$", "/mo", "tier", "plan", "headline", "launch", "new product"]
    moderate = ["new", "introducing", "blog", "feature", "case study", "guide", "announcement"]
    if any(k in t for k in major): return "major"
    if any(k in t for k in moderate): return "moderate"
    return "minor"

def run_competitors(brand, config):
    print(f"\n=== RADAR: {brand} ===")
    comps = config.get("competitors", [])
    if not comps:
        return {"ran": False, "reason": "no competitors configured"}
    cache_dir = CACHE / "competitor-radar" / brand
    cache_dir.mkdir(parents=True, exist_ok=True)
    report_lines = [f"## 📡 Competitor Radar — {brand} (Week of {TODAY})"]
    all_new = {}
    success = fail = 0
    failed_urls = []
    brain_updates = 0
    brand_slug = brand.replace(" ", "")
    for comp in comps:
        cname = comp["name"]; base = comp["url"]
        comp_dir = cache_dir / cname.replace(" ", "_").replace("/", "_")
        comp_dir.mkdir(parents=True, exist_ok=True)
        prev_path = comp_dir / "last_scan.json"
        prev = json.loads(prev_path.read_text()).get("data", {}) if prev_path.exists() else {}
        current = {}
        notable_comp = []
        for w in comp.get("watch", []):
            path = w["path"]
            url = base.rstrip("/") + path
            time.sleep(2)
            if not check_robots(base, path):
                notable_comp.append(f"🚫 robots.txt disallows {path} — skipped")
                continue
            content = scrape(url)
            if content is None:
                fail += 1; failed_urls.append(url)
                current[f"{cname}_{path}"] = {"content": prev.get(f"{cname}_{path}", {}).get("content", ""), "ts": TODAY, "failed": True}
                continue
            success += 1
            key = f"{cname}_{path}"
            current[key] = {"content": content, "ts": TODAY}
            prev_content = prev.get(key, {}).get("content", "")
            if prev_content:
                prev_lines = set(l.strip() for l in prev_content.split("\n") if len(l.strip()) > 25)
                cur_lines = [l.strip() for l in content.split("\n") if len(l.strip()) > 25]
                added = [l for l in cur_lines if l not in prev_lines]
                if added:
                    sig = score_change(" ".join(added[:20]))
                    sample = added[0][:140]
                    if sig == "major":
                        notable_comp.append(f"⚠️ **MAJOR:** Changes on {path} — e.g. \"{sample}\"")
                    elif sig == "moderate":
                        notable_comp.append(f"**MODERATE:** {len(added)} new content lines on {path} — e.g. \"{sample}\"")
                    else:
                        notable_comp.append(f"(minor: {len(added)} small text changes on {path})")
            else:
                notable_comp.append(f"**NEW BASELINE:** {path} first captured")
        all_new.update(current)
        if notable_comp:
            report_lines.append(f"\n### {cname}")
            for nc in notable_comp:
                if not nc.startswith("(minor"):
                    report_lines.append(nc)
                else:
                    print(f"  {cname}: {nc}")
            for nc in notable_comp:
                if nc.startswith(("⚠️", "**MODERATE")):
                    record_insight(brand_slug, "competitive_context", f"{cname}: {nc}",
                                   source="competitor-radar")
                    brain_updates += 1
        else:
            report_lines.append(f"\n### {cname}\nNo significant changes detected.")
    report_lines.append(f"\n---\n📊 Scrape stats: {success}/{success+fail} URLs succeeded"
                        + (f", {fail} failed ({', '.join(failed_urls[:3])})" if fail else ""))
    report = "\n".join(report_lines)
    cid = resolve_channel(brand, config)
    if cid:
        post_discord(cid, report)
    else:
        print(f"  WARNING: no discord channel for {brand}")
    # save baselines: per-competitor + combined
    for comp in comps:
        cname = comp["name"]
        comp_dir = cache_dir / cname.replace(" ", "_").replace("/", "_")
        sub = {k: v for k, v in all_new.items() if k.startswith(cname)}
        (comp_dir / "last_scan.json").write_text(json.dumps({"timestamp": TODAY, "data": sub}, indent=2))
    (cache_dir / f"all_scans_{TODAY}.json").write_text(json.dumps({"timestamp": TODAY, "data": all_new}, indent=2))
    print(f"  scraped {success}/{success+fail}, brain_updates={brain_updates}")
    return {"ran": True, "urls_ok": success, "urls_failed": fail, "discord": bool(cid),
            "brain_updates": brain_updates, "report": report}

# ---------- DISCORD ----------
def post_discord(channel_id, text):
    for i in range(0, len(text), 1900):
        chunk = text[i:i+1900]
        r = subprocess.run(["hermes", "send", "-t", f"discord:{channel_id}", "-f", "-"],
                           input=chunk, capture_output=True, text=True, timeout=60)
        ok = r.returncode == 0
        print(f"  discord {channel_id}: {'sent' if ok else 'FAILED ' + r.stderr[:150]}")
        if not ok:
            return False
        time.sleep(1)
    return True

# ---------- MAIN ----------
if __name__ == "__main__":
    if __name__ == "__main__":
        state = {"week_of": TODAY, "brands": {}}
    brand_dirs = sorted(p.name for p in BRANDS_DIR.iterdir() if (p / "marketing").exists())
    summary_brands = []
    for slug in brand_dirs:
        mdir = BRANDS_DIR / slug / "marketing"
        perf_cfg_path = mdir / "performance-sources.yaml"
        comp_cfg_path = mdir / "competitors.yaml"
        bstate = {}
        brand_display = slug
        if perf_cfg_path.exists():
            cfg = yaml.safe_load(perf_cfg_path.read_text())
            brand_display = cfg.get("brand", slug)
            try:
                r = run_performance(brand_display, cfg)
            except Exception as e:
                print(f"PERF FAILED {slug}: {e}"); r = {"ran": False, "error": str(e)}
            bstate["performance_pulse"] = r
        else:
            bstate["performance_pulse"] = {"ran": False, "reason": "missing performance-sources.yaml"}
        if comp_cfg_path.exists():
            cfg = yaml.safe_load(comp_cfg_path.read_text())
            try:
                r = run_competitors(brand_display, cfg)
            except Exception as e:
                print(f"RADAR FAILED {slug}: {e}"); r = {"ran": False, "error": str(e)}
            bstate["competitor_radar"] = r
        else:
            bstate["competitor_radar"] = {"ran": False, "reason": "missing competitors.yaml"}
        bstate["brain_updated"] = (bstate.get("performance_pulse", {}).get("brain_updates", 0) +
                                   bstate.get("competitor_radar", {}).get("brain_updates", 0)) > 0
        state["brands"][slug] = bstate
        summary_brands.append((slug, bstate))

    state_path = HOME / ".openclaw/workspace/SYSTEM/cache/marketing-orchestrator/weekly-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, default=str))
    print("\nSTATE SAVED:", state_path)

    # combined summary (console; discord post handled by caller)
    print("\n===== COMBINED SUMMARY =====")
    for slug, bs in summary_brands:
        pp, cr = bs.get("performance_pulse", {}), bs.get("competitor_radar", {})
        print(f"\n{slug}: perf={pp.get('sources_responded') or pp.get('reason')} radar_ok={cr.get('ran')} urls_ok={cr.get('urls_ok')} brain={bs['brain_updated']}")


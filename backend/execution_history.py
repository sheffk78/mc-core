"""
Execution History module for Mission Control Schedule View
Reads cron job execution history from ~/.openclaw/cron/runs/ and provides stats
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

RUNS_PATH = Path.home() / ".openclaw" / "cron" / "runs"


async def read_job_execution_history(job_id: str) -> Dict:
    """
    Read execution history for a specific job from ~/.openclaw/cron/runs/{jobId}.jsonl
    Returns last 3 runs + aggregated metrics
    """
    history_file = RUNS_PATH / f"{job_id}.jsonl"
    
    try:
        if not history_file.exists():
            return {
                "runs": [],
                "lastRun": None,
                "successRate7d": None,
                "totalRuns": 0
            }
        
        # Read JSONL file (one JSON object per line)
        runs = []
        with open(history_file, 'r') as f:
            for line in f:
                if line.strip():
                    runs.append(json.loads(line))
        
        # Sort by timestamp (newest first)
        runs.sort(key=lambda r: r.get('runAtMs', 0), reverse=True)
        
        # Get last 3 runs
        last_3_runs = runs[:3]
        last_run = runs[0] if runs else None
        
        # Calculate success rate for last 7 days
        success_rate_7d = calculate_success_rate(runs, 7)
        
        return {
            "runs": last_3_runs,
            "lastRun": last_run,
            "successRate7d": success_rate_7d,
            "totalRuns": len(runs)
        }
    
    except Exception as e:
        print(f"Error reading execution history for {job_id}: {e}")
        return {
            "runs": [],
            "lastRun": None,
            "successRate7d": None,
            "totalRuns": 0
        }


def calculate_success_rate(runs: List[Dict], days: int) -> Optional[int]:
    """
    Calculate success rate for runs in the last N days
    """
    if not runs:
        return None
    
    cutoff_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    recent_runs = [r for r in runs if r.get('runAtMs', 0) > cutoff_ms]
    
    if not recent_runs:
        return None
    
    successful = sum(1 for r in recent_runs if r.get('status') == 'success')
    total = len(recent_runs)
    
    return int((successful / total) * 100)


def parse_cron_field(field: str, min_val: int, max_val: int) -> List[int]:
    """Parse a single cron field (e.g. '*/5', '1-5', '0,6') into sorted list of ints."""
    values: set = set()
    for part in field.split(','):
        if part == '*':
            values.update(range(min_val, max_val + 1))
        elif '/' in part:
            base, step_str = part.split('/', 1)
            step = int(step_str)
            if base == '*':
                start, end = min_val, max_val
            elif '-' in base:
                start, end = map(int, base.split('-'))
            else:
                start, end = int(base), max_val
            values.update(range(start, end + 1, step))
        elif '-' in part:
            start, end = map(int, part.split('-'))
            values.update(range(start, end + 1))
        else:
            try:
                values.add(int(part))
            except ValueError:
                pass
    return sorted(values)


def calculate_run_times_for_day(cron_expr: str, date: datetime) -> List[Dict]:
    """
    Calculate the (hour, minute) pairs when a cron job runs on a given date.
    Returns a list of {"hour": int, "minute": int} dicts, sorted by time.
    Cron format: minute hour dom month dow  (standard 5-field cron)
    """
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return []

        min_field, hour_field, dom_field, mon_field, dow_field = parts

        # Check month match
        month_vals = parse_cron_field(mon_field, 1, 12)
        if date.month not in month_vals:
            return []

        # Day-of-week conversion: Python weekday() → 0=Mon…6=Sun; cron dow → 0/7=Sun,1=Mon…6=Sat
        python_wd = date.weekday()          # 0=Mon, 6=Sun
        cron_dow = (python_wd + 1) % 7     # Mon=1 … Sat=6, Sun=0

        dom_is_star = dom_field == '*'
        dow_is_star = dow_field == '*'

        dom_vals = parse_cron_field(dom_field, 1, 31)
        dow_vals_raw = parse_cron_field(dow_field, 0, 7)
        dow_vals = set(v % 7 for v in dow_vals_raw)  # normalise 7→0 (Sunday)

        if dom_is_star and dow_is_star:
            day_matches = True
        elif dom_is_star:
            day_matches = cron_dow in dow_vals
        elif dow_is_star:
            day_matches = date.day in dom_vals
        else:
            # Both non-wildcard: standard OR semantics
            day_matches = (date.day in dom_vals) or (cron_dow in dow_vals)

        if not day_matches:
            return []

        hours = parse_cron_field(hour_field, 0, 23)
        minutes = parse_cron_field(min_field, 0, 59)
        return [{"hour": h, "minute": m} for h in hours for m in minutes]

    except Exception as e:
        print(f"Error parsing cron expression '{cron_expr}': {e}")
        return []


def find_execution_near_time(
    runs: List[Dict], scheduled_dt: datetime, window_minutes: int = 10
) -> Optional[Dict]:
    """Return the run record closest to scheduled_dt within window_minutes, or None."""
    scheduled_ms = scheduled_dt.timestamp() * 1000
    window_ms = window_minutes * 60 * 1000
    best: Optional[Dict] = None
    best_diff = float('inf')
    for run in runs:
        diff = abs(run.get('runAtMs', 0) - scheduled_ms)
        if diff <= window_ms and diff < best_diff:
            best = run
            best_diff = diff
    return best


async def generate_weekly_schedule(jobs: List[Dict], week_start: datetime) -> List[Dict]:
    """
    Build a flat list of calendar events for every enabled job over the 7-day
    week starting on week_start (Monday 00:00).

    Each entry is unique by (jobId, date, hour) — jobs that fire more than once
    per hour are collapsed to one block showing the best-known status.
    """
    events: List[Dict] = []
    now = datetime.now()

    for job in jobs:
        if not job.get('enabled', True):
            continue

        cron_expr = job.get('cron', '')
        if not cron_expr or len(cron_expr.split()) != 5:
            continue  # skip non-standard / every-N-minutes strings

        job_id = job.get('id')

        # Load all historical runs from JSONL file
        all_runs: List[Dict] = []
        history_file = RUNS_PATH / f"{job_id}.jsonl"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                all_runs.append(json.loads(line))
                            except Exception:
                                pass
            except Exception:
                pass

        for day_offset in range(7):
            date = week_start + timedelta(days=day_offset)
            run_times = calculate_run_times_for_day(cron_expr, date)
            if not run_times:
                continue

            # Collapse to one entry per hour (keep earliest minute in that hour)
            by_hour: Dict[int, int] = {}
            for rt in run_times:
                h = rt['hour']
                if h not in by_hour:
                    by_hour[h] = rt['minute']

            for hour, minute in sorted(by_hour.items()):
                scheduled_dt = date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                execution = find_execution_near_time(all_runs, scheduled_dt)

                if execution:
                    status = execution.get('status', 'scheduled')
                    last_run = datetime.fromtimestamp(
                        execution['runAtMs'] / 1000
                    ).isoformat()
                    duration = execution.get('durationMs')
                    output = execution.get('summary') or execution.get('error', '') or ''
                else:
                    status = 'scheduled'
                    last_run = None
                    duration = None
                    output = None

                events.append({
                    'jobId': job_id,
                    'jobName': job.get('name', ''),
                    'description': job.get('description', ''),
                    'brand': job.get('brand'),  # Include brand for filtering
                    'cron': cron_expr,
                    'date': date.strftime('%Y-%m-%d'),
                    'dayOfWeek': day_offset,   # 0 = Monday
                    'hour': hour,
                    'minute': minute,
                    'scheduledTime': scheduled_dt.isoformat(),
                    'status': status,
                    'lastRun': last_run,
                    'duration': duration,
                    'output': output,
                    'enabled': job.get('enabled', True),
                })

    return events


async def enhance_schedule_item_with_execution_history(item: Dict) -> Dict:
    """
    Take a schedule item and add execution history data to it
    """
    job_id = item.get('id')
    if not job_id:
        return item
    
    history = await read_job_execution_history(job_id)
    
    # Add execution history fields to the item
    item['lastRun'] = None
    item['lastDuration'] = None
    item['lastOutput'] = None
    item['recentRuns'] = []
    item['successRate7d'] = None
    item['totalRuns'] = 0
    
    if history['lastRun']:
        last_run = history['lastRun']
        item['lastRun'] = datetime.fromtimestamp(last_run.get('runAtMs', 0) / 1000).isoformat()
        item['lastDuration'] = last_run.get('durationMs', 0)
        item['lastOutput'] = last_run.get('summary') or last_run.get('error', '')
        item['recentRuns'] = [
            {
                'timestamp': datetime.fromtimestamp(r.get('runAtMs', 0) / 1000).isoformat(),
                'status': r.get('status'),
                'duration': r.get('durationMs')
            }
            for r in history['runs']
        ]
        item['successRate7d'] = history['successRate7d']
        item['totalRuns'] = history['totalRuns']
    
    return item

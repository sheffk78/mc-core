# Mission Control — Quick Start Reference

## URLs

| Service | URL |
|---------|-----|
| **Frontend (UI)** | `https://mc.agentictrust.app` |
| **Backend (API)** | `https://mission-control-production-c88a.up.railway.app` |
| **GitHub Repo** | `https://github.com/sheffk78/mission-control` |
| **Railway Dashboard** | https://railway.app (requires login) |

## Common API Calls

```bash
# Get weekly calendar view
curl 'https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly'

# Get all schedule items
curl 'https://mission-control-production-c88a.up.railway.app/api/v1/schedule'

# Get schedule for AgenticTrust brand only
curl 'https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly' | jq '.events | map(select(.brand == "agentictrust"))'

# Get job count by brand
curl 'https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly' | jq '.events | group_by(.brand) | map({brand: .[0].brand, count: length})'
```

## Deployment Checklist

### After Making Code Changes

1. **Commit to main:**
   ```bash
   git add .
   git commit -m "your message"
   git push origin main
   ```

2. **Railway auto-deploys** (wait 2-5 minutes)

3. **Verify:**
   ```bash
   # Test API
   curl https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly

   # Visit UI
   open https://mc.agentictrust.app
   ```

### If Changes Don't Show Up

```bash
# Force redeploy with dummy commit
echo "# Redeploy trigger - $(date)" >> .railway-trigger
git add .railway-trigger
git commit -m "chore: Trigger redeploy"
git push origin main
```

Or use Railway dashboard → "Redeploy" button.

## Seeding Schedule Data

### Step 1: Prepare
```python
# Use /tmp/final_reseed.py pattern:
# - Extract brand from job name (strict rules)
# - Exclude: qmd-*, firecrawl-*, email-*, test-*, etc.
# - Result: 25 clean jobs (19 agentictrust, 6 trustoffice)
```

### Step 2: Delete Old Data
Via Railway MongoDB console:
```javascript
db.schedule.deleteMany({})
```

### Step 3: Seed New Data
```bash
python3 /path/to/reseed_script.py
```

### Step 4: Verify
```bash
curl 'https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly' | \
  jq '.events | group_by(.brand) | map({brand: .[0].brand, count: length})'
```

Expected: `agentictrust: 267, trustoffice: 42` (or similar 7-day spread)

## File Locations

```
mission-control/
├── backend/                    # Python FastAPI server
│   ├── server.py              # Entry point
│   ├── routes/schedule.py     # Schedule endpoints
│   └── execution_history.py   # Cron parsing + weekly schedule logic
├── frontend/                   # React app
│   └── src/components/
│       ├── ScheduleView.js    # Schedule page layout
│       ├── WeeklyCalendar.jsx # Calendar grid
│       └── JobBlock.jsx       # Job block styling
├── DEPLOYMENT-GUIDE.md        # Full deployment docs
└── QUICK-START.md            # This file
```

## Making Common Changes

### Change job block colors (status)
**File:** `frontend/src/components/JobBlock.jsx`
```javascript
const STATUS_CONFIG = {
  success: { bgColor: "#d4edda", ... },    // Green
  failed: { bgColor: "#f8d7da", ... },     // Red
  running: { bgColor: "#fff3cd", ... },    // Yellow
  scheduled: { bgColor: "#e2e3e5", ... },  // Gray
};
```

### Limit job name width
**File:** `frontend/src/styles/calendar.css`
```css
.job-name {
  max-width: 80px;  /* Adjust this value */
  overflow: hidden;
  text-overflow: ellipsis;
}
```

### Change which jobs appear
**File:** Use Python reseed script to filter by brand and exclusion patterns.

## Brand Assignment Rules

```
✅ Include:
- Jobs with "trustoffice" in name → trustoffice brand
- Jobs with "agentictrust" in name → agentictrust brand
- Jobs starting with "WF-" → agentictrust brand (workflows)

❌ Exclude:
- qmd-* (index operations)
- firecrawl-* (internal)
- email-* (internal)
- *-test or test-* (test jobs)
- slack-check (internal)
- mempalace-*, graphify-* (internal)
```

## Debugging

### API not responding
```bash
# Check if backend is running
curl -I https://mission-control-production-c88a.up.railway.app/api/v1/schedule

# Check Railway logs
# → Go to Railway dashboard, click Backend service, view logs
```

### Frontend shows wrong data
```bash
# Clear browser cache and reload
# Or: Open dev console (F12) and check Network tab
# Verify REACT_APP_BACKEND_URL points to correct backend
```

### Database has old/duplicate entries
```javascript
// Via Railway MongoDB console
db.schedule.deleteMany({})  // Start fresh
// Then reseed with correct data
```

## Support

- **Full docs:** See `DEPLOYMENT-GUIDE.md`
- **GitHub:** `https://github.com/sheffk78/mission-control`
- **Railway status:** Check dashboard for build logs and errors

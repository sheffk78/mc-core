# Mission Control — Deployment & Architecture Guide

**Last Updated:** April 10, 2026  
**Status:** Production on Railway

---

## Architecture Overview

Mission Control runs as **two separate Railway services** deployed from the same GitHub repository (`sheffk78/mission-control`).

### Service 1: Backend (Python FastAPI)

| Property | Value |
|----------|-------|
| **Stack** | Python 3.13 + FastAPI + Uvicorn + Motor (async MongoDB) |
| **Directory** | `backend/` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
| **Production URL** | `https://mission-control-production-c88a.up.railway.app` |
| **API Routes** | All `/api/v1/*` endpoints |
| **Database** | MongoDB Atlas (async via Motor driver) |
| **WebSocket** | Real-time schedule updates |

### Service 2: Frontend (React 19)

| Property | Value |
|----------|-------|
| **Stack** | React 19 + ShadcnUI + Tailwind CSS |
| **Directory** | `frontend/` |
| **Build Command** | `npm install --legacy-peer-deps && npm run build` |
| **Start Command** | `npx serve -s build -l $PORT` |
| **Public Domain** | `https://mc.agentictrust.app` |
| **Backend Reference** | Environment variable `REACT_APP_BACKEND_URL=https://mission-control-production-c88a.up.railway.app` |
| **Behavior** | React SPA — serves `index.html` for any unknown route (standard React Router behavior) |

---

## Critical Networking Detail

**⚠️ THE #1 MISTAKE: Hitting the frontend domain for API calls**

```bash
# ❌ WRONG — Returns React index.html (404 handling)
curl https://mc.agentictrust.app/api/v1/schedule

# ✅ CORRECT — Backend URL
curl https://mission-control-production-c88a.up.railway.app/api/v1/schedule
```

**Why:** The frontend service (`mc.agentictrust.app`) is a React SPA. Any route it doesn't recognize returns `index.html` (standard SPA behavior). The actual API lives on the backend service at the Railway production URL.

**For frontend code:** The React app uses the `REACT_APP_BACKEND_URL` environment variable to know where to fetch from.

---

## API Endpoints Reference

All endpoints are at: `https://mission-control-production-c88a.up.railway.app/api/v1/`

### Schedule Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/schedule` | List all schedule items (from database) |
| `GET` | `/schedule/weekly?week_offset=0` | Get calendar view for a specific week |
| `GET` | `/schedule/{job_id}` | Get single schedule item details |
| `POST` | `/schedule` | Create new schedule item |
| `PATCH` | `/schedule/{job_id}` | Update schedule item |

### Weekly Calendar Endpoint

```bash
curl 'https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly'

# Returns:
{
  "weekStart": "2026-04-06",
  "weekEnd": "2026-04-12",
  "events": [
    {
      "jobId": "...",
      "jobName": "...",
      "brand": "trustoffice",  # or "agentictrust"
      "cron": "0 6 * * *",
      "date": "2026-04-06",
      "hour": 6,
      "minute": 0,
      "status": "scheduled",  # or "success", "failed", "running"
      "lastRun": null,
      "duration": null,
      ...
    }
  ]
}
```

---

## Deployment Workflow

### How Changes Deploy

1. **Commit to `main` branch** in GitHub (`sheffk78/mission-control`)
2. **Railway detects the push** via webhook (automatic)
3. **Railway rebuilds both services:**
   - **Backend:** Runs `pip install` + starts uvicorn
   - **Frontend:** Runs `npm install --legacy-peer-deps && npm run build` + starts serve
4. **Deployment takes 2-5 minutes** depending on build size

### Triggering a Redeploy

If Railway doesn't detect a push, you can force a redeploy:

**Option 1: Make a dummy commit**
```bash
cd mission-control
echo "# Redeploy trigger - $(date)" >> .railway-trigger
git add .railway-trigger
git commit -m "chore: Trigger Railway redeploy"
git push origin main
```

**Option 2: Railway Console**
- Log into Railway dashboard
- Navigate to the service (Backend or Frontend)
- Click "Redeploy" button

### Checking Deployment Status

- **Railway Console:** Shows build logs and current deployment status
- **Test the API:** `curl https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly`
- **Test the UI:** Visit `https://mc.agentictrust.app` in browser

---

## Database Architecture

### Data Sources

**Schedule items** can come from two places:

1. **MongoDB Collection (`schedule`)** — Primary source when populated
2. **Filesystem (`~/.openclaw/cron/jobs.json`)** — Fallback if database is empty

### The Challenge: Database Seeding

When you want to populate the calendar with cron jobs:

1. **Read cron jobs** from `~/.openclaw/cron/jobs.json` (local machine)
2. **POST to API** to create schedule items in database
3. **Railway backend reads from MongoDB** to serve the calendar

**Problem:** Old entries accumulate. If you seed multiple times, you get duplicates.

**Solution:** Before reseeding, delete all old schedule items from MongoDB:

```bash
# Via Railway MongoDB console or admin panel
# Delete all documents in the schedule collection
db.schedule.deleteMany({})
```

Then reseed with correct data.

---

## Cron Job Brand Assignment

**Rules for proper brand assignment:**

```python
def extract_brand(job_name):
    """Strict brand extraction"""
    name_lower = job_name.lower()
    
    # Explicit matches take priority
    if 'trustoffice' in name_lower:
        return 'trustoffice'
    
    if 'agentictrust' in name_lower:
        return 'agentictrust'
    
    # WF- prefix jobs are AgenticTrust Workflows
    if name_lower.startswith('wf-'):
        return 'agentictrust'
    
    # Everything else: skip
    return None
```

**Jobs to always EXCLUDE:**
- `qmd-*` (index operations)
- `firecrawl-*` (internal)
- `slack-check` (internal)
- `*-test` or `test-*` (test jobs)
- `email-*` (internal email operations)
- `mempalace-*` (internal)
- `graphify-*` (internal)

---

## Making Changes to Mission Control

### Backend Changes (Python)

**File structure:**
```
backend/
├── server.py              # FastAPI app initialization
├── db.py                  # MongoDB connection + session management
├── models.py              # Pydantic models (ScheduleItem, etc.)
├── routes/
│   ├── schedule.py        # Schedule endpoints
│   ├── tasks.py           # Task endpoints
│   └── approvals.py       # Approval endpoints
├── execution_history.py   # Cron job parsing + weekly schedule generation
├── seed.py                # Database seeding
└── requirements.txt       # Python dependencies
```

**To add a new endpoint:**
1. Create a route function in the appropriate file under `routes/`
2. Add `@router.get()`, `@router.post()`, etc. decorator
3. Register the router in `server.py`: `api_router.include_router(schedule_router)`
4. Test locally: `uvicorn backend:app --reload`
5. Commit and push to main

**Important:** The backend uses async/await throughout. Use `async def` for all route handlers.

### Frontend Changes (React)

**File structure:**
```
frontend/
├── src/
│   ├── App.js             # Main app component
│   ├── App.css            # Global styles + brand colors
│   ├── components/
│   │   ├── ScheduleView.js     # Schedule page
│   │   ├── WeeklyCalendar.jsx  # Calendar grid
│   │   ├── JobBlock.jsx        # Individual job block
│   │   ├── Sidebar.js          # Brand filter sidebar
│   │   └── ...
│   ├── lib/
│   │   ├── api.js         # API client functions
│   │   └── brands.js      # Brand utilities
│   └── styles/
│       └── calendar.css   # Calendar-specific styles
├── package.json           # Dependencies
└── public/
    └── index.html         # HTML entry point
```

**API client pattern:**
```javascript
// lib/api.js
export async function fetchWeeklySchedule(weekOffset = 0) {
  const response = await fetch(
    `${process.env.REACT_APP_BACKEND_URL}/api/v1/schedule/weekly?week_offset=${weekOffset}`
  );
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}
```

**To modify the calendar display:**
1. Update `WeeklyCalendar.jsx` for layout logic
2. Update `JobBlock.jsx` for individual job styling
3. Update `calendar.css` for styling
4. Run `npm start` to test locally
5. Build and push: `git commit && git push origin main`

### Common Changes

**Change job block colors (status indicators):**
- Edit `JobBlock.jsx` — `STATUS_CONFIG` object defines colors
- Green = success, red = failed, yellow = running, gray = scheduled
- Each status maps to `bgColor`, `borderColor`, `textColor`

**Change how jobs are filtered by brand:**
- Edit `WeeklyCalendar.jsx` — the `filteredEvents` computation
- Currently filters based on the `brand` prop passed from ScheduleView

**Limit text width in calendar:**
- Edit `calendar.css` — `.job-name { max-width: 80px; }`
- Adjust the `80px` to fit your layout

---

## Troubleshooting

### Issue: API returns HTML instead of JSON

**Cause:** You're hitting the frontend URL instead of the backend URL.

**Fix:**
```bash
# Wrong
curl https://mc.agentictrust.app/api/v1/schedule

# Right
curl https://mission-control-production-c88a.up.railway.app/api/v1/schedule
```

### Issue: Changes don't show up after pushing

**Cause:** Railway hasn't redeployed yet, or the build failed.

**Solutions:**
1. Wait 2-5 minutes for automatic redeploy
2. Check Railway console for build errors
3. Force redeploy with dummy commit (see Deployment Workflow section)
4. Check git status: `git log --oneline -5` to verify commit is on main

### Issue: Brand filtering shows wrong jobs

**Cause:** Old database entries with wrong brands haven't been deleted.

**Fix:**
1. Delete all schedule items from MongoDB (via Railway console)
2. Reseed with correct brand assignments (use the strict rules above)
3. Verify with: `curl https://mission-control-production-c88a.up.railway.app/api/v1/schedule/weekly | jq '.events | group_by(.brand)'`

### Issue: Text overflows in calendar cells

**Cause:** Job names are too long for the column width.

**Fix:** Edit `calendar.css` and reduce `max-width` on `.job-name`, or increase cell width by reducing cell padding.

---

## Environment Variables

### Backend (Railway environment)

```bash
# MongoDB connection (Railway provides this)
MONGODB_URL=...

# Python path
PYTHONUNBUFFERED=1

# Port (Railway sets this)
PORT=8080
```

### Frontend (Railway environment)

```bash
# Backend API URL (critical — must point to backend service)
REACT_APP_BACKEND_URL=https://mission-control-production-c88a.up.railway.app

# Port (Railway sets this)
PORT=3000
```

If you need to test locally:
```bash
# .env.local in frontend/
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## Git Workflow

**Main branch is always production.** Every commit to `main` triggers a Railway redeploy.

```bash
# Standard workflow
git checkout -b feature/new-schedule-view
# ... make changes ...
git add .
git commit -m "feat: Add brand-based filtering to schedule"
git push origin feature/new-schedule-view
# Open PR, get review, merge to main
# Railway auto-deploys

# For testing before merge
cd mission-control
npm run dev          # Frontend local (reads REACT_APP_BACKEND_URL)
cd backend
uvicorn server:app --reload  # Backend local
```

---

## Performance Notes

- **Weekly calendar generation:** Takes ~100ms for 25 jobs × 7 days = 175 events
- **Database queries:** MongoDB Atlas is fast for small collections (<10k items)
- **Frontend load:** React SPA loads in <2s on decent connection
- **Real-time updates:** WebSocket broadcasts every 30 seconds (configurable)

---

## Future Improvements

1. **Direct database deletion endpoint** — Add `DELETE /schedule/all` for cleanup
2. **Migration tool** — Automatically map old schedule entries to new brands
3. **Backup/restore** — Export schedule collection to JSON for safekeeping
4. **Rate limiting** — Add to prevent accidental duplicate seeding
5. **Audit log** — Track who changed what and when in the schedule

---

## Key Takeaways

1. **Two separate services:** Backend (API) and Frontend (UI)
2. **Use backend URL for API calls:** `mission-control-production-c88a.up.railway.app`
3. **Git push to main = auto-redeploy** on Railway (2-5 min)
4. **Database seeding:** Delete old entries before reseeding to avoid duplicates
5. **Brand assignment:** Strict rules prevent contamination (agentictrust in name = agentictrust brand)
6. **Cron jobs need filtering:** Exclude internal/test jobs, keep only business workflows

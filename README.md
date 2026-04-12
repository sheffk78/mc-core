# Mission Control v2

Real-time operations dashboard for managing brands, tasks, approvals, costs, revenue, and activities. Built with **Hono** (server) + **React** (frontend) + **Bun** (runtime) + **SQLite** (database).

## Architecture

```
mission-control-v2/
├── server/              # Hono API server (Bun)
│   ├── src/
│   │   └── index.ts     # Entry point — Hono app, routes, static serving
│   ├── routes/          # API route handlers (brands, tasks, approvals, etc.)
│   ├── middleware/       # Auth middleware (token-based)
│   ├── db/              # Drizzle ORM schema + connection
│   ├── ws.ts            # WebSocket handler for real-time updates
│   └── scripts/         # Utility scripts (migrate, seed, backup)
├── web/                 # React SPA (Vite + Tailwind)
│   ├── src/
│   ├── index.html
│   └── vite.config.ts
├── Dockerfile           # Multi-stage Docker build
├── railway.json         # Railway deployment config
└── package.json         # Root workspace config
```

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Runtime   | Bun                                 |
| Server    | Hono (with Bun adapter)             |
| Database  | SQLite via better-sqlite3 + Drizzle |
| Frontend  | React 19, Vite 6, Tailwind 3       |
| Realtime  | WebSocket (Hono/Bun native)         |
| Deploy    | Railway (Docker)                    |

## Quick Start

### Prerequisites

- **Bun** >= 1.3.0 — `curl -fsSL https://bun.sh/install | bash`

### Setup

```bash
# Clone and enter the project
cd mission-control-v2

# Copy environment config
cp .env.example .env
# Edit .env with your values (MC_AUTH_TOKEN, etc.)

# Install dependencies (workspaces)
bun install

# Run database migrations
bun run migrate

# Seed initial data (optional)
bun run seed
```

### Development

```bash
# Start both server and web dev servers
bun run dev

# Or start individually:
bun run --filter server dev    # Server with hot-reload on :3000
bun run --filter web dev       # Vite dev server on :5173
```

### Build

```bash
# Build everything (web + server)
bun run build

# Start production server
bun server/dist/index.js
```

## API

All API routes are prefixed with `/api/v1/` and require authentication via `Authorization: Bearer <MC_AUTH_TOKEN>` header.

| Endpoint             | Methods                  | Description           |
|----------------------|--------------------------|-----------------------|
| `/api/v1/brands`     | GET, POST                | Brand management      |
| `/api/v1/tasks`      | GET, POST, PATCH         | Task tracking         |
| `/api/v1/approvals`  | GET, POST, PATCH         | Approval workflows    |
| `/api/v1/activities` | GET, POST                | Activity log          |
| `/api/v1/costs`      | GET, POST                | Cost tracking         |
| `/api/v1/stats`      | GET                      | Dashboard statistics  |
| `/api/v1/revenue`    | GET, POST                | Revenue metrics       |

### Health Check

```
GET /health  (no auth required)
```

Returns server status, uptime, and connected WebSocket client count.

### WebSocket

Connect to `/ws` for real-time updates. Server broadcasts task changes, approval updates, and activity events to all connected clients.

## Database

SQLite database stored at `DB_PATH` (default: `./data/mc.db`). Schema managed with Drizzle ORM.

```bash
# Generate migration from schema changes
bunx drizzle-kit generate

# Run migrations
bun run migrate
```

## Backup

```bash
# Create a timestamped backup of mc.db
bun run server/scripts/backup.ts

# Backup to custom directory
bun run server/scripts/backup.ts /path/to/backups
```

Backups older than 30 days are automatically pruned.

## Deployment (Railway)

The project deploys to Railway via Docker. The `Dockerfile` uses a multi-stage build:

1. **Builder stage** — Installs deps, builds web (Vite), builds server (Bun)
2. **Production stage** — Copies dist + production node_modules, exposes port 3000

Health check is configured at `/health`.

### Environment Variables

| Variable          | Required | Default         | Description                          |
|-------------------|----------|-----------------|--------------------------------------|
| `MC_AUTH_TOKEN`   | ✅       | —               | Bearer token for API authentication  |
| `PORT`            | ❌       | `3000`          | Server port                          |
| `FRONTEND_URL`    | ❌       | `localhost:3000`| CORS allowed origin                  |
| `NODE_ENV`        | ❌       | `development`   | Environment mode                     |
| `DB_PATH`         | ❌       | `./data/mc.db`  | SQLite database file path            |

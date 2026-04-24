# ---- Stage 1: Build ----
FROM oven/bun:1.2-alpine AS builder

ARG CACHE_BUST=1

WORKDIR /app

# Copy root workspace config
COPY package.json bun.lockb* ./

# Copy workspace package.json files
COPY server/package.json server/
COPY web/package.json web/

# Install all dependencies (workspaces)
RUN bun install --frozen-lockfile || bun install

# Copy source code
COPY server/ server/
COPY web/ web/
COPY drizzle.config.ts* ./
COPY tsconfig.base.json* ./

# Build web frontend (Vite)
RUN cd web && bun run build

# Build server (Bun bundler)
RUN cd server && bun run build

# ---- Stage 2: Production ----
FROM oven/bun:1.2-alpine AS production

WORKDIR /app

# Copy root package.json and lockfile for install
COPY package.json bun.lockb* ./

# Copy workspace package.json files
COPY server/package.json server/
COPY web/package.json web/

# Install production dependencies only
RUN bun install --frozen-lockfile --production || bun install --production

# Copy built server from builder
COPY --from=builder /app/server/dist server/dist

# Copy built web frontend from builder
COPY --from=builder /app/web/dist web/dist

# Copy migration/init scripts from builder
COPY --from=builder /app/server/scripts server/scripts

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

# Initialize DB (creates tables if missing, safe for volumes) then start server
CMD ["sh", "-c", "bun server/scripts/init-db.ts && bun server/dist/index.js"]

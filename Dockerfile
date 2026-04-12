# ---- Stage 1: Build ----
FROM oven/bun:1.2-alpine AS builder

WORKDIR /app

# Copy root workspace config
COPY package.json bun.lockb* ./

# Copy workspace package.json files
COPY server/package.json server/
COPY web/package.json web/

# Copy tsconfig files
COPY tsconfig.base.json ./

# Install all dependencies (workspaces)
RUN bun install --frozen-lockfile || bun install

# Copy source code
COPY server/ server/
COPY web/ web/
COPY drizzle.config.ts* ./

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

# Copy any static assets or migration files if present
COPY --from=builder /app/server/scripts server/scripts 2>/dev/null || true

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["bun", "server/dist/index.js"]

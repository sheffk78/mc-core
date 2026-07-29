# Railway Deploy — Quick Reference

## 🚀 Quick Start

### Deploy from Local Dockerfile (No GitHub Required)

```bash
# Set your Railway token
export RAILWAY_TOKEN="your_token"

# Deploy backend
python3 skills/railway-deploy/deploy_service.py \
  --project-id "PROJECT_ID" \
  --service-name "my-backend" \
  --dockerfile-path "backend/Dockerfile" \
  --env-file "backend/.env" \
  --postgres-service-id "POSTGRES_SERVICE_ID"

# Deploy frontend
python3 skills/railway-deploy/deploy_service.py \
  --project-id "PROJECT_ID" \
  --service-name "my-frontend" \
  --dockerfile-path "frontend/Dockerfile" \
  --env-file "frontend/.env" \
  --postgres-service-id "POSTGRES_SERVICE_ID"
```

### Deploy from GitHub (Auto-Deploy Enabled)

```bash
export RAILWAY_TOKEN="your_token"

# Deploy backend with auto-deploy
python3 skills/railway-deploy/deploy_service.py \
  --project-id "PROJECT_ID" \
  --service-name "backend" \
  --github-repo "org/backend" \
  --dockerfile-path "backend/Dockerfile" \
  --auto-deploy \
  --env-vars "PYTHONUNBUFFERED=1"

# Deploy frontend with auto-deploy
python3 skills/railway-deploy/deploy_service.py \
  --project-id "PROJECT_ID" \
  --service-name "frontend" \
  --github-repo "org/frontend" \
  --nixpacks-config "frontend/nixpacks.toml" \
  --auto-deploy \
  --env-vars "NEXT_PUBLIC_API_URL=https://backend.up.railway.app"
```

---

## ⚠️ Important Notes

### Hard Model Gate
- **DeepSeek V4 Pro or GPT-5.5 ONLY** for Railway GraphQL operations
- Use Python scripts for GraphQL (not bash)
- Model-specific errors occur with lower-intel models

### Environment Variables
- After setting env vars with `variableUpsert`, you **MUST trigger a redeploy**
- Use `git commit --allow-empty && git push` or `serviceInstanceDeployV2`
- DATABASE_URL uses variableRefs: `${{Postgres.DATABASE_URL}}`

### GitHub Repo Prerequisite
- Before enabling auto-deploy, verify GitHub repo is connected
- Check `upstreamUrl` with `railway services`
- If `upstreamUrl` is null, connect via `githubRepoUpdate` or `serviceConnect`

### Dockerfile CMD Pattern
```dockerfile
# ✅ CORRECT (required for Railway)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### CRA nixpacks.toml
```toml
[phases.setup]
nixPkgs = ["nodejs-18_x", "npm-9_x"]

[phases.install]
cmds = ["npm install --legacy-peer-deps"]

[phases.build]
cmds = ["npm run build"]

[start]
cmd = "npx serve -s build -l ${PORT:-3000}"
```

---

## 📋 Prerequisite Checklist

Before deploying, verify:

- [ ] GitHub repos exist and are pushed to `main`
- [ ] Railway project exists with Postgres service
- [ ] Environment IDs are available
- [ ] All required files exist (Dockerfile, nixpacks.toml, requirements.txt, etc.)
- [ ] `RAILWAY_TOKEN` environment variable is set
- [ ] Dockerfile uses `sh -c` pattern for CMD
- [ ] CRA uses explicit `nixPkgs` in nixpacks.toml

---

## 🔧 Troubleshooting

### Service creation fails with null result
- Verify project ID and service name are correct
- Check Railway token is valid
- Ensure required fields (projectId, environmentId) are in mutation input

### $PORT not expanding in Dockerfile
- Use exec form `[`...`]` not shell form `"..."`
- Use `sh -c` for command execution
- Use `${PORT:-8000}` for default value

### Environment variables not taking effect
- Trigger a redeploy after setting variables
- Push a commit or use `serviceInstanceDeployV2`

### Auto-deploy not triggering
- Check `upstreamUrl` is not null
- Connect GitHub repo via `githubRepoUpdate`
- Enable auto-deploy via `serviceInstanceAutoDeployUpdate`

### Database connection fails
- Verify `DATABASE_URL` uses variableRefs: `${{Postgres.DATABASE_URL}}`
- Check PostgreSQL service is running
- Verify environment names match (PRODUCTION vs STAGING)

---

## 📚 More Information

- **Complete Documentation:** See SKILL.md
- **StenoDesk Post-Mortem:** `archive/2026-07-29-cleanup/StenoDesk-migration-post-mortem.md`
- **Branding Templates:** `/skills/templates/BRAND-OS-STRUCTURE.md`
- **Asset Migration:** `/skills/brand-asset-migration/SKILL.md`

---

## 🛠️ Scripts

### deploy_service.py
Complete end-to-end deployment script with Dockerfile/nixpacks support.

```bash
python3 skills/railway-deploy/deploy_service.py --help
```

### introspect_schema.py
Query Railway GraphQL schema to discover available mutations and types.

```bash
export RAILWAY_TOKEN="your_token"
python3 skills/railway-deploy/introspect_schema.py
```
# TOOLS/railway-deploy.md

Full Railway deployment guide, project IDs, and auth debugging. Also see `skills/railway-deploy/SKILL.md`.

## Auth

- **Token:** `~/.hermes/secrets/railway-token.txt` — works for ALL projects (TrustOffice, WingPoint, TJB, AeriusView, TrustMinutes)
- Read from file: `TOKEN=$(cat ~/.hermes/secrets/railway-token.txt | tr -d '\n')`
- Never assume `RAILWAY_API_TOKEN` in env. Never ask Jeff for the token.
- **Smoke test:** `curl -s -X POST $API -H "Authorization: Bearer $TOKEN" -d '{"query":"query { me { id email } }"}'` (NOT `{ projects { ... } }` — returns `[]` due to schema changes)

## ⚠️ Railway CLI v4.44+ does NOT work in headless mode

`railway login --token` doesn't exist, `--browserless` fails, config parser loops. Do NOT use CLI for automation.

## What to use instead

| Operation | Method |
|---|---|
| **Deploys** | Git push (if repo connected) OR GraphQL `serviceInstanceDeployV2` |
| **Env vars** | GraphQL `variableUpsert` |
| **Logs** | GraphQL `buildLogs` / `deploymentLogs` |
| **Domains** | GraphQL `customDomainCreate` + `customDomain` queries |

## API endpoint

```
https://backboard.railway.app/graphql/v2
```

## Key project IDs

See `skills/railway-deploy/SKILL.md` for the full project ID reference.
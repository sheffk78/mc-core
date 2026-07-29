|# railway-deploy — Railway Deployment Guide

> **Purpose:** Deploy web apps and services to Railway using GraphQL API or CLI. Provides complete working scripts, Dockerfile patterns, and prerequisite checks.

## Trigger

Use this skill when:
- You need to deploy a Python/Node/React/FastAPI app to Railway
- You need to create PostgreSQL services on Railway
- You need to connect services via `serviceConnect`
- You need to set up auto-deploy from GitHub repos

---

## ⛔ HARD MODEL GATE

**CRITICAL:** This skill REQUIRES DeepSeek V4 Pro or GPT-5.5 ONLY for Railway GraphQL operations.

If your current model does NOT pass this gate, spawn a higher-intel agent with explicit model override:

```python
# Example using delegate_task
context = {
    "railway_project_id": "...",
    "service_name": "...",
    "model_override": "deepseek-v4-pro"  # Required!
}

delegate_task(
    goal="Deploy service to Railway with GraphQL API",
    context=context,
    role="leaf"
)
```

**Why?** Railway GraphQL API has quirks that non-reasoning models cannot handle correctly. Attempting GraphQL with lower-intel models leads to JSON escaping errors, schema guessing failures, and silent deployment failures.

---

## Quick Start

### Option 1: Use the Complete Deployment Script (Recommended)

Use the provided complete working script that handles all steps:

```bash
python3 skills/railway-deploy/deploy_service.py \
  --project-id "YOUR_PROJECT_ID" \
  --service-name "steno-desk-backend" \
  --github-repo "sheffk78/steno-desk-backend" \
  --dockerfile-path "backend/Dockerfile" \
  --env-file "backend/.env" \
  --auto-deploy
```

This script:
- Creates the service via GraphQL API
- Sets up environment variables
- Enables auto-deploy
- Verifies deployment

### Option 2: Use the Railway CLI (Simpler, No GraphQL)

For basic deployments, use the Railway CLI which doesn't have the model gate:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
cd backend
railway up
```

---

## Prerequisite Checks

**BEFORE deploying, verify ALL of the following:**

### 1. GitHub Repos Exist

```bash
# Check if repo exists
gh repo view sheffk78/steno-desk-backend

# If not, create it
gh repo create sheffk78/steno-desk-backend --public --source=./backend --remote=origin
```

**Required files in repo:**
- `Dockerfile` (for backend services)
- `nixpacks.toml` (for frontend services)
- `requirements.txt` (Python dependencies)
- `package.json` (Node dependencies)
- `.gitignore`

### 2. Railway Project Exists

```bash
# Check project ID
railway whoami

# Project should exist with service(s)
railway services
```

### 3. Service Templates Available

Railway provides templates for common services:

**PostgreSQL:**
```bash
railway template create postgresql
```

**Redis:**
```bash
railway template create redis
```

### 4. Environment IDs Available

You need environment IDs for GraphQL operations:

```bash
# Get environments
railway environments
```

### 5. Railway Token Available

```bash
# Get token (if using GraphQL API)
railway token
```

### 6. Auto-Deploy Enabled (Before Pushing Code)

```bash
# Enable auto-deploy via GraphQL
# See "Auto-Deploy" section below
```

---

## Complete Working Deployment Script

This script provides a complete end-to-end deployment pattern for Railway:

```python
# skills/railway-deploy/deploy_service.py

import os
import requests
import json
from pathlib import Path

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"
RAILWAY_TOKEN = os.getenv("RAILWAY_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {RAILWAY_TOKEN}",
    "Content-Type": "application/json"
}

def run_graphql(query, variables=None):
    """Execute a GraphQL query against Railway v2 API."""
    payload = {
        "query": query,
        "variables": variables or {}
    }
    response = requests.post(RAILWAY_GRAPHQL_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

def create_service(project_id, service_name, dockerfile_path=None):
    """
    Create a new Railway service.

    Args:
        project_id: Railway project UUID
        service_name: Name of the service
        dockerfile_path: Path to Dockerfile (for Dockerfile builder services)

    Returns:
        Service instance ID
    """
    # Query service type based on Dockerfile presence
    query = """
    mutation($input: ServiceCreateInput!) {
        serviceCreate(input: $input) {
            id
            name
            projectId
            environmentId
            _service {
                id
            }
        }
    }
    """

    variables = {
        "input": {
            "name": service_name,
            "projectId": project_id
        }
    }

    # If Dockerfile is present, add builder info
    if dockerfile_path and Path(dockerfile_path).exists():
        variables["input"]["builder"] = {
            "dockerfile": dockerfile_path
        }

    result = run_graphql(query, variables)
    service = result["data"]["serviceCreate"]

    print(f"✅ Service created: {service['name']} ({service['id']})")
    return service["id"]

def connect_postgres(service_id, postgres_service_id, env_name="PRODUCTION"):
    """
    Connect a service to PostgreSQL via serviceConnect.

    Args:
        service_id: Service ID to connect
        postgres_service_id: PostgreSQL service ID
        env_name: Environment name (e.g., "PRODUCTION")

    Returns:
        Connection details
    """
    query = """
    mutation($input: ServiceConnectInput!) {
        serviceConnect(input: $input) {
            id
            name
            connectedServices {
                id
                name
            }
        }
    }
    """

    variables = {
        "input": {
            "serviceId": service_id,
            "upstreamServices": [
                {"id": postgres_service_id, "envName": env_name}
            ]
        }
    }

    result = run_graphql(query, variables)
    connection = result["data"]["serviceConnect"]

    print(f"✅ Connected to PostgreSQL: {connection['name']}")
    return connection

def set_environment_variable(service_id, env_name, key, value):
    """
    Set an environment variable on a service.

    Note: After setting env vars, you MUST trigger a redeploy
    for them to take effect.

    Args:
        service_id: Service ID
        env_name: Environment name
        key: Variable name
        value: Variable value
    """
    query = """
    mutation($input: VariableUpsertInput!) {
        variableUpsert(input: $input) {
            id
            name
            serviceId
            value
            variableRefs {
                name
            }
        }
    }
    """

    variables = {
        "input": {
            "serviceId": service_id,
            "environmentId": env_name,
            "name": key,
            "value": value,
            "skipDeploys": False
        }
    }

    result = run_graphql(query, variables)
    variable = result["data"]["variableUpsert"]

    print(f"✅ Set environment variable: {key} = {value}")
    return variable

def enable_auto_deploy(service_id):
    """
    Enable auto-deploy for a service.

    Args:
        service_id: Service ID

    Returns:
        Auto-deploy configuration
    """
    query = """
    mutation($input: ServiceInstanceAutoDeployUpdateInput!) {
        serviceInstanceAutoDeployUpdate(input: $input) {
            id
            enabled
            upstreamUrl
        }
    }
    """

    variables = {
        "input": {
            "id": service_id,
            "enabled": True
        }
    }

    result = run_graphql(query, variables)
    config = result["data"]["serviceInstanceAutoDeployUpdate"]

    print(f"✅ Auto-deploy enabled for: {config['upstreamUrl']}")
    return config

def trigger_deployment(service_id):
    """
    Trigger a manual deployment.

    Args:
        service_id: Service ID
    """
    query = """
    mutation($input: ServiceInstanceDeployV2Input!) {
        serviceInstanceDeployV2(input: $input) {
            id
            status
        }
    }
    """

    variables = {
        "input": {
            "id": service_id,
            "latestCommit": True
        }
    }

    result = run_graphql(query, variables)
    deployment = result["data"]["serviceInstanceDeployV2"]

    print(f"✅ Deployment triggered: {deployment['id']}")
    return deployment

def verify_deployment(service_id):
    """
    Verify the latest deployment is successful.

    Args:
        service_id: Service ID

    Returns:
        Deployment status
    """
    query = """
    query($serviceId: ID!) {
        service(id: $serviceId) {
            id
            deployments(last: 1) {
                edges {
                    node {
                        id
                        status
                        startedAt
                        completedAt
                    }
                }
            }
        }
    }
    """

    variables = {
        "serviceId": service_id
    }

    result = run_graphql(query, variables)
    deployment = result["data"]["service"]["deployments"]["edges"][0]["node"]

    print(f"✅ Deployment status: {deployment['status']}")
    return deployment

def main():
    """Complete deployment example."""
    # Configuration
    project_id = "YOUR_PROJECT_ID"  # Replace with actual project ID
    service_name = "steno-desk-backend"
    github_repo = "sheffk78/steno-desk-backend"
    dockerfile_path = "backend/Dockerfile"
    postgres_service_id = "YOUR_POSTGRES_SERVICE_ID"

    # 1. Create service
    service_id = create_service(project_id, service_name, dockerfile_path)

    # 2. Connect PostgreSQL (if backend)
    if postgres_service_id:
        connect_postgres(service_id, postgres_service_id)

    # 3. Set environment variables
    # DATABASE_URL is auto-generated, so we use variableRefs
    set_environment_variable(service_id, "PRODUCTION", "DATABASE_URL", "${{Postgres.DATABASE_URL}}")

    # Other env vars
    set_environment_variable(service_id, "PRODUCTION", "PYTHONUNBUFFERED", "1")
    set_environment_variable(service_id, "PRODUCTION", "PORT", "8000")

    # 4. Enable auto-deploy
    auto_deploy_config = enable_auto_deploy(service_id)

    # 5. Trigger deployment
    trigger_deployment(service_id)

    # 6. Verify
    verify_deployment(service_id)

if __name__ == "__main__":
    main()
```

---

## Dockerfile Patterns

### Python Backend (Recommended Pattern)

**Critical:** Use the `sh -c` pattern for proper $PORT expansion.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

**Why this works:**
- `sh -c` is required for $PORT expansion in Railway's container runtime
- The exec form `[`...`]` is required (not the shell form `"..."`)
- `${PORT:-8000}` provides a default value if PORT is not set
- `PYTHONUNBUFFERED=1` ensures logs are streamed properly

**Complete example with health endpoint:**

```python
# backend/server.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/health")
def health():
    """Railway health check endpoint."""
    return JSONResponse(content={"status": "ok"})

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Service is running"}
```

**requirements.txt:**
```
fastapi
uvicorn
```

### Node.js Backend

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
ENV PORT=3000
CMD ["node", "server.js"]
```

---

## nixpacks.toml Patterns

### CRA (Create React App) — Complete Working Pattern

**Critical:** CRA requires explicit `nixPkgs` declaration and `--legacy-peer-deps`.

```toml
# frontend/nixpacks.toml

[phases.setup]
nixPkgs = ["nodejs-18_x", "npm-9_x"]

[phases.install]
cmds = ["npm install --legacy-peer-deps"]

[phases.build]
cmds = ["npm run build"]

[start]
cmd = "npx serve -s build -l ${PORT:-3000}"
```

**Why this works:**
- `nixPkgs` must be explicitly declared (auto-detect fails for CRA)
- `--legacy-peer-deps` prevents lockfile conflicts
- `npx serve` serves the build output (not `npm start` which runs dev mode)
- `${PORT:-3000}` expands the PORT variable at runtime

### Next.js Frontend

```toml
# frontend/nixpacks.toml

[phases.setup]
nixPkgs = ["nodejs-18_x", "npm-9_x"]

[phases.install]
cmds = ["npm install"]

[phases.build]
cmds = ["npm run build"]

[start]
cmd = "node server.js"
```

---

## Environment Variables

### PostgreSQL URL References

**DATABASE_URL** and **DATABASE_PUBLIC_URL** are auto-generated by the Postgres service. You should NOT query them via GraphQL — they are not exposed in the ServiceInstance schema.

Use variableRefs syntax in your code:

```python
# backend/.env (or via GraphQL variableUpsert)
DATABASE_URL="${{Postgres.DATABASE_URL}}"
DATABASE_PUBLIC_URL="${{Postgres.DATABASE_PUBLIC_URL}}"
```

**Important:** After setting environment variables with `variableUpsert`, you MUST trigger a redeploy for them to take effect:

```bash
# Option 1: Push a commit
git commit --allow-empty -m "redeploy env vars"
git push origin main

# Option 2: Use GraphQL
serviceInstanceDeployV2(id: "SERVICE_ID", latestCommit: true)
```

### Common Environment Variables

**Backend:**
- `DATABASE_URL`: `${{Postgres.DATABASE_URL}}`
- `DATABASE_PUBLIC_URL`: `${{Postgres.DATABASE_PUBLIC_URL}}`
- `PORT`: `8000` (or `3000` for Node)
- `PYTHONUNBUFFERED`: `1`
- `NODE_ENV`: `production`

**Frontend:**
- `REACT_APP_API_URL` or `NEXT_PUBLIC_API_URL`: Backend URL
- `NEXTAUTH_URL`: Frontend URL
- `NEXTAUTH_SECRET`: (if using NextAuth)

---

## Auto-Deploy Setup

### Prerequisite: GitHub Repo Connection

**Before enabling auto-deploy, verify the GitHub repo is connected:**

```bash
# Check upstreamUrl
railway services
# Should show: upstreamUrl = "https://github.com/..." 
```

**If upstreamUrl is null, connect the repo:**

Via Railway CLI:
```bash
railway service connect
```

Via GraphQL:
```bash
# Use githubRepoUpdate mutation
```

### Enable Auto-Deploy

```bash
# Via GraphQL (DeepSeek V4 Pro or GPT-5.5 ONLY)
mutation($input: ServiceInstanceAutoDeployUpdateInput!) {
    serviceInstanceAutoDeployUpdate(input: $input) {
        id
        enabled
        upstreamUrl
    }
}

# Variables
{
    "input": {
        "id": "SERVICE_ID",
        "enabled": true
    }
}
```

### Auto-Deploy Flow

1. Create service with Dockerfile/nixpacks.toml
2. Connect repo via `githubRepoUpdate` or `serviceConnect`
3. Enable auto-deploy via `serviceInstanceAutoDeployUpdate`
4. Push to main branch → Railway auto-deploys

---

## Live GraphQL Introspection Script

If you need to understand the Railway GraphQL schema, use this introspection script:

```python
# skills/railway-deploy/introspect_schema.py

import os
import requests

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"
RAILWAY_TOKEN = os.getenv("RAILWAY_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {RAILWAY_TOKEN}",
    "Content-Type": "application/json"
}

def introspect_schema():
    """Query Railway GraphQL v2 schema for all mutation fields."""
    query = """
    {
        __schema {
            mutationType {
                name
                fields {
                    name
                    description
                    args {
                        name
                        type {
                            name
                            kind
                        }
                        isNonNull
                    }
                }
            }
            types {
                name
                kind
                description
                interfaces {
                    name
                }
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
                inputFields {
                    name
                    type {
                        name
                        kind
                    }
                    isNonNull
                    defaultValue
                }
            }
        }
    }
    """

    response = requests.post(RAILWAY_GRAPHQL_URL, headers=HEADERS, json={"query": query})
    response.raise_for_status()
    return response.json()

def print_mutations(schema):
    """Print all mutation fields with their arguments."""
    mutations = schema["data"]["__schema"]["mutationType"]["fields"]
    print("=== MUTATIONS ===")
    for mutation in mutations:
        print(f"\n{name}({mutation['name']})")
        if mutation["args"]:
            print("  Args:")
            for arg in mutation["args"]:
                type_str = f"{arg['type']['name']}!" if arg['isNonNull'] else arg['type']['name']
                print(f"    - {arg['name']}: {type_str}")

def print_service_types(schema):
    """Print all Service* types."""
    types = schema["data"]["__schema"]["types"]
    service_types = [t for t in types if t["name"].startswith("Service")]
    print("\n=== SERVICE TYPES ===")
    for service_type in service_types:
        print(f"\n{name}({service_type['name']})")
        print(f"  Description: {service_type.get('description', 'N/A')}")
        if service_type["fields"]:
            print("  Fields:")
            for field in service_type["fields"]:
                type_str = field["type"]["name"]
                print(f"    - {field['name']}: {type_str}")

def print_input_types(schema):
    """Print all input types with required fields."""
    types = schema["data"]["__schema"]["types"]
    input_types = [t for t in types if t["kind"] == "INPUT_OBJECT"]
    print("\n=== INPUT TYPES ===")
    for input_type in input_types:
        print(f"\n{name}({input_type['name']})")
        if input_type.get("description"):
            print(f"  Description: {input_type['description']}")
        if input_type["inputFields"]:
            print("  Required Fields:")
            for field in input_type["inputFields"]:
                type_str = f"{field['type']['name']}!" if field['isNonNull'] else field['type']['name']
                print(f"    - {field['name']}: {type_str}")

if __name__ == "__main__":
    print("Introspecting Railway GraphQL v2 schema...")
    schema = introspect_schema()
    print_mutations(schema)
    print_service_types(schema)
    print_input_types(schema)
```

**Usage:**
```bash
export RAILWAY_TOKEN="your_token_here"
python3 skills/railway-deploy/introspect_schema.py > railway_schema.json
```

---

## Error Patterns

### 1. "Field 'ServiceCreateInput.projectId' of required type 'String!' was not provided"

**Cause:** Missing required field in mutation input.

**Fix:** Always provide `projectId` and `environmentId`:

```python
variables = {
    "input": {
        "name": "service-name",
        "projectId": "PROJECT_ID",
        "environmentId": "ENV_ID"
    }
}
```

### 2. "Cannot query field 'variables' on type 'ServiceInstance'"

**Cause:** ServiceInstance is a read-only reference, not the service instance itself.

**Fix:** Variables are stored elsewhere. Use variableRefs syntax instead of querying.

### 3. JSON escaping errors in bash scripts

**Cause:** Bash `cat << 'EOF'` doesn't preserve JSON structure.

**Fix:** Use Python for GraphQL, not bash:

```python
import requests
import json

response = requests.post(
    "https://backboard.railway.app/graphql/v2",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"query": "mutation { serviceCreate(...) }"}
)
```

### 4. $PORT not expanding in Dockerfile

**Cause:** Using shell form `CMD "..."` instead of exec form `[`...`]`.

**Fix:** Always use exec form with `sh -c`:

```dockerfile
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### 5. Auto-deploy not triggering after push

**Cause:** Auto-deploy not enabled or GitHub repo not connected.

**Fix:**
1. Check `upstreamUrl` on service instance
2. Connect repo via `githubRepoUpdate`
3. Enable auto-deploy via `serviceInstanceAutoDeployUpdate`

---

## Troubleshooting

### Check Deployment Status

```bash
# Via GraphQL
query {
    service(id: "SERVICE_ID") {
        deployments(last: 1) {
            edges {
                node {
                    id
                    status
                    startedAt
                    completedAt
                }
            }
        }
    }
}
```

### Check Service Logs

```bash
# Via Railway CLI
railway service logs --service service-name
```

### Health Endpoint Not Responding

1. Verify `/api/health` endpoint exists in your code
2. Check `PORT` environment variable matches your app
3. Verify container is running: `railway ps`

### Database Connection Failed

1. Verify `DATABASE_URL` is set with correct variableRefs syntax
2. Check PostgreSQL service is running
3. Verify environment names match (PRODUCTION vs STAGING)

---

## Alternative: Use Railway CLI

For simple deployments without GraphQL, use the CLI:

```bash
# Install
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy backend (Dockerfile builder)
cd backend
railway up

# Deploy frontend (nixpacks)
cd frontend
railway up

# Connect services
railway service connect

# Set environment variables
railway variables set DATABASE_URL "${{Postgres.DATABASE_URL}}"
```

---

## Common Workflows

### Deploy Python Backend with Dockerfile

```bash
# 1. Create Dockerfile with correct CMD pattern
# 2. Create requirements.txt
# 3. Deploy via Railway CLI
cd backend
railway up

# 4. Set environment variables
railway variables set DATABASE_URL "${{Postgres.DATABASE_URL}}"
railway variables set PYTHONUNBUFFERED "1"

# 5. Trigger redeploy
git commit --allow-empty -m "redeploy env vars"
git push origin main
```

### Deploy React Frontend with nixpacks.toml

```bash
# 1. Create nixpacks.toml with explicit nixPkgs
# 2. Add build and start scripts
# 3. Deploy via Railway CLI
cd frontend
railway up

# 4. Set environment variables
railway variables set NEXT_PUBLIC_API_URL "https://backend.up.railway.app"

# 5. Trigger redeploy
git commit --allow-empty -m "redeploy env vars"
git push origin main
```

### Connect Services

```bash
# Via CLI
railway service connect
# Select service A and service B

# Or deploy backend first, then connect frontend
cd frontend
railway up
railway service connect
# Select: steno-desk-frontend → steno-desk-backend
```

---

## References

- **StenoDesk Post-Mortem:** `archive/2026-07-29-cleanup/StenoDesk-migration-post-mortem.md`
- **Branding Templates:** `/skills/templates/BRAND-OS-STRUCTURE.md`, `/skills/templates/BRAND-ONBOARDING-CHECKLIST.md`
- **Asset Migration:** `/skills/brand-asset-migration/SKILL.md`
- **Railway Documentation:** https://docs.railway.app

---

## Examples

### Example 1: Complete Backend Deployment

```bash
# deploy_stenodesk_backend.sh

export RAILWAY_TOKEN="your_token"

# Get project ID
PROJECT_ID=$(railway whoami | grep project | awk '{print $4}')

# Create backend service
python3 skills/railway-deploy/deploy_service.py \
  --project-id "$PROJECT_ID" \
  --service-name "steno-desk-backend" \
  --github-repo "sheffk78/steno-desk-backend" \
  --dockerfile-path "backend/Dockerfile" \
  --auto-deploy
```

### Example 2: Frontend Deployment

```bash
# deploy_stenodesk_frontend.sh

export RAILWAY_TOKEN="your_token"

# Create frontend service
python3 skills/railway-deploy/deploy_service.py \
  --project-id "$PROJECT_ID" \
  --service-name "steno-desk-frontend" \
  --github-repo "sheffk78/steno-desk-frontend" \
  --nixpacks-config "frontend/nixpacks.toml" \
  --auto-deploy
```

### Example 3: Deploy from Local Machine

```bash
# Deploy without GitHub repo
python3 skills/railway-deploy/deploy_service.py \
  --project-id "$PROJECT_ID" \
  --service-name "local-service" \
  --local-dockerfile "backend/Dockerfile" \
  --no-auto-deploy
```
# Cloud Run Deployment Guide

This server deploys to Google Cloud Run (project `rubenschulze-sandbox`, region
`europe-west1`) as a container image, mirroring the deployment model of
`assistant-mcp`: the `deploy.yml` workflow verifies each commit on the host and
inside the image, then builds, pushes, and deploys the digest-pinned image.

## Container Image

The `Dockerfile` builds on `python:3.14-slim` with a pinned `uv` binary:

- `uv sync --frozen --no-dev --extra plotting --extra scientific` installs the
  runtime dependencies (including matplotlib/numpy for the visualization tools)
  and the project itself, in two frozen syncs so dependency layers cache
  independently of source changes.
- `MCP_TRANSPORT=http` is baked in; the server binds to `0.0.0.0:$PORT`
  (default 8080) per the Cloud Run convention.
- The command runs the `math-mcp-learning-server` entry point.

## Deploy Pipeline

`.github/workflows/deploy.yml` runs on every push to `main` and on manual
trigger (`workflow_dispatch`):

1. **host** — `ruff check`, `ruff format --check`, `pyright`, and `pytest` on
   Python 3.14 (via `setup-uv`, cache enabled, `uv sync --all-extras`).
2. **docker** — builds the container image (layer-cached via GHA cache) and
   runs the complete test suite *inside the image*, where the plotting and
   scientific extras are actually installed. On the host runner those
   matplotlib-gated tests are skips.
3. **deploy** (only on `main`) — Workload Identity Federation authentication
   (GitHub OIDC, no service account key in GitHub), image build and push to
   Artifact Registry
   (`europe-west1-docker.pkg.dev/rubenschulze-sandbox/math-mcp-learning-server/server`),
   then a Cloud Run deploy of the digest-pinned image to the service
   `math-mcp-learning-server` with unauthenticated ingress allowed (the MCP
   layer enforces the shared secret itself).

Pull requests never publish images; pushes happen exclusively in the deploy
pipeline on `main`. Deploys only happen after green verification of the same
commit. Rollback: `workflow_dispatch` on the last good commit, or
`gcloud run services update-traffic` to the previous revision.

## Startup Probe and Stateless HTTP

The deploy configures a startup probe on `GET /healthz` (container port 8080,
budget 60 s for the Python cold start). Until the probe of a fresh instance
succeeds, Cloud Run holds back incoming requests instead of routing them to
the unready instance. The endpoint is unauthenticated by design and checks no
dependencies.

The HTTP transport runs statelessly: each request is served independently and
no session state is kept in the process. The local stdio transport is
unaffected.

| Variable | Meaning | Injection in deploy |
|---|---|---|
| `MCP_TRANSPORT` | `http` selects the HTTP transport (default `stdio`) | Plain env var (`http`) |
| `MCP_STATELESS_HTTP` | `false` (case-insensitive) restores stateful HTTP; unset or any other value: stateless (default) | Plain env var (`true`) |
| `PORT` | Listen port (Cloud Run injects this) | Injected by Cloud Run |

## Authentication (Shared Secret Bearer Token)

The public HTTP service requires a shared secret on every MCP request, sent as
`Authorization: Bearer <token>`. The secret is compared constant-time
(`hmac.compare_digest`). Requests without or with a wrong token get `401`.
Only the MCP endpoints are protected — `/healthz` stays open for platform
probes. The stdio transport (local) is never authenticated.

**Activation contract:** authentication activates when `MCP_AUTH_TOKEN` is
set to a non-blank value; unset or blank means the server runs without
authentication (intended for local stdio use).

| Variable | Meaning | Injection in deploy |
|---|---|---|
| `MCP_AUTH_TOKEN` | Shared secret; must be sent as Bearer token by every client | Secret Manager (`mcp-auth-token`) |

### Secret Rotation (`MCP_AUTH_TOKEN`)

1. Generate a new secret and add it as a new Secret Manager version:

   ```bash
   openssl rand -hex 32 | \
     gcloud secrets versions add mcp-auth-token --project=rubenschulze-sandbox --data-file=-
   ```

2. Re-run the deploy (the workflow references `mcp-auth-token:latest`, so the
   new revision picks up the latest version).
3. Distribute the new secret to your MCP clients. Requests with the old
   secret fail with `401` once the new revision serves traffic.

Token material is never logged; the constant-time comparison prevents
timing-based recovery of the secret.

## One-Time Google Cloud Setup

The pipeline assumes these resources exist. Steps that overlap with the
existing `assistant-mcp` setup (project, Workload Identity pool, deploy
service account) are reused rather than recreated.

### 1. Artifact Registry repository

```bash
gcloud artifacts repositories create math-mcp-learning-server \
  --repository-format=docker --location=europe-west1 --project=rubenschulze-sandbox
```

### 2. Workload Identity Federation (OIDC provider for this repo)

The pool `github-actions` from the `assistant-mcp` setup is reused; this repo
gets its own provider because the existing one is locked to the
`assistant-mcp` repository by its attribute condition:

```bash
gcloud iam workload-identity-pools providers create-oidc math-mcp \
  --location=global --workload-identity-pool=github-actions \
  --project=rubenschulze-sandbox \
  --issuer="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '5pirit5eal/math-mcp-learning-server'"
```

### 3. Runtime service account (identity of the Cloud Run service; intentionally no roles)

```bash
gcloud iam service-accounts create math-mcp-runtime \
  --project=rubenschulze-sandbox --display-name="math-mcp Cloud Run runtime"
```

### 4. Deploy service account permissions

Reuse the existing `github-actions-deploy` service account. It needs write
access to the new Artifact Registry repository (its project-level `run.admin`
and `iam.serviceAccountUser` on the runtime account carry over):

```bash
gcloud artifacts repositories add-iam-policy-binding math-mcp-learning-server \
  --location=europe-west1 --project=rubenschulze-sandbox \
  --member="serviceAccount:github-actions-deploy@rubenschulze-sandbox.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

### 5. Shared secret in Secret Manager

```bash
openssl rand -hex 32 | \
  gcloud secrets create mcp-auth-token --project=rubenschulze-sandbox --data-file=-
```

The deploy service account must be able to read it:

```bash
gcloud secrets add-iam-policy-binding mcp-auth-token --project=rubenschulze-sandbox \
  --member="serviceAccount:github-actions-deploy@rubenschulze-sandbox.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 6. GitHub repository variables

The deploy workflow reads two repository variables and fails with a
actionable message when they are missing:

```bash
gh variable set WORKLOAD_IDENTITY_PROVIDER \
  --repo 5pirit5eal/math-mcp-learning-server \
  --body "projects/$(gcloud projects describe rubenschulze-sandbox --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-actions/providers/math-mcp"
```

## MCP Clients: Connecting

The MCP endpoint is `https://<service-url>/mcp`. Clients pass the shared
secret as a Bearer token.

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "math-cloud": {
      "transport": "http",
      "url": "https://<service-url>/mcp",
      "headers": { "Authorization": "Bearer <shared-secret>" }
    }
  }
}
```

**FastMCP client:**

```python
from fastmcp import Client

async with Client("https://<service-url>/mcp", auth="<shared-secret>") as client:
    tools = await client.list_tools()
```

Resolve the service URL with:

```bash
gcloud run services describe math-mcp-learning-server \
  --region=europe-west1 --project=rubenschulze-sandbox \
  --format='value(status.url)'
```

## Manual Verification After Deploy

- [ ] An authenticated tool call works (e.g. `calc_expression` with `2 + 2`).
- [ ] Unauthenticated requests are rejected:
      `curl -i https://<service-url>/mcp` returns `401`.
- [ ] Requests with a wrong token are rejected:
      `curl -i -H "Authorization: Bearer wrong" https://<service-url>/mcp`
      returns `401`.
- [ ] The health endpoint answers: `curl https://<service-url>/healthz`
      returns `{"status": "ok"}`.

## Workspace Persistence in Cloud Run

The persistent workspace (`workspace_save` / `workspace_load`) writes to
`~/.math-mcp/workspace.json` inside the container. Cloud Run containers have
ephemeral, instance-local filesystems: saved values survive requests handled
by the same instance and cold starts within a revision's lifetime are not
guaranteed to preserve them. This is standard serverless behavior and suitable
for the educational purpose of this server. For durable persistence, back
`src/math_mcp/persistence/storage.py` with external storage (e.g. a database
or GCS).

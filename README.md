# math-mcp-learning-server

Educational MCP server for math operations, statistics, visualization, and
persistent workspaces, built with FastMCP and deployed on Google Cloud Run.

Fork of [clouatre-labs/math-mcp-learning-server](https://github.com/clouatre-labs/math-mcp-learning-server),
restructured onto my personal MCP server scaffold (lean CI, semantic-release
versioning, release-driven deploys, OpenSpec workflow skills).

## Develop

```bash
uv sync --all-extras
uv run pytest
uv run ruff check .
uv run mypy src
```

- Transport: `MCP_TRANSPORT` (`stdio` default, `http` binds `0.0.0.0:$PORT`)
- HTTP auth: shared-secret bearer token from `MCP_AUTH_TOKEN`; unset = no auth
- Workspaces persist under `~/.math-mcp/` (instance-local, ephemeral on Cloud Run)
- `eval()` is restricted to the `math` module and `abs` (see `src/math_mcp/eval.py`)

## Pipeline

- CI (`.github/workflows/ci.yml`): ruff, mypy, pytest, actionlint, and a
  Docker build with the test suite run inside the image.
- Release (`.github/workflows/release.yml`): semantic-release derives the
  version from Conventional Commits (`.releaserc`) and publishes a GitHub
  release.
- Deploy (`.github/workflows/deploy.yml`): on a release, verifies on host and
  in image, then deploys the digest-pinned image to Cloud Run.
- Dependabot updates uv, GitHub Actions, and Docker dependencies weekly;
  patch and minor PRs auto-merge.

## One-time setup (fork)

1. GCP: WIF pool/provider for GitHub Actions, deploy and runtime service
   accounts, Artifact Registry repo, Secret Manager secret `mcp-auth-token`
   (see the flags in `deploy.yml` for the exact resource names).
2. `gh variable set WORKLOAD_IDENTITY_PROVIDER --body 'projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<POOL>/providers/<PROVIDER>'`
3. Create a GitHub App for semantic-release (contents: write), then set the
   `RELEASE_APP_ID` and `RELEASE_APP_PRIVATE_KEY` secrets.

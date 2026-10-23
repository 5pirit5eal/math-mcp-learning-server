# Delivery Pipeline Specification

## Purpose

Describe the repository's DevOps design: a lean CI gate on every PR and push, a
semantic-release loop on main that derives versions from Conventional Commits,
and a release-driven deploy that verifies twice (host and container) before
shipping the digest-pinned image to Google Cloud Run. Dependabot keeps
dependencies current and auto-merges safe updates.

## Requirements

### Requirement: Continuous Integration Gate

CI SHALL run on pull requests and pushes to main (Python 3.14, uv-managed):
actionlint, markdownlint, commitlint (from the last tag to HEAD), `ruff check`,
`mypy`, and `pytest`. A separate job SHALL build the Docker image with GHA layer
caching and run the full pytest suite inside the image, mounting the workspace
read-only and overlaying a fresh uv environment.

#### Scenario: Failing lint

- **WHEN** a PR introduces a ruff or mypy violation
- **THEN** the CI host job fails and the PR cannot merge

#### Scenario: Image parity

- **WHEN** CI passes on the host
- **THEN** the docker job still runs the test suite inside the built image to catch environment-dependent failures

### Requirement: Conventional Commit Release Loop

On every push to main, the release workflow SHALL wait for that commit's CI run
to succeed, then run semantic-release via a GitHub App token (contents: write).
semantic-release SHALL derive the version and changelog from Conventional
Commits per `.releaserc`, bump the version in `pyproject.toml` and `uv.lock`,
commit those with `chore(release): <version> [skip ci]`, and publish a GitHub
release. Non-releasable commit types (docs, style, chore, refactor, test,
build, ci) SHALL deliberately produce no release.

#### Scenario: Feature commit

- **WHEN** a commit `feat: add new tool` lands on main and its CI run succeeds
- **THEN** semantic-release publishes a minor release with updated CHANGELOG and project version

#### Scenario: Housekeeping commit

- **WHEN** only `chore` or `ci` commits land on main
- **THEN** no release is cut and nothing deploys

### Requirement: Release-Driven Cloud Run Deploy

The deploy workflow SHALL trigger on a published GitHub release, re-verify on
the host (ruff, mypy, pytest) and inside the container image before deploying,
authenticate to GCP via Workload Identity Federation (failing fast with a setup
hint when the provider variable is missing), and push the image to Artifact
Registry. It SHALL deploy the digest-pinned image to Cloud Run in europe-west1
with: `--allow-unauthenticated`, the runtime service account, the secret
`MCP_AUTH_TOKEN` from Secret Manager (`mcp-auth-token:latest`), environment
`MCP_TRANSPORT=http` and `MCP_STATELESS_HTTP=true`, and an HTTP startup probe
on `/healthz:8080`. Deploys SHALL be serialized per ref. The workflow's flags
and secrets SHALL stay asserted by `tests/test_deploy_config.py`.

#### Scenario: Release published

- **WHEN** a GitHub release is published
- **THEN** deploy verifies host and image, then rolls out the digest-pinned image to Cloud Run with the auth secret attached

#### Scenario: Missing WIF variable

- **WHEN** `WORKLOAD_IDENTITY_PROVIDER` is not set as a repository variable
- **THEN** the deploy job fails immediately with instructions to run the one-time GCP setup

### Requirement: Runtime Container Image

The Docker image SHALL be based on `python:3.14-slim`, install dependencies
with uv in two frozen syncs (dependencies, then the project) with the
`plotting` and `scientific` extras, default `MCP_TRANSPORT=http`, expose port
8080, and run the server via the package entry point.

#### Scenario: Container startup

- **WHEN** the image runs on a platform with port 8080 mapped
- **THEN** the server starts in HTTP mode and answers `/healthz`

### Requirement: Dependency Automation

Dependabot SHALL open weekly update PRs for uv dependencies, GitHub Actions,
and Docker dependencies; patch and minor updates SHALL auto-merge (squash)
after their checks pass, while major updates wait for review.

#### Scenario: Minor dependency bump

- **WHEN** Dependabot opens a minor-version update PR
- **THEN** the PR auto-merges once CI passes

### Requirement: Commit Message Discipline

Commit messages SHALL use the Conventional Commits types configured in
`.releaserc`, enforced by commitlint in CI, because semantic-release derives
both the version and the deploy trigger from them.

#### Scenario: Non-conforming message

- **WHEN** a commit on main uses a message commitlint rejects
- **THEN** the commitlint CI step fails

# AGENTS.md

## Project

Educational FastMCP server (`src/math_mcp/`): math tools (`tools/calculate.py`,
`tools/matrix.py`, `tools/visualization.py`), persistent workspaces
(`persistence/`, writes to `~/.math-mcp/`), MCP resources (`resources.py`),
and a restricted `eval()` sandbox (`eval.py` — `math` module and `abs` only;
never use `eval()` anywhere else). `server.py` is the composition root:
`build_server()`, middleware, `healthz`. Tool inputs are validated with
pydantic; optional context is `ctx: SkipValidation[Context | None] = None`,
never required, always guarded with `if ctx:`. Sync work is offloaded with
`asyncio.to_thread()`.

## Docs discipline

Prefer deterministic checks (test, lint, CI) over prose rules: wire the
check first, keep the doc a one-line pointer. Keep this file and the
skills (`.vibe/skills/`) minimal — load-bearing rules and navigation
pointers only.

## Commits

Commit messages use the Conventional Commits types configured in
`.releaserc` (enforced by commitlint in CI); semantic-release derives the
version and the Cloud Run deploy runs only on a release. Ship Cloud Run
changes with a releasable type; other types deliberately stay undeployed.

## Verification

CI (`.github/workflows/ci.yml`) runs ruff, mypy, pytest, actionlint,
markdownlint, commitlint, and a
Docker build with the test suite inside the image. Python tooling: uv +
ruff + mypy + pytest (no pyright, no coverage gate — intentionally lean).
`tests/test_deploy_config.py` asserts the deploy workflow's Cloud Run
flags and secrets; keep it passing when touching `deploy.yml`.

Project rules live in `openspec/config.yaml`; OpenSpec artifacts are
written in English.

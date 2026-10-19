# math-mcp-learning-server

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg?style=for-the-badge)](LICENSE)
[![REUSE](https://img.shields.io/reuse/compliance/github.com/clouatre-labs/math-mcp-learning-server?style=for-the-badge)](https://api.reuse.software/info/github.com/clouatre-labs/math-mcp-learning-server)
[![OpenSSF Best Practices](https://img.shields.io/cii/level/12334?style=for-the-badge)](https://www.bestpractices.dev/projects/12334)

**Educational MCP server with 17 tools, persistent workspace, and cloud hosting.** Built with [FastMCP](https://gofastmcp.com) and the official [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk).

Deployed to Google Cloud Run; not distributed through PyPI or MCP registries.

## Demo

![math-mcp Demo](https://raw.githubusercontent.com/clouatre-labs/math-mcp-learning-server/main/assets/demo.gif)

See [CONTRIBUTING.md](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/CONTRIBUTING.md#demo-gif) for instructions to record your own demo.

## Quick Start

The server is deployed to Google Cloud Run (see the [Cloud Run Deployment Guide](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/docs/CLOUD_DEPLOYMENT.md)). Connect your MCP client with the shared secret bearer token:

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

## Tools

| Category | Tool | Description |
|----------|------|-------------|
| **Workspace** | `workspace_save` | Save calculations to persistent storage |
| | `workspace_load` | Retrieve previously saved calculations |
| **Math** | `calc_expression` | Safely evaluate mathematical expressions |
| | `calc_statistics` | Statistical analysis (mean, median, mode, std_dev, variance) |
| | `calc_interest` | Calculate compound interest for investments |
| | `calc_units` | Convert between units (length, weight, temperature) |
| **Matrix** | `matrix_multiply` | Multiply two matrices |
| | `matrix_transpose` | Transpose a matrix |
| | `matrix_determinant` | Calculate matrix determinant |
| | `matrix_inverse` | Calculate matrix inverse |
| | `matrix_eigenvalues` | Calculate eigenvalues |
| **Visualization** | `plot_function` | Plot mathematical functions |
| | `plot_histogram` | Create statistical histograms |
| | `plot_line_chart` | Create line charts |
| | `plot_scatter` | Create scatter plots |
| | `plot_box_plot` | Create box plots |
| | `plot_financial_line` | Create financial line charts |

## Resources

- `math://workspace` - Persistent calculation workspace summary
- `math://history` - Chronological calculation history
- `math://functions` - Available mathematical functions reference
- `math://constants/{constant}` - Mathematical constants (pi, e, golden_ratio, etc.)
- `math://catalog/tools` - Tool catalog with metadata and usage examples
- `math://variables` - Active variables in the current workspace
- `math://test` - Server health check

## Prompts

- `math_tutor` - Structured tutoring prompts (configurable difficulty)
- `formula_explainer` - Formula explanation with step-by-step breakdowns

See [Usage Examples](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/docs/EXAMPLES.md) for detailed examples.

## Development

Requires Python 3.14 (pinned via `.python-version`) and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras      # install all dependencies (incl. matplotlib/numpy)
uv run math-mcp-learning-server          # stdio transport (local MCP clients)
uv run pytest              # tests
uv run ruff check .        # lint
uv run ruff format .       # format
uv run pyright src/        # type check
```

The HTTP transport with the shared-secret auth can be exercised locally:

```bash
MCP_TRANSPORT=http MCP_AUTH_TOKEN=<secret> uv run math-mcp-learning-server
# serves http://0.0.0.0:8080/mcp (Bearer token required); /healthz stays open
```

See [CONTRIBUTING.md](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/CONTRIBUTING.md) for testing and contribution guidelines, and the [Cloud Run Deployment Guide](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/docs/CLOUD_DEPLOYMENT.md) for the deployment pipeline and one-time Google Cloud setup.

## Security

- **Shared-Secret Bearer Auth** - HTTP deployments require `Authorization: Bearer <token>` (constant-time comparison, injected from Google Secret Manager)
- **OpenSSF Best Practices Silver** - Fewer than 1% of open source projects reach this level
- **REUSE/SPDX** - License compliance for all files
- **Signed Commits** - GPG-signed commits required
- **Dependency Scanning** - Automated updates via Renovate
- **pip-audit CVE Scanning** - Automated dependency vulnerability checks
- **gitleaks Secret Scanning** - Detects secrets in code and history
- **zizmor GitHub Actions Security** - Workflow security scanning
- **commitlint Enforcement** - Conventional commit validation in CI
- **OpenSSF Scorecard** - Continuous open source security assessment

<!-- markdownlint-disable MD033 -->
<details>
<summary><strong>calc_expression safety</strong></summary>

The `calc_expression` tool uses restricted `eval()` with a whitelist of allowed characters and functions, restricted global scope (only `math` module and `abs`), and no access to dangerous built-ins or imports. All tool inputs are validated with Pydantic models. File operations are restricted to the designated workspace directory. Complete type hints and validation are enforced for all operations.

</details>
<!-- markdownlint-enable MD033 -->

## Documentation

- [Architecture](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/docs/ARCHITECTURE.md)
- [Cloud Deployment Guide](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/docs/CLOUD_DEPLOYMENT.md)
- [Usage Examples](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/docs/EXAMPLES.md)
- [Contributing Guidelines](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/CONTRIBUTING.md)
- [Roadmap](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/ROADMAP.md)
- [Code of Conduct](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/CODE_OF_CONDUCT.md)
- [License](https://github.com/clouatre-labs/math-mcp-learning-server/blob/main/LICENSE)

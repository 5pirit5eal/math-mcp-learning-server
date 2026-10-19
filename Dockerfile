# syntax=docker/dockerfile:1
FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.31 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install runtime dependencies (incl. plotting/scientific extras), then the
# project itself, in two frozen syncs so dependency layers cache independently
# of source changes.
RUN uv sync --frozen --no-dev --extra plotting --extra scientific --no-install-project \
    && uv sync --frozen --no-dev --extra plotting --extra scientific

ENV MCP_TRANSPORT=http
EXPOSE 8080

CMD ["uv", "run", "math-mcp-learning-server"]

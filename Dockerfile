# Build-and-run image for the BCI-MCP Model Context Protocol server.
#
# The server speaks MCP over **stdio** (the transport Claude Desktop and the
# Glama directory use), so the container just launches `bci-mcp serve` and
# exchanges JSON-RPC on stdin/stdout — there is no network port to expose.
#
#   docker build -t bci-mcp .
#   docker run --rm -i bci-mcp          # MCP server over stdio (default)
#   docker run --rm -i bci-mcp devices  # any CLI subcommand also works
FROM python:3.12-slim

# Quiet, reproducible, no-cache Python in a container. BCI_RECORD_DIR points the
# `record` tool at a predictable, writable mount point (see VOLUME below).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BCI_RECORD_DIR=/data

WORKDIR /app

# Copy only what the build backend needs, then install. numpy/scipy/mcp/typer/
# rich all ship manylinux wheels, so no compiler or build-essential is required
# (keeps the image small and the build fast).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

# Drop privileges, with a writable recordings directory owned by the user.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data && chown appuser:appuser /data
USER appuser
VOLUME /data

# Default to the MCP stdio server; `bci-mcp` as entrypoint keeps the whole CLI
# usable (e.g. `docker run --rm -i bci-mcp stream --device synthetic:// --once`).
ENTRYPOINT ["bci-mcp"]
CMD ["serve"]

# Contributing to BCI-MCP

Thanks for your interest! BCI-MCP is a Python project (3.10+).

## Setup

```bash
python -m pip install -e ".[all,dev]"
git config core.hooksPath .githooks
```

The hooks path enables `prepare-commit-msg`, which strips unwanted AI `Co-authored-by` trailers from commits. See [AGENTS.md](AGENTS.md).

## Develop

- Source lives in `src/bci_mcp/`, tests in `tests/`.
- All tests are hardware-free (synthetic device, recording playback, in-process LSL, BrainFlow synthetic board), so you can run the full suite with no headset.
- Before opening a PR:

```bash
ruff check src tests
python -m pytest
```

## Adding a device backend

Implement `bci_mcp.core.device.Device`, return `Chunk(data=(channels, n) float32 µV, timestamps=(n,))`, and register a URI scheme via `bci_mcp.core.registry.register(...)`. See `devices/synthetic.py` for the simplest example and `devices/neurofocus.py` for a real-hardware one.

## Design docs

Specs and implementation plans live under `docs/superpowers/`.

## Releases (PyPI + npm)

Publishing is tag-driven. Bump **both** versions to the same value:

- `pyproject.toml` → `version = "X.Y.Z"`
- `npm/bci-mcp/package.json` → `"version": "X.Y.Z"`

Then:

```bash
git tag vX.Y.Z
git push origin main --tags
```

GitHub Actions (`.github/workflows/publish.yml`) builds, verifies versions match the tag, and publishes to PyPI and npm.

**PyPI** and **npm** use OIDC trusted publishing from `publish.yml` — no long-lived API tokens in GitHub secrets.

Configure trusted publishers on [pypi.org](https://pypi.org/manage/project/bci-mcp/settings/publishing/) and [npmjs.com](https://www.npmjs.com/package/bci-mcp) (see below).

Optional **environments** `pypi` and `npm` in GitHub for approval gates.

### PyPI trusted publisher

| Field | Value |
|-------|--------|
| PyPI | **GitHub** |
| Owner | `enkhbold470` |
| Repository | `bci-mcp` |
| Workflow | `publish.yml` |
| Environment | `pypi` |

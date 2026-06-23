# BCI-MCP Plan 4 — Polish, README, SEO, docs

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Steps use checkbox (`- [ ]`).

**Goal:** Make the repo a star-worthy, SEO/LLM-discoverable, well-documented project: a killer README, a LICENSE, community/metadata files, an honest MkDocs site (kill the old fictional API docs), expanded examples, and a final green verification — plus an updated CLAUDE.md.

**Architecture:** Documentation/content only — no behavior changes to `bci_mcp`. Verification = a few cheap tests (README/CITATION present and well-formed), `mkdocs build --strict` succeeding, `ruff` + `pytest` still green, and the CLI/MCP smoke commands working.

**Builds on Plans 1–3.** The package provides: device-agnostic acquisition (`synthetic`, `neurofocus` serial+BLE, `brainflow`, `lsl`, `serial`, `playback`), a DSP pipeline → `BrainState` (focus/calm/attention/engagement/fatigue/meditation + band powers + signal quality), a real MCP server (FastMCP/stdio) with tools/resources/prompt, a Rich CLI (`devices/stream/record/play/neurofeedback/dashboard/serve`), recording (CSV/npz/EDF) + replay, an LSL publisher, and a FastAPI web dashboard. 75 tests pass.

**Conventions:** `python3 -m pytest`, `ruff check src tests`, one commit per task, **NO `Co-Authored-By` trailer.** Repo: `github.com/enkhbold470/bci-mcp`; docs site `enkhbold470.github.io/bci-mcp`.

---

### Task 1: Killer README

**Files:**
- Overwrite: `README.md`
- Create: `tests/test_readme.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_readme.py`:

```python
from pathlib import Path

README = (Path(__file__).resolve().parent.parent / "README.md").read_text()


def test_readme_has_key_sections():
    for needle in ["BCI-MCP", "Model Context Protocol", "Quickstart",
                   "Claude Desktop", "Any EEG device", "pip install"]:
        assert needle in README, f"README missing: {needle}"


def test_readme_advertises_devices_and_keywords():
    for kw in ["synthetic", "NeuroFocus", "OpenBCI", "Muse", "BrainFlow", "LSL",
               "neurofeedback", "EEG", "brain-computer interface"]:
        assert kw in README, f"README missing keyword: {kw}"
```

- [ ] **Step 2: Run, confirm fail.**

- [ ] **Step 3: Overwrite `README.md`** with the following (keep it accurate to the implemented features):

````markdown
# 🧠 BCI-MCP — Plug your brain into any AI

> **A real [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that streams live EEG brain state — focus, calm, attention — from *any* EEG device (or a built-in synthetic brain) straight into Claude and any MCP client.**

[![CI](https://github.com/enkhbold470/bci-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/enkhbold470/bci-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-7c3aed)](https://modelcontextprotocol.io)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://enkhbold470.github.io/bci-mcp/)

**BCI-MCP** is a brain–computer interface (BCI) toolkit and a genuine **Model Context Protocol server**. It reads an EEG (electroencephalography) signal — from an [OpenBCI](https://openbci.com) board, a [Muse](https://choosemuse.com) headband, a NeuroFocus device, any [Lab Streaming Layer](https://labstreaminglayer.org) source, or a **built-in synthetic brain that needs no hardware** — turns it into real-time cognitive metrics, and exposes them to AI assistants like **Claude Desktop** as MCP tools and resources. Your AI can literally read and reason about your brain state.

```
$ bci-mcp stream --device synthetic

  FOCUS        ██████████████░░░░░░  0.71
  CALM         ██████░░░░░░░░░░░░░░  0.32
  ATTENTION    █████████████████░░░  0.86
  ENGAGEMENT   ██████████████░░░░░░  0.70
  α ████  β ███████  θ ██  δ █  γ ███     signal: GOOD
```

---

## ✨ Why BCI-MCP

- 🔌 **Any EEG device** — one URI, every backend. Synthetic, NeuroFocus (USB + BLE), OpenBCI, Muse, anything on LSL, or a generic serial stream.
- 🤖 **A real MCP server** — not a toy. Built on the official MCP Python SDK (FastMCP), it plugs into **Claude Desktop** and any MCP client over stdio.
- 🧪 **Works with zero hardware** — a synthetic brain + recording playback mean `pip install` → working demo → green CI, no headset required.
- 📊 **Real neuroscience** — band powers (δ θ α β γ via Welch PSD), focus/calm/attention/engagement/fatigue metrics, signal-quality + artifact detection, personalized calibration.
- 🎮 **Batteries included** — live terminal brain-meter, web dashboard, neurofeedback trainer, session recording (CSV/npz/EDF) + replay, and an LSL publisher for the wider BCI ecosystem.
- ✅ **Tested & typed** — 75+ hardware-free tests, ruff-clean, CI on Python 3.10–3.12.

## 🧰 Any EEG device

| Device | URI | Install |
|---|---|---|
| **Synthetic** (no hardware) | `synthetic://` | core |
| **NeuroFocus v4** (USB serial) | `neurofocus://serial//dev/tty.usbmodemXXXX` | `[devices]` |
| **NeuroFocus v4** (BLE) | `neurofocus://ble/NEUROFOCUS_V4_01` | `[devices]` |
| **OpenBCI** Cyton/Ganglion | `brainflow://cyton?serial_port=/dev/ttyUSB0` | `[devices]` |
| **Muse** 2 / S | `brainflow://muse_s` | `[devices]` |
| **Any LSL stream** | `lsl://YourStreamName` | `[lsl]` |
| **Generic serial** (1 int/line) | `serial:///dev/ttyACM0` | `[devices]` |
| **Recording replay** | `playback://session.npz` | core |

## 🚀 Quickstart

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
python -m pip install -e ".[all]"     # or just "." for the core synthetic + MCP path

bci-mcp devices                       # list connectable devices/URIs
bci-mcp stream --device synthetic://  # live terminal brain-meter (no hardware)
bci-mcp dashboard                     # live web dashboard at http://127.0.0.1:8000
```

Record and replay a session (great for demos and offline analysis):

```bash
bci-mcp record --device synthetic:// --seconds 30 --out session.npz
bci-mcp play session.npz
```

Train your focus:

```bash
bci-mcp neurofeedback --device synthetic:// --metric focus --target 0.7
```

## 🤖 Use it from Claude Desktop

Add this to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "bci-mcp": {
      "command": "bci-mcp",
      "args": ["serve"]
    }
  }
}
```

Then ask Claude things like *"What's my current focus level?"* or *"Run a 60-second neurofeedback session and tell me how I did."* Claude calls the MCP tools below.

**MCP tools:** `list_devices`, `connect`, `disconnect`, `get_brain_state`, `get_band_powers`, `get_signal_quality`, `calibrate`, `record`, `start_neurofeedback`, `get_neurofeedback_score`, `mark_event`, `stream_summary`.
**MCP resources:** `brain://state`, `brain://device`. **Prompt:** `interpret_brain_state`.

## 🏗️ Architecture

```
EEG device ─► Device (synthetic │ neurofocus │ brainflow │ lsl │ serial │ playback)
                 │  Chunk (channels × samples, µV)
                 ▼
              Stream ──► RingBuffer ──► consumers
                 ▼
            DSP Pipeline  (bandpass/notch → Welch band powers → metrics → quality)
                 │  BrainState (focus, calm, attention, …, signal quality)
                 ├──► CLI brain-meter / web dashboard
                 ├──► neurofeedback trainer
                 ├──► recorder (CSV / npz / EDF)  ◄──► PlaybackDevice
                 ├──► LSL publisher
                 └──► MCP server (FastMCP, stdio)  ──►  Claude / any MCP client
```

## 📦 Install options

```bash
pip install -e "."              # core: numpy, scipy, mcp, typer, rich (synthetic + MCP + CLI)
pip install -e ".[devices]"     # + brainflow, bleak, pyserial (OpenBCI, Muse, NeuroFocus, serial)
pip install -e ".[lsl]"         # + pylsl (consume/publish Lab Streaming Layer)
pip install -e ".[edf]"         # + pyedflib (EDF recording)
pip install -e ".[dashboard]"   # + fastapi, uvicorn (web dashboard)
pip install -e ".[all]"         # everything
```

## 🧠 Keywords

EEG · BCI · brain-computer interface · Model Context Protocol · MCP · Claude · AI · neurofeedback · OpenBCI · Muse · BrainFlow · Lab Streaming Layer (LSL) · brainwave · neurotech · neuroscience · Python · real-time signal processing · band power · alpha/beta/theta · focus tracking.

## 📚 Documentation

Full docs: **https://enkhbold470.github.io/bci-mcp/**

## ⚠️ Disclaimer

BCI-MCP is for research, education, and personal experimentation. It is **not a medical device** and must not be used for diagnosis or treatment.

## 🤝 Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Run `ruff check src tests && pytest` before opening a PR.

## 📄 License

MIT — see [LICENSE](LICENSE).
````

- [ ] **Step 4: Run, confirm pass** — `python3 -m pytest tests/test_readme.py -v` → 2 passed.

- [ ] **Step 5: Commit** — `git add README.md tests/test_readme.py && git commit -m "docs: killer SEO-optimized README"`

---

### Task 2: LICENSE + community & metadata files

**Files:**
- Create: `LICENSE` (MIT)
- Create: `CONTRIBUTING.md`
- Create: `CITATION.cff`
- Create: `CHANGELOG.md`
- Create: `docs/github-topics.md`
- Create: `tests/test_metadata.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_metadata.py`:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_license_is_mit():
    text = (ROOT / "LICENSE").read_text()
    assert "MIT License" in text


def test_citation_is_valid_yaml():
    import importlib.util

    if importlib.util.find_spec("yaml") is None:
        # CITATION.cff must at least exist and mention the project
        assert "bci-mcp" in (ROOT / "CITATION.cff").read_text().lower()
        return
    import yaml

    data = yaml.safe_load((ROOT / "CITATION.cff").read_text())
    assert data["cff-version"]
    assert "title" in data


def test_contributing_exists():
    assert "Contributing" in (ROOT / "CONTRIBUTING.md").read_text()
```

- [ ] **Step 2: Run, confirm fail.**

- [ ] **Step 3: Create `LICENSE`** — a standard MIT license, copyright holder `enkhbold470`, year 2026. (Use the canonical MIT text.)

- [ ] **Step 4: Create `CONTRIBUTING.md`** — accurate to this project:

```markdown
# Contributing to BCI-MCP

Thanks for your interest! BCI-MCP is a Python project (3.10+).

## Setup

```bash
python -m pip install -e ".[all,dev]"
```

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
```

- [ ] **Step 5: Create `CITATION.cff`:**

```yaml
cff-version: 1.2.0
message: "If you use BCI-MCP in your research, please cite it."
title: "BCI-MCP: Plug your brain into any AI"
abstract: "A Model Context Protocol server that streams live EEG brain state from any EEG device into AI assistants."
authors:
  - family-names: Ganbold
    given-names: Enkhbold
repository-code: "https://github.com/enkhbold470/bci-mcp"
url: "https://enkhbold470.github.io/bci-mcp/"
license: MIT
keywords:
  - EEG
  - brain-computer interface
  - Model Context Protocol
  - neurofeedback
  - BrainFlow
```

- [ ] **Step 6: Create `CHANGELOG.md`:**

```markdown
# Changelog

## 0.1.0
- Device-agnostic EEG acquisition: synthetic, NeuroFocus (serial + BLE), OpenBCI/Muse via BrainFlow, LSL, generic serial, recording playback.
- DSP pipeline: band powers (δ θ α β γ), focus/calm/attention/engagement/fatigue/meditation metrics, signal quality + artifacts, calibration.
- Real Model Context Protocol server (FastMCP, stdio) with tools, resources, and a prompt.
- CLI: devices, stream, record, play, neurofeedback, dashboard, serve.
- Recording (CSV/npz/EDF) + replay, neurofeedback trainer, LSL publisher, FastAPI web dashboard.
```

- [ ] **Step 7: Create `docs/github-topics.md`:**

```markdown
# GitHub topics

Set discoverability topics on the repo:

```bash
gh repo edit enkhbold470/bci-mcp --add-topic eeg,bci,brain-computer-interface,mcp,\
model-context-protocol,claude,ai,neurofeedback,openbci,muse,brainflow,lsl,\
brainwave,neurotech,neuroscience,python,signal-processing
```

Also set a social-preview image in repo Settings → Social preview for better link unfurls.
```

- [ ] **Step 8: Run, confirm pass** — `python3 -m pytest tests/test_metadata.py -v` → 3 passed.

- [ ] **Step 9: Commit** — `git add LICENSE CONTRIBUTING.md CITATION.cff CHANGELOG.md docs/github-topics.md tests/test_metadata.py && git commit -m "docs: LICENSE, CONTRIBUTING, CITATION, CHANGELOG, GitHub topics"`

---

### Task 3: MkDocs site rewrite (kill the fictional API docs)

**Files:**
- Overwrite: `docs/index.md`, `docs/getting-started/installation.md`, `docs/getting-started/quick-start.md`, `docs/getting-started/configuration.md`, `docs/features/bci-features.md`, `docs/features/mcp-integration.md`, `docs/features/signal-processing.md`, `docs/api/bci-module.md`, `docs/api/mcp-module.md`, `docs/changelog.md`
- Modify: `mkdocs.yml` (nav + mkdocstrings paths)
- Delete: `docs/test.md` (and remove from nav)

The current API docs describe classes that don't exist (`BciDevice`, `McpClient`, etc.). Replace all docs with accurate content for the real package, and point `mkdocstrings` at `src/bci_mcp`.

- [ ] **Step 1: Rewrite `docs/index.md`** — a concise version of the README intro (pitch, device table, quickstart, Claude Desktop config, links). Keep it accurate.

- [ ] **Step 2: Rewrite getting-started pages:**
  - `installation.md` — `pip install -e ".[all]"` + extras table; Python 3.10+.
  - `quick-start.md` — the real CLI commands (`devices/stream/record/play/neurofeedback/dashboard/serve`) and the Claude Desktop config snippet.
  - `configuration.md` — device URIs and their query params (channels/focus/seed for synthetic; serial_port/mac_address for brainflow; ble name / serial port for neurofocus), notch frequency, calibration.

- [ ] **Step 3: Rewrite features pages** to describe the real implementation:
  - `bci-features.md` — devices, acquisition, recording/playback, neurofeedback, dashboard.
  - `mcp-integration.md` — the real MCP tools/resources/prompt and how to wire Claude Desktop.
  - `signal-processing.md` — bandpass/notch, Welch band powers, the metric formulas, signal quality, calibration.

- [ ] **Step 4: Replace API pages with mkdocstrings autodoc** — `docs/api/bci-module.md`:

```markdown
# Core & DSP API

::: bci_mcp.core.device
::: bci_mcp.core.registry
::: bci_mcp.pipeline
::: bci_mcp.dsp.bands
::: bci_mcp.dsp.metrics
::: bci_mcp.dsp.state
```

`docs/api/mcp-module.md`:

```markdown
# MCP & devices API

::: bci_mcp.mcp.service
::: bci_mcp.devices.synthetic
::: bci_mcp.devices.neurofocus
```

- [ ] **Step 5: Update `docs/changelog.md`** to include or `--8<--` the root `CHANGELOG.md` content (just paste the same content).

- [ ] **Step 6: Update `mkdocs.yml`** — set `plugins.mkdocstrings.handlers.python.paths: [src]`, remove the `Test Page: test.md` nav entry, and delete `docs/test.md`.

- [ ] **Step 7: Build the docs strictly** — install docs deps and build:

```bash
python3 -m pip install mkdocs-material mkdocstrings mkdocstrings-python
mkdocs build --strict
```
Expected: build succeeds with no warnings/errors (fix any broken nav links or mkdocstrings import paths until `--strict` passes). If `--strict` flags a benign warning you cannot resolve, drop to `mkdocs build` and note exactly what was warned.

- [ ] **Step 8: Commit** — `git add docs mkdocs.yml && git commit -m "docs: rewrite MkDocs site to match the real package (kill fictional API docs)"`

---

### Task 4: Examples, CLAUDE.md refresh, final verification

**Files:**
- Create: `examples/record_and_analyze.py`
- Create: `examples/README.md`
- Overwrite: `CLAUDE.md`
- Create: `tests/test_examples_compile.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_examples_compile.py`:

```python
from pathlib import Path

EXAMPLES = (Path(__file__).resolve().parent.parent / "examples")


def test_all_examples_compile():
    py_files = list(EXAMPLES.glob("*.py"))
    assert py_files, "no example scripts found"
    for f in py_files:
        compile(f.read_text(), f.name, "exec")
```

- [ ] **Step 2: Run, confirm fail** (if `record_and_analyze.py` absent or has a syntax error) — or pass if existing examples already compile; ensure the new example is added regardless.

- [ ] **Step 3: Create `examples/record_and_analyze.py`:**

```python
"""Record a synthetic session, then load it and print band powers."""
import numpy as np

from bci_mcp.dsp import bands, filters
from bci_mcp.pipeline import Pipeline
from bci_mcp.recording.reader import load_recording


def main() -> None:
    pipe = Pipeline("synthetic://?focus=0.7&seed=1")
    pipe.start()
    try:
        import time

        time.sleep(0.5)
        path = pipe.record(seconds=2.0, path="demo_session.npz")
        print("saved", path)
    finally:
        pipe.stop()

    rec = load_recording(path)
    filtered = filters.bandpass(rec.data, rec.sample_rate)
    print("band powers:", bands.band_powers(filtered, rec.sample_rate))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create `examples/README.md`** — list and briefly describe each example (`claude_desktop_config.json`, `mcp_quickstart.py`, `record_and_analyze.py`).

- [ ] **Step 5: Overwrite `CLAUDE.md`** so future Claude instances get accurate guidance. It MUST start with the required preamble and describe: the real `src/bci_mcp/` package layout; how to install (`pip install -e ".[all,dev]"`); how to run tests (`python -m pytest`, `ruff check src tests`); the architecture (Device→Stream→Pipeline→BrainState→{CLI, MCP, dashboard, recorder, LSL}); the URI device registry; the real MCP server (FastMCP/stdio) and that this IS the official MCP SDK; that all tests are hardware-free; and where specs/plans live (`docs/superpowers/`). Remove the old warnings about the import bug / fictional docs (now resolved). Begin the file with exactly:

```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
```

- [ ] **Step 6: Run example + tests** — `python3 -m pytest tests/test_examples_compile.py -v` → pass; and run the example end-to-end: `python3 examples/record_and_analyze.py` (should print a saved path + band powers; clean up `demo_session.npz` after).

- [ ] **Step 7: FINAL full verification** — run and confirm all green:

```bash
ruff check src tests
python3 -m pytest
python3 -c "import bci_mcp; from bci_mcp.mcp import server; print('import OK', bci_mcp.__version__)"
bci-mcp --help
bci-mcp devices
bci-mcp stream --device "synthetic://?focus=0.8" --once
```
Report the actual pytest summary, ruff result, and that the CLI commands work.

- [ ] **Step 8: Commit** — `git add examples CLAUDE.md tests/test_examples_compile.py && git commit -m "docs: examples, refreshed CLAUDE.md, final verification"`

---

## Self-review (plan author)

**Spec coverage:** killer SEO README (Task 1) ✓; LICENSE + CONTRIBUTING + CITATION + CHANGELOG + GitHub-topics (Task 2) ✓; MkDocs rewrite killing fictional API docs + mkdocstrings on the real package (Task 3) ✓; examples + refreshed CLAUDE.md + final end-to-end verification (Task 4) ✓.

**Verification:** README/CITATION/LICENSE/CONTRIBUTING asserted by tests; examples compile-checked + one run end-to-end; `mkdocs build --strict` must pass; full `ruff` + `pytest` + CLI/MCP smoke at the end.

**No behavior changes:** docs/content only; the package code from Plans 1–3 is untouched, so the 75 existing tests must remain green (final step confirms).

**Consistency:** README device table + MCP tool list + CLI commands match exactly what Plans 1–3 implemented (synthetic/neurofocus/brainflow/lsl/serial/playback; tools list incl. record/neurofeedback; CLI devices/stream/record/play/neurofeedback/dashboard/serve).

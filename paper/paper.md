---
title: 'BCI-MCP: A Model Context Protocol server that streams live EEG band-power metrics to AI assistants'
tags:
  - Python
  - EEG
  - brain-computer interface
  - Model Context Protocol
  - large language models
  - neurofeedback
authors:
  - name: Enkhbold Ganbold
    orcid: 0009-0007-1785-7034
    affiliation: 1
affiliations:
  - name: Independent researcher, United States
    index: 1
date: 27 September 2026
bibliography: paper.bib
---

# Summary

BCI-MCP is a Python package that connects electroencephalography (EEG) devices to
large-language-model (LLM) assistants through the Model Context Protocol (MCP)
[@mcpspec]. It acquires live EEG from a synthetic generator, BrainFlow boards such as
OpenBCI and Muse [@brainflow], Lab Streaming Layer streams [@kothe2025], serial devices,
the NeuroFocus ear-EEG prototype, or recorded files. A deterministic pipeline turns
each 2 s window into band powers, six heuristic band-power ratios, signal-quality and
artifact flags, and a confidence score. The results are exposed to any MCP client as
14 tools, 2 resources and 1 prompt. The same pipeline also drives a terminal meter,
a web dashboard, recording to CSV/NPZ/EDF, an LSL publisher and a neurofeedback trainer.

# Statement of need

MCP makes it easy to give an assistant new data sources, and consumer EEG is cheap
enough that people want to try "asking Claude about my brain state". The difficulty is
interpretive. An LLM given raw samples will improvise signal processing, and an LLM
given one unexplained number will narrate it as a fact about the user's mind.
BCI-MCP targets developers, neurofeedback hobbyists and researchers prototyping
LLM-in-the-loop BCI studies who need the opposite: signal processing that is
deterministic and inspectable, and outputs that carry what is needed to discount them.

Three design decisions follow from that need. First, the model never receives raw
EEG; it receives computed scalars from standard methods (60 Hz notch, 1–45 Hz
zero-phase Butterworth band-pass, Welch PSD [@welch1967] via SciPy and NumPy
[@virtanen2020; @harris2020]). Second, every metric is a published ratio with its
formula, source and caveat available to the model: `focus` is the engagement index
$\beta/(\alpha+\theta)$ [@pope1995], `attention` is the inverse theta/beta ratio
[@lubar1991; @monastra1999] whose diagnostic value is contested [@arns2013], and
`fatigue` is $(\theta+\alpha)/\beta$ [@eoh2005]. Third, the pipeline's limitations
(for example, that Welch averaging hides event-related potentials) live in one module
and are served to the model through `get_pipeline_limitations`, inline disclaimers and
the `interpret_brain_state` prompt. Because tool arguments come from a model that may
be steered by untrusted content, all arguments are validated, recordings are sandboxed,
file- and port-granting device schemes are refused over MCP, and HTTP transports
support bearer-token authentication.

# State of the field

BCI2000 [@schalk2004] and OpenViBE [@renard2010] are established real-time BCI
platforms, and MNE-Python [@gramfort2013] is the standard for offline analysis.
BCI-MCP reuses BrainFlow and LSL for acquisition and does not compete with these
tools. Its contribution is the LLM-facing interface. Other EEG-to-MCP projects exist:
Neurosity offers a hosted MCP server for its own headset [@neurositymcp], and several
single-device open-source servers appeared in 2026. BCI-MCP is device-agnostic,
runs locally, works without hardware through a synthetic device on the same code
path, and ships an evaluation of its own pipeline.

# Software design and evaluation

A URI registry (`synthetic://`, `brainflow://`, `lsl://`, `neurofocus://`, …) maps to
backends behind a five-method `Device` interface. A single thread fills a 10 s ring
buffer, and `Pipeline.current_state()` analyses the latest 2 s. `BrainService` holds
all testable logic, and the FastMCP server is a thin adapter over it. The package has
149 hardware-free tests and runs on Python 3.10–3.14.

The `paper/benchmarks/` directory reproduces four checks of the released code. (1)
On synthetic signals with a known alpha/beta trade-off, all six metrics are monotonic
in the generator parameter (Spearman $|\rho| = 0.996$). (2) On the eyes-open and
eyes-closed baselines of 109 subjects in the PhysioNet EEG Motor Movement/Imagery
Dataset [@eegmmidb; @schalk2004; @goldberger2000], the uncalibrated `calm` metric on O1/Oz/O2
rises with eyes closed in 105 of 109 subjects (Wilcoxon $p = 3\times10^{-19}$),
recovering the Berger effect [@berger1929; @barry2007]. (3) Injected flatline,
railing, EMG-like and blink artifacts are flagged above fixed amplitude thresholds.
However, the amplitude-only blink detector also fires on 40% of the eyes-closed
occipital windows, a known limitation. (4) Over stdio, a `get_brain_state` tool call
has a median round trip of 1.3 ms. The metrics are heuristic proxies, not validated
measures of cognitive state, and the package is not a medical device.

# Research impact statement

BCI-MCP is published on PyPI and npm and listed in several MCP directories. It gives
researchers a ready-made, documented bridge for studies of how LLM assistants use,
or misuse, physiological signals. For example, it can be used to test whether models
respect the confidence and limitation fields they are given, which is the main open
question this design raises.

# AI usage disclosure

Much of the June 2026 rewrite was written with AI coding assistants (Claude Code,
Cursor) working from design documents kept in `docs/superpowers/`; the author directed
the design, integrated the NeuroFocus hardware protocol, reviewed and tested the
changes, and is responsible for the code. The benchmark scripts and a first draft of
this paper were prepared with an AI assistant (Claude). The author checked every
number against the benchmark outputs and every reference against its DOI record.

# Acknowledgements

We thank the creators of the EEG Motor Movement/Imagery Dataset and PhysioNet.

# References

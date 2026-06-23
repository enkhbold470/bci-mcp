# Changelog

## 0.1.0
- Device-agnostic EEG acquisition: synthetic, NeuroFocus (serial + BLE), OpenBCI/Muse via BrainFlow, LSL, generic serial, recording playback.
- DSP pipeline: band powers (δ θ α β γ), focus/calm/attention/engagement/fatigue/meditation metrics, signal quality + artifacts, calibration.
- Real Model Context Protocol server (FastMCP, stdio) with tools, resources, and a prompt.
- CLI: devices, stream, record, play, neurofeedback, dashboard, serve.
- Recording (CSV/npz/EDF) + replay, neurofeedback trainer, LSL publisher, FastAPI web dashboard.

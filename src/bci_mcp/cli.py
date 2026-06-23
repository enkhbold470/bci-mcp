"""bci-mcp command-line interface."""
from __future__ import annotations

import time

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

from .dsp.state import BrainState
from .pipeline import Pipeline

app = typer.Typer(add_completion=False, help="Plug your brain into any AI.")
console = Console()


@app.command()
def devices() -> None:
    """List known device URIs you can connect to."""
    console.print("[bold]Available device schemes:[/bold]")
    console.print("  synthetic://              built-in EEG, no hardware (default)")
    console.print("  neurofocus://ble/<name>   NeuroFocus v4 over BLE        (Plan 2)")
    console.print("  neurofocus://serial/<port> NeuroFocus v4 over USB       (Plan 2)")
    console.print("  brainflow://<board>       OpenBCI / Muse / etc.         (Plan 2)")
    console.print("  lsl://<stream>            any Lab Streaming Layer source (Plan 2)")


def _render(state: BrainState | None) -> Table:
    table = Table(title="BCI-MCP — live brain state")
    table.add_column("metric")
    table.add_column("value")
    table.add_column("bar")
    if state is None:
        table.add_row("status", "warming up…", "")
        return table
    for name, value in state.metrics.items():
        bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
        table.add_row(name, f"{value:.2f}", bar)
    table.add_row("signal", state.signal_quality, f"{state.quality_score:.2f}")
    return table


@app.command()
def stream(
    device: str = typer.Option("synthetic://", help="Device URI."),
    once: bool = typer.Option(False, help="Print one snapshot and exit."),
) -> None:
    """Live terminal brain-meter."""
    pipeline = Pipeline(device)
    pipeline.start()
    try:
        if once:
            state = None
            for _ in range(50):
                time.sleep(0.1)
                state = pipeline.current_state()
                if state is not None:
                    break
            console.print(_render(state))
            return
        with Live(_render(None), console=console, refresh_per_second=4) as live:
            while True:
                time.sleep(0.25)
                live.update(_render(pipeline.current_state()))
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()


@app.command()
def serve(transport: str = typer.Option("stdio", help="stdio | sse")) -> None:
    """Run the MCP server (for Claude Desktop)."""
    from .mcp.server import serve as serve_mcp

    serve_mcp(transport=transport)


# Alias `bci-mcp mcp` → `bci-mcp serve`
@app.command(name="mcp")
def mcp_alias(transport: str = typer.Option("stdio")) -> None:
    """Alias for `serve`."""
    serve(transport=transport)


if __name__ == "__main__":
    app()

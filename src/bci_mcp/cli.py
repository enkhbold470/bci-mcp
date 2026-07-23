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
    """List connectable EEG devices and URI schemes."""
    from .core.registry import discover, list_schemes

    console.print("[bold]Discovered devices:[/bold]")
    for entry in discover():
        console.print(f"  {entry['uri']:<28} {entry['name']}")
    console.print(f"\n[bold]URI schemes:[/bold] {', '.join(list_schemes())}")
    console.print("  e.g. neurofocus://ble/NEUROFOCUS_V4_01, brainflow://muse_s, "
                  "brainflow://cyton?serial_port=/dev/ttyUSB0, lsl://MyStream")


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
    conf_note = state.status if state.status != "ok" else ""
    table.add_row("confidence", f"{state.confidence:.2f}", conf_note)
    table.caption = (
        "heuristic band-power proxies · not clinical · transients averaged out"
    )
    table.caption_style = "dim"
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
def serve(
    transport: str = typer.Option(
        "stdio",
        help="stdio | sse | streamable-http (use streamable-http on Manufact Cloud)",
    ),
) -> None:
    """Run the MCP server (for Claude Desktop or Manufact Cloud)."""
    from .mcp.server import serve as serve_mcp

    serve_mcp(transport=transport)


# Alias `bci-mcp mcp` → `bci-mcp serve`
@app.command(name="mcp")
def mcp_alias(transport: str = typer.Option("stdio")) -> None:
    """Alias for `serve`."""
    serve(transport=transport)


@app.command()
def record(device: str = typer.Option("synthetic://"), seconds: float = 10.0,
           out: str = "session.npz", fmt: str = typer.Option(None)) -> None:
    """Record a session to a file."""
    pipeline = Pipeline(device)
    pipeline.start()
    try:
        time.sleep(0.5)  # warm up
        path = pipeline.record(seconds=seconds, path=out, fmt=fmt)
        console.print(f"[green]Saved[/green] {path}")
    finally:
        pipeline.stop()


@app.command()
def play(path: str, once: bool = typer.Option(False)) -> None:
    """Replay a recording through the live brain-meter."""
    from pathlib import Path as _Path

    resolved = _Path(path).resolve()
    if not resolved.is_file():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)
    stream(device=f"playback://{resolved}?loop=true", once=once)


@app.command()
def neurofeedback(device: str = typer.Option("synthetic://"),
                  metric: str = "focus", target: float = 0.7,
                  seconds: float = 30.0) -> None:
    """Run a neurofeedback session and print a summary."""
    from .neurofeedback.trainer import NeurofeedbackSession

    pipeline = Pipeline(device)
    pipeline.start()
    sess = NeurofeedbackSession(pipeline, metric=metric, target=target)
    sess.start()
    try:
        time.sleep(0.5)
        end = time.time() + seconds
        with Live(console=console, refresh_per_second=4) as live:
            while time.time() < end:
                time.sleep(0.25)
                sess.sample()
                s = sess.score()
                live.update(f"{metric}: {s['current']:.2f}  in-zone: "
                            f"{s['cumulative_in_zone_pct']:.0f}%")
        summary = sess.summary()
        console.print(f"[bold]Session:[/bold] {summary.time_in_zone_pct:.0f}% in zone, "
                      f"mean {summary.mean_score:.2f}, best streak {summary.best_streak}")
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()


@app.command()
def dashboard(device: str = typer.Option("synthetic://"), host: str = "127.0.0.1",
              port: int = 8000) -> None:
    """Launch the live web dashboard."""
    from .dashboard.server import serve_dashboard

    if host not in ("127.0.0.1", "::1", "localhost"):
        console.print(
            f"[yellow]Warning:[/yellow] Dashboard bound to {host} — brain state data will be "
            "accessible to anyone on the network. The dashboard has no authentication."
        )
    console.print(f"[green]Dashboard[/green] http://{host}:{port}  (device: {device})")
    serve_dashboard(device=device, host=host, port=port)


if __name__ == "__main__":
    app()

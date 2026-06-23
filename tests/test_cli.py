from typer.testing import CliRunner

from bci_mcp.cli import app

runner = CliRunner()


def test_devices_lists_synthetic():
    result = runner.invoke(app, ["devices"])
    assert result.exit_code == 0
    assert "synthetic://" in result.stdout


def test_stream_once_prints_metrics():
    # --once renders a single BrainState snapshot and exits (no live loop)
    result = runner.invoke(app, ["stream", "--device", "synthetic://?seed=1", "--once"])
    assert result.exit_code == 0
    assert "focus" in result.stdout.lower()

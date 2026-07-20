"""Security tests for the recording-path sandbox and the MCP URI allowlist."""
import pytest

from bci_mcp.recording.paths import (
    MCP_ALLOWED_SCHEMES,
    safe_record_path,
    validate_mcp_uri,
)


@pytest.fixture
def record_dir(tmp_path, monkeypatch):
    allowed = tmp_path / "recordings"
    allowed.mkdir()
    monkeypatch.setenv("BCI_RECORD_DIR", str(allowed))
    return allowed


def test_relative_path_lands_in_allowed_dir(record_dir):
    assert safe_record_path("session.npz") == str(record_dir / "session.npz")


def test_relative_traversal_uses_basename_only(record_dir):
    assert safe_record_path("../../etc/passwd") == str(record_dir / "passwd")
    assert safe_record_path("a/b/../../../c.npz") == str(record_dir / "c.npz")


def test_absolute_path_inside_allowed_dir_ok(record_dir):
    target = record_dir / "s.npz"
    assert safe_record_path(str(target)) == str(target)


def test_absolute_path_outside_rejected(record_dir):
    with pytest.raises(ValueError):
        safe_record_path("/etc/passwd")


def test_absolute_traversal_rejected(record_dir):
    with pytest.raises(ValueError):
        safe_record_path(str(record_dir / ".." / "escape.npz"))


def test_prefix_sibling_dir_rejected(record_dir, tmp_path):
    sibling = str(tmp_path / "recordings-evil" / "x.npz")
    with pytest.raises(ValueError):
        safe_record_path(sibling)


def test_degenerate_paths_rejected(record_dir):
    for bad in ("", ".", ".."):
        with pytest.raises(ValueError):
            safe_record_path(bad)


def test_symlink_escape_rejected(record_dir, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = record_dir / "link"
    link.symlink_to(outside)
    with pytest.raises(ValueError):
        safe_record_path(str(link / "x.npz"))


def test_allowed_schemes_pass():
    for scheme in MCP_ALLOWED_SCHEMES:
        assert validate_mcp_uri(f"{scheme}://x") == f"{scheme}://x"


@pytest.mark.parametrize("uri", [
    "playback:///etc/passwd",
    "PLAYBACK:///etc/passwd",
    "serial:///dev/ttyUSB0",
    "file:///etc/passwd",
    "unknown://",
    "",
    "no-scheme-at-all",
])
def test_filesystem_and_unknown_schemes_rejected(uri):
    with pytest.raises(ValueError):
        validate_mcp_uri(uri)

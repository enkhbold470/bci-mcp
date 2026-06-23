from bci_mcp.core.registry import discover, list_schemes


def test_list_schemes_includes_core():
    schemes = list_schemes()
    for s in ("synthetic", "serial", "neurofocus"):
        assert s in schemes


def test_optional_schemes_present_when_installed():
    import importlib.util
    schemes = list_schemes()
    if importlib.util.find_spec("brainflow"):
        assert "brainflow" in schemes
    if importlib.util.find_spec("pylsl"):
        assert "lsl" in schemes


def test_discover_returns_entries_with_uris():
    entries = discover()
    assert any(e["uri"].startswith("synthetic://") for e in entries)
    for e in entries:
        assert "uri" in e and "name" in e

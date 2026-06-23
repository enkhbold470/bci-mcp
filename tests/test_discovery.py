from bci_mcp.core.registry import discover, list_schemes


def test_list_schemes_includes_all_registered():
    schemes = list_schemes()
    for s in ("synthetic", "serial", "neurofocus", "brainflow", "lsl"):
        assert s in schemes


def test_discover_returns_entries_with_uris():
    entries = discover()
    assert any(e["uri"].startswith("synthetic://") for e in entries)
    for e in entries:
        assert "uri" in e and "name" in e

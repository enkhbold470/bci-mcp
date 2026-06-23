import bci_mcp


def test_version_exposed():
    assert isinstance(bci_mcp.__version__, str)
    assert bci_mcp.__version__.count(".") >= 2

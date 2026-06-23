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

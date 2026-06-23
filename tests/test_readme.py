from pathlib import Path

README = (Path(__file__).resolve().parent.parent / "README.md").read_text()


def test_readme_has_key_sections():
    for needle in ["BCI-MCP", "Model Context Protocol", "Quickstart",
                   "Claude Desktop", "Any EEG device", "pip install"]:
        assert needle in README, f"README missing: {needle}"


def test_readme_advertises_devices_and_keywords():
    for kw in ["synthetic", "NeuroFocus", "OpenBCI", "Muse", "BrainFlow", "LSL",
               "neurofeedback", "EEG", "brain-computer interface"]:
        assert kw in README, f"README missing keyword: {kw}"

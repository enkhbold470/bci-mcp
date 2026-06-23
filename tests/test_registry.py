import pytest

from bci_mcp.core.registry import create_device
from bci_mcp.devices.synthetic import SyntheticDevice


def test_default_scheme_is_synthetic():
    dev = create_device("synthetic://")
    assert isinstance(dev, SyntheticDevice)


def test_params_parsed():
    dev = create_device("synthetic://?channels=8&focus=0.9&seed=3")
    assert dev.info.channel_count == 8
    assert dev.focus == 0.9


def test_unknown_scheme_raises():
    with pytest.raises(ValueError, match="Unknown device scheme"):
        create_device("nope://whatever")

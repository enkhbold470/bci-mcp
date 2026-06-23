"""URI-based device registry: create_device('synthetic://?focus=0.8')."""
from __future__ import annotations

from collections.abc import Callable
from urllib.parse import ParseResult, parse_qs, urlparse

from .device import Device

DeviceFactory = Callable[[ParseResult, dict[str, str]], Device]
_REGISTRY: dict[str, DeviceFactory] = {}


def register(scheme: str, factory: DeviceFactory) -> None:
    _REGISTRY[scheme] = factory


def create_device(uri: str) -> Device:
    parsed = urlparse(uri)
    scheme = parsed.scheme or "synthetic"
    if scheme not in _REGISTRY:
        raise ValueError(
            f"Unknown device scheme '{scheme}'. Known: {sorted(_REGISTRY)}"
        )
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    return _REGISTRY[scheme](parsed, params)

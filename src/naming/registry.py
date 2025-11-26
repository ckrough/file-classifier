from __future__ import annotations

from typing import Dict, Type

from src.naming.styles import NamingStyle
from src.naming.compact_gpo import CompactGPOStyle
from src.naming.descriptive_nara import DescriptiveNARAStyle


_REGISTRY: Dict[str, Type[NamingStyle]] = {
    "compact_gpo": CompactGPOStyle,
    "descriptive_nara": DescriptiveNARAStyle,
}


def get_style(name: str) -> NamingStyle:
    key = (name or "").strip().lower()
    if key not in _REGISTRY:
        allowed = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown naming style '{name}'. Allowed: {allowed}"
        )
    return _REGISTRY[key]()

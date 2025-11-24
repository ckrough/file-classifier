"""NamingStyle interface and shared type hints."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Pattern

from src.analysis.models import NormalizedMetadata


class NamingStyle(ABC):
    """Interface for naming styles.

    Styles decide both folder components and filename composition. They should not
    perform cross-style validations beyond what is intrinsic to the style (e.g.,
    allowed characters). Structural checks (depth, path length, single period)
    are enforced centrally by the builder.
    """

    @abstractmethod
    def folder_components(self, normalized: NormalizedMetadata) -> list[str]:
        """Return the list of folder names (without separators)."""

    @abstractmethod
    def filename(self, normalized: NormalizedMetadata, ext: str) -> str:
        """Return the filename (basename + extension)."""

    @abstractmethod
    def allowed_chars(self) -> Pattern[str]:
        """Regex pattern for allowed characters in names for this style."""

    def options(self) -> dict:
        """Optional advisory options (e.g., target length)."""
        return {}

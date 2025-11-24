"""Utilities for naming styles (TitleCase, pluralization, validation)."""
from __future__ import annotations

import re

# TitleCase for folder segments: replace underscores with spaces, title-case, then restore underscores

def to_title_case(text: str) -> str:
    if not text:
        return text
    words = text.replace("_", " ").split()
    return " ".join(w.capitalize() for w in words).replace(" ", "_")


def pluralize_doctype(doctype: str) -> str:
    # Common irregular plurals mirrored from prior behavior
    irregular = {
        "policy": "Policies",
        "1099": "1099s",
        "1040": "1040s",
        "w2": "W2s",
    }
    lower = doctype.lower()
    if lower in irregular:
        return irregular[lower]
    formatted = to_title_case(doctype)
    if formatted.endswith("s") and not formatted.endswith(("ss", "es", "xs", "zs")):
        return formatted
    if formatted.endswith("y") and len(formatted) > 1 and formatted[-2] not in "aeiou":
        return formatted[:-1] + "ies"
    if formatted.endswith(("s", "x", "z", "ch", "sh")):
        return formatted + "es"
    return formatted + "s"


LOWER_UNDERSCORE_ALLOWED = re.compile(r"^[a-z0-9_-]+$")


def ensure_allowed(text: str, pattern: re.Pattern[str]) -> None:
    if not pattern.match(text):
        bad = {c for c in text if not re.match(r"[a-z0-9_-]", c)}
        raise ValueError(
            f"Invalid characters: {bad}. Only a-z, 0-9, underscores (_), and hyphens (-) allowed."
        )

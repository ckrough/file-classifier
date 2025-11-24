from __future__ import annotations

import re
from src.analysis.models import NormalizedMetadata
from src.naming.styles import NamingStyle
from src.naming.utils import to_title_case, pluralize_doctype, LOWER_UNDERSCORE_ALLOWED, ensure_allowed


class DescriptiveNARAStyle(NamingStyle):
    def __init__(self) -> None:
        self._allowed = LOWER_UNDERSCORE_ALLOWED

    def allowed_chars(self) -> re.Pattern[str]:
        return self._allowed

    def folder_components(self, normalized: NormalizedMetadata) -> list[str]:
        return [
            to_title_case(normalized.domain),
            to_title_case(normalized.category),
            pluralize_doctype(normalized.doctype),
        ]

    def filename(self, normalized: NormalizedMetadata, ext: str) -> str:
        # doctype_vendor[_subject][_YYYY[MM[DD]]][_vNN|_final|_draft].ext
        parts: list[str] = []
        for field_name, value in (
            ("doctype", normalized.doctype),
            ("vendor_name", normalized.vendor_name),
        ):
            if not value:
                raise ValueError(f"Missing required field '{field_name}' for descriptive_nara")
            ensure_allowed(value, self._allowed)
            parts.append(value)
        # subject optional
        if normalized.subject:
            ensure_allowed(normalized.subject, self._allowed)
            parts.append(normalized.subject)
        # date optional but if provided must match regex
        if normalized.date:
            if not re.match(r"^\d{4}(\d{2}(\d{2})?)?$", normalized.date):
                raise ValueError(f"Invalid date format for descriptive_nara: '{normalized.date}'")
            parts.append(normalized.date)
        # version optional
        if normalized.version:
            # version can be vNN, final, draft
            if not re.match(r"^(v\d{2}|final|draft)$", normalized.version):
                raise ValueError(
                    "Invalid version for descriptive_nara: must be vNN, final, or draft"
                )
            parts.append(normalized.version)
        base = "_".join(parts)
        return f"{base}{ext}"

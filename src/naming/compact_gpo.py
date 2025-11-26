from __future__ import annotations

import re
from src.analysis.models import NormalizedMetadata
from src.naming.styles import NamingStyle
from src.naming.utils import (
    to_title_case,
    pluralize_doctype,
    LOWER_UNDERSCORE_ALLOWED,
    ensure_allowed,
)


class CompactGPOStyle(NamingStyle):
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
        # vendor[_{YYYY|YYYYMM|YYYYMMDD}].ext
        vendor = normalized.vendor_name
        if not vendor or vendor.lower() in {"unknown", "n/a", "na", "none", "generic"}:
            raise ValueError(f"Invalid vendor for compact_gpo: '{vendor}'")
        ensure_allowed(vendor, self._allowed)
        base = vendor
        date = normalized.date or ""
        if date:
            if not re.match(r"^\d{4}(\d{2}(\d{2})?)?$", date):
                raise ValueError(f"Invalid date format for compact_gpo: '{date}'")
            base = f"{base}_{date}"
        return f"{base}{ext}"

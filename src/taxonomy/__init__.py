"""Central taxonomy for domains, categories, and doctypes.

This module defines the canonical vocabulary for the directory hierarchy used by
this application, along with helpers to normalize raw values into that
vocabulary.

The intent is that:
- Classification and Standards Enforcement agents *aim* to emit values from
  this vocabulary.
- Code is the final gatekeeper and will canonicalize via aliases or, in strict
  mode, reject unknown values.

Taxonomies are loaded from YAML files in the taxonomies/ directory. The default
taxonomy is 'household', but users can specify a different taxonomy via the
TAXONOMY_NAME environment variable or --taxonomy CLI argument.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Taxonomy directory location
# ---------------------------------------------------------------------------

TAXONOMIES_DIR = Path(__file__).parent.parent.parent / "taxonomies"


# ---------------------------------------------------------------------------
# Data classes for taxonomy configuration
# ---------------------------------------------------------------------------


@dataclass
class CategoryInfo:
    """Information about a category within a domain."""

    name: str
    description: str = ""


@dataclass
class DomainInfo:
    """Information about a domain including its categories."""

    name: str
    description: str = ""
    categories: List[CategoryInfo] = field(default_factory=list)


@dataclass
class DoctypeInfo:
    """Information about a document type."""

    name: str
    description: str = ""


@dataclass
class TaxonomyConfig:
    """Complete taxonomy configuration loaded from a YAML file.

    This includes:
    - Canonical domains with their categories and descriptions
    - Canonical doctypes with descriptions
    - Alias mappings for domains, categories, and doctypes
    """

    name: str
    version: str = "1.0"
    description: str = ""

    # Structured domain information (for prompt generation)
    domains: List[DomainInfo] = field(default_factory=list)

    # Structured doctype information (for prompt generation)
    doctypes: List[DoctypeInfo] = field(default_factory=list)

    # Flat sets for fast lookup (computed from domains/doctypes)
    domain_names: Set[str] = field(default_factory=set)
    category_names: Dict[str, Set[str]] = field(default_factory=dict)
    doctype_names: Set[str] = field(default_factory=set)

    # Alias mappings
    domain_aliases: Dict[str, str] = field(default_factory=dict)
    category_aliases: Dict[Tuple[str, str], str] = field(default_factory=dict)
    doctype_aliases: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Global taxonomy state
# ---------------------------------------------------------------------------

_active_taxonomy: Optional[TaxonomyConfig] = None


def _normalize_token(value: str) -> str:
    """Normalize a taxonomy token for lookup.

    - Strips whitespace
    - Lowercases
    - Replaces spaces and hyphens with underscores
    """
    value = (value or "").strip().lower()
    if not value:
        return ""
    value = value.replace("-", "_").replace(" ", "_")
    return value


def load_taxonomy(name_or_path: str) -> TaxonomyConfig:
    """Load a taxonomy configuration from a YAML file.

    Args:
        name_or_path: Either a taxonomy name (e.g., 'household') which will be
                     looked up in the taxonomies/ directory, or an absolute
                     path to a YAML file.

    Returns:
        TaxonomyConfig: The loaded taxonomy configuration.

    Raises:
        FileNotFoundError: If the taxonomy file does not exist.
        ValueError: If the YAML file is invalid or missing required fields.
    """
    # Determine the file path
    if Path(name_or_path).is_absolute():
        config_path = Path(name_or_path)
    else:
        config_path = TAXONOMIES_DIR / f"{name_or_path}.yaml"
        if not config_path.exists():
            config_path = TAXONOMIES_DIR / f"{name_or_path}.yml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Taxonomy file not found: {config_path}\n"
            f"  → Available taxonomies: {list_available_taxonomies()}"
        )

    logger.info("Loading taxonomy from: %s", config_path)

    # Load YAML
    try:
        import yaml
    except ImportError as e:
        raise ImportError(
            "PyYAML is required for taxonomy loading. Install with: pip install pyyaml"
        ) from e

    text = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid taxonomy file: expected dict, got {type(data)}")

    # Parse the taxonomy
    return _parse_taxonomy_data(data, config_path.stem)


def _parse_taxonomy_data(data: dict, default_name: str) -> TaxonomyConfig:
    """Parse a taxonomy dictionary into a TaxonomyConfig."""
    config = TaxonomyConfig(
        name=data.get("name", default_name),
        version=str(data.get("version", "1.0")),
        description=data.get("description", ""),
    )

    _parse_domains_section(data, config)
    _parse_doctypes_section(data, config)
    _parse_aliases_section(data, config)

    logger.debug(
        "Loaded taxonomy '%s': %d domains, %d doctypes, %d domain aliases, "
        "%d category aliases, %d doctype aliases",
        config.name,
        len(config.domain_names),
        len(config.doctype_names),
        len(config.domain_aliases),
        len(config.category_aliases),
        len(config.doctype_aliases),
    )

    return config


def _parse_domains_section(data: dict, config: TaxonomyConfig) -> None:
    """Populate domain structures on the taxonomy config."""
    for domain_data in data.get("domains", []):
        domain_name = _normalize_token(domain_data.get("name", ""))
        if not domain_name:
            continue

        categories: List[CategoryInfo] = []
        config.category_names[domain_name] = set()

        for cat_data in domain_data.get("categories", []):
            cat_name = _normalize_token(cat_data.get("name", ""))
            if not cat_name:
                continue
            categories.append(
                CategoryInfo(
                    name=cat_name,
                    description=cat_data.get("description", ""),
                )
            )
            config.category_names[domain_name].add(cat_name)

        config.domains.append(
            DomainInfo(
                name=domain_name,
                description=domain_data.get("description", ""),
                categories=categories,
            )
        )
        config.domain_names.add(domain_name)


def _parse_doctypes_section(data: dict, config: TaxonomyConfig) -> None:
    """Populate doctype structures on the taxonomy config."""
    for doctype_data in data.get("doctypes", []):
        doctype_name = _normalize_token(doctype_data.get("name", ""))
        if not doctype_name:
            continue
        config.doctypes.append(
            DoctypeInfo(
                name=doctype_name,
                description=doctype_data.get("description", ""),
            )
        )
        config.doctype_names.add(doctype_name)


def _parse_aliases_section(data: dict, config: TaxonomyConfig) -> None:
    """Populate alias mappings on the taxonomy config."""
    aliases_data = data.get("aliases", {})

    # Domain aliases
    for alias, canonical in aliases_data.get("domains", {}).items():
        alias_normalized = _normalize_token(alias)
        canonical_normalized = _normalize_token(canonical)
        if alias_normalized and canonical_normalized:
            config.domain_aliases[alias_normalized] = canonical_normalized

    # Category aliases
    for cat_alias in aliases_data.get("categories", []):
        domain = _normalize_token(cat_alias.get("domain", ""))
        alias = _normalize_token(cat_alias.get("alias", ""))
        canonical = _normalize_token(cat_alias.get("canonical", ""))
        if domain and alias and canonical:
            config.category_aliases[(domain, alias)] = canonical

    # Doctype aliases
    for alias, canonical in aliases_data.get("doctypes", {}).items():
        alias_normalized = _normalize_token(alias)
        canonical_normalized = _normalize_token(canonical)
        if alias_normalized and canonical_normalized:
            config.doctype_aliases[alias_normalized] = canonical_normalized


def list_available_taxonomies() -> List[str]:
    """List available taxonomy names from the taxonomies directory."""
    if not TAXONOMIES_DIR.exists():
        return []
    taxonomies = []
    for path in TAXONOMIES_DIR.iterdir():
        if path.suffix in {".yaml", ".yml"} and path.is_file():
            taxonomies.append(path.stem)
    return sorted(taxonomies)


def set_taxonomy(name_or_path: str) -> TaxonomyConfig:
    """Set the active taxonomy by name or path.

    Args:
        name_or_path: Either a taxonomy name (e.g., 'household') or an
                     absolute path to a YAML file.

    Returns:
        TaxonomyConfig: The newly active taxonomy configuration.
    """
    global _active_taxonomy
    _active_taxonomy = load_taxonomy(name_or_path)
    logger.info(
        "Active taxonomy set to: %s (v%s)",
        _active_taxonomy.name,
        _active_taxonomy.version,
    )
    return _active_taxonomy


def get_active_taxonomy() -> TaxonomyConfig:
    """Get the currently active taxonomy configuration.

    If no taxonomy has been explicitly set, loads the default 'household'
    taxonomy.

    Returns:
        TaxonomyConfig: The active taxonomy configuration.
    """
    global _active_taxonomy
    if _active_taxonomy is None:
        # Load default taxonomy
        from src.config import settings

        default_name = getattr(settings, "TAXONOMY_NAME", "household")
        _active_taxonomy = load_taxonomy(default_name)
    return _active_taxonomy


def reset_taxonomy() -> None:
    """Reset the active taxonomy to None, forcing reload on next access.

    This is primarily useful for testing.
    """
    global _active_taxonomy
    _active_taxonomy = None


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def canonical_domain(raw: str) -> Optional[str]:
    """Resolve a raw domain string to a canonical domain slug.

    Returns None if no suitable canonical value can be found.
    """
    token = _normalize_token(raw)
    if not token:
        return None

    taxonomy = get_active_taxonomy()

    if token in taxonomy.domain_names:
        return token

    alias = taxonomy.domain_aliases.get(token)
    if alias and alias in taxonomy.domain_names:
        return alias

    return None


def canonical_category(domain: str, raw: str) -> Optional[str]:
    """Resolve a raw category string to a canonical category for the domain.

    Returns None if no suitable canonical value can be found.
    """
    dom = canonical_domain(domain) or _normalize_token(domain)
    if not dom:
        return None

    token = _normalize_token(raw)
    if not token:
        return None

    taxonomy = get_active_taxonomy()
    categories = taxonomy.category_names.get(dom, set())

    if token in categories:
        return token

    alias = taxonomy.category_aliases.get((dom, token))
    if alias and alias in categories:
        return alias

    return None


def canonical_doctype(raw: str) -> Optional[str]:
    """Resolve a raw doctype string to a canonical doctype slug.

    Returns None if no suitable canonical value can be found.
    """
    token = _normalize_token(raw)
    if not token:
        return None

    taxonomy = get_active_taxonomy()

    if token in taxonomy.doctype_names:
        return token

    alias = taxonomy.doctype_aliases.get(token)
    if alias and alias in taxonomy.doctype_names:
        return alias

    return None


# ---------------------------------------------------------------------------
# XML snippet generation for prompt injection
# ---------------------------------------------------------------------------


def generate_taxonomy_xml(config: Optional[TaxonomyConfig] = None) -> str:
    """Generate an XML snippet of the taxonomy for prompt injection.

    This produces an XML fragment matching the <taxonomy> structure expected
    by the classification and standards enforcement agent prompts.

    Args:
        config: The taxonomy configuration to use. If None, uses the active
               taxonomy.

    Returns:
        str: An XML string suitable for injection into prompt templates.
    """
    if config is None:
        config = get_active_taxonomy()

    lines = ["<taxonomy>", "    <domains>"]

    for domain in config.domains:
        if domain.description:
            lines.append(
                "      "
                f'<domain name="{domain.name}" '
                f'description="{_escape_xml(domain.description)}">'
            )
        else:
            lines.append(f'      <domain name="{domain.name}">')

        for category in domain.categories:
            if category.description:
                lines.append(
                    "        "
                    f'<category name="{category.name}">'  # noqa: S308
                    f"{_escape_xml(category.description)}"
                    "</category>"
                )
            else:
                lines.append(f'        <category name="{category.name}"/>')

        lines.append("      </domain>")

    lines.append("    </domains>")
    lines.append("")
    lines.append("    <doctypes>")

    for doctype in config.doctypes:
        if doctype.description:
            lines.append(
                "      "
                f'<doctype name="{doctype.name}">'  # noqa: S308
                f"{_escape_xml(doctype.description)}"
                "</doctype>"
            )
        else:
            lines.append(f'      <doctype name="{doctype.name}"/>')

    lines.append("    </doctypes>")
    lines.append("  </taxonomy>")

    return "\n".join(lines)


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------------------------------------------------------------------
# Backward-compatible exports
# ---------------------------------------------------------------------------

# These are provided for backward compatibility with code that directly
# imports the constants. They delegate to the active taxonomy.


def _get_canonical_domains() -> Set[str]:
    """Get canonical domains from active taxonomy (for backward compatibility)."""
    return get_active_taxonomy().domain_names


def _get_canonical_categories() -> Dict[str, Set[str]]:
    """Get canonical categories from active taxonomy (for backward compatibility)."""
    return get_active_taxonomy().category_names


def _get_canonical_doctypes() -> Set[str]:
    """Get canonical doctypes from active taxonomy (for backward compatibility)."""
    return get_active_taxonomy().doctype_names


def _get_domain_aliases() -> Dict[str, str]:
    """Get domain aliases from active taxonomy (for backward compatibility)."""
    return get_active_taxonomy().domain_aliases


def _get_category_aliases() -> Dict[Tuple[str, str], str]:
    """Get category aliases from active taxonomy (for backward compatibility)."""
    return get_active_taxonomy().category_aliases


def _get_doctype_aliases() -> Dict[str, str]:
    """Get doctype aliases from active taxonomy (for backward compatibility)."""
    return get_active_taxonomy().doctype_aliases


__all__ = [
    # Core API
    "TaxonomyConfig",
    "DomainInfo",
    "CategoryInfo",
    "DoctypeInfo",
    "load_taxonomy",
    "set_taxonomy",
    "get_active_taxonomy",
    "reset_taxonomy",
    "list_available_taxonomies",
    # Normalization functions
    "canonical_domain",
    "canonical_category",
    "canonical_doctype",
    # XML generation
    "generate_taxonomy_xml",
    # Backward compatibility (use get_active_taxonomy() for dynamic access)
    "_get_canonical_domains",
    "_get_canonical_categories",
    "_get_canonical_doctypes",
    "_get_domain_aliases",
    "_get_category_aliases",
    "_get_doctype_aliases",
]

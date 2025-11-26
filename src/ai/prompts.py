"""
Prompt management using LangChain templates.

This module provides access to LangChain ChatPromptTemplate objects
loaded from XML files in the prompts/ directory.

Supports the multi-agent document processing prompts:
- classification-agent
- standards-enforcement-agent
- path-construction-agent
- conflict-resolution-agent

Prompts can include a <!-- TAXONOMY_SNIPPET --> placeholder that will be
replaced with the active taxonomy's XML representation at load time.
"""

import logging
import re
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# Prompts directory (relative to project root)
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

# Valid prompt name pattern (lowercase alphanumeric with hyphens)
VALID_PROMPT_NAME = re.compile(r"^[a-z][a-z0-9-]*$")

# Placeholder for taxonomy injection
TAXONOMY_PLACEHOLDER = "<!-- TAXONOMY_SNIPPET -->"


def _inject_taxonomy(content: str) -> str:
    """Replace taxonomy placeholder with the active taxonomy XML.

    If the placeholder is not found, returns the content unchanged.
    """
    if TAXONOMY_PLACEHOLDER not in content:
        return content

    # Import here to avoid circular imports
    from src.taxonomy import generate_taxonomy_xml  # pylint: disable=import-outside-toplevel

    taxonomy_xml = generate_taxonomy_xml()
    logger.debug("Injecting taxonomy XML into prompt (%d chars)", len(taxonomy_xml))
    return content.replace(TAXONOMY_PLACEHOLDER, taxonomy_xml)


def load_prompt_template(prompt_name: str) -> ChatPromptTemplate:
    """
    Load a prompt template from XML files by name.

    Looks for two files in the prompts/ directory:
    - {prompt_name}-system.xml
    - {prompt_name}-user.xml

    Falls back to .txt files for backward compatibility.

    If the prompt contains <!-- TAXONOMY_SNIPPET -->, it will be replaced
    with the active taxonomy's XML representation.

    Args:
        prompt_name (str): The base name of the prompt (alphanumeric with hyphens).
                          Must match pattern: ^[a-z][a-z0-9-]*$

    Returns:
        ChatPromptTemplate: A LangChain prompt template with system and human messages.

    Raises:
        ValueError: If prompt_name contains invalid characters
                   (path traversal prevention).
        FileNotFoundError: If prompt files are missing.
        IOError: If prompt files cannot be read.
    """
    # Validate prompt name to prevent path traversal attacks
    if not VALID_PROMPT_NAME.match(prompt_name):
        logger.error("Invalid prompt name format: %s", prompt_name)
        raise ValueError(
            f"Invalid prompt name: {prompt_name}\n"
            f"  → Prompt names must match pattern: ^[a-z][a-z0-9-]*$\n"
            f"  → Example: 'classification-agent'\n"
            f"  → This prevents path traversal attacks"
        )

    try:
        # Try XML files first
        system_prompt_path = PROMPTS_DIR / f"{prompt_name}-system.xml"
        user_prompt_path = PROMPTS_DIR / f"{prompt_name}-user.xml"

        # Fall back to .txt files for backward compatibility
        if not system_prompt_path.exists():
            system_prompt_path = PROMPTS_DIR / f"{prompt_name}-system.txt"
            if not system_prompt_path.exists():
                system_prompt_path = PROMPTS_DIR / f"{prompt_name}-system-prompt.txt"

        if not user_prompt_path.exists():
            user_prompt_path = PROMPTS_DIR / f"{prompt_name}-user.txt"
            if not user_prompt_path.exists():
                user_prompt_path = PROMPTS_DIR / f"{prompt_name}-user-prompt.txt"

        logger.debug("Loading system prompt from: %s", system_prompt_path)
        system_prompt = system_prompt_path.read_text(encoding="utf-8").strip()

        logger.debug("Loading user prompt from: %s", user_prompt_path)
        user_prompt = user_prompt_path.read_text(encoding="utf-8").strip()

        # Inject taxonomy into prompts if placeholder is present
        system_prompt = _inject_taxonomy(system_prompt)
        user_prompt = _inject_taxonomy(user_prompt)

        # Create ChatPromptTemplate with proper message roles
        # XML content is passed directly - AI models work natively with XML structure
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )

    except FileNotFoundError as e:
        logger.error("Prompt file not found: %s", e)
        raise
    except (IOError, OSError) as e:
        logger.error("Error reading prompt files: %s", e)
        raise


# Cache key includes taxonomy name to invalidate when taxonomy changes
_prompt_cache: dict = {}


def get_prompt_template(prompt_name: str) -> ChatPromptTemplate:
    """
    Get a prompt template by name (cached with lazy loading).

    This function caches prompts per taxonomy to ensure prompts are reloaded
    when the active taxonomy changes.

    Supported prompts:
    - 'classification-agent'
    - 'standards-enforcement-agent'
    - 'path-construction-agent'
    - 'conflict-resolution-agent'

    Args:
        prompt_name (str): The name of the prompt to load.

    Returns:
        ChatPromptTemplate: The requested prompt template.
    """
    # Import here to avoid circular imports
    from src.taxonomy import get_active_taxonomy  # pylint: disable=import-outside-toplevel

    taxonomy = get_active_taxonomy()
    cache_key = (prompt_name, taxonomy.name, taxonomy.version)

    if cache_key not in _prompt_cache:
        prompt = load_prompt_template(prompt_name)
        logger.info(
            "Prompt template '%s' loaded successfully (taxonomy: %s v%s)",
            prompt_name,
            taxonomy.name,
            taxonomy.version,
        )
        _prompt_cache[cache_key] = prompt

    return _prompt_cache[cache_key]


def clear_prompt_cache() -> None:
    """Clear the prompt cache.

    Call this after changing the active taxonomy to force prompts to be
    reloaded with the new taxonomy.
    """
    _prompt_cache.clear()
    logger.debug("Prompt cache cleared")


__all__ = [
    "get_prompt_template",
    "load_prompt_template",
    "clear_prompt_cache",
]

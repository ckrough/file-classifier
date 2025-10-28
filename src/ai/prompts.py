"""
Prompt management using LangChain templates.

This module provides access to LangChain ChatPromptTemplate objects
loaded from text files in the prompts/ directory.

Supports the multi-agent document processing prompts:
- classification-agent
- standards-enforcement-agent
- path-construction-agent
- conflict-resolution-agent
"""

import logging
from functools import lru_cache
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# Prompts directory (relative to project root)
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt_template(prompt_name: str) -> ChatPromptTemplate:
    """
    Load a prompt template from text files by name.

    Looks for two files in the prompts/ directory:
    - {prompt_name}-system.txt (or {prompt_name}-system-prompt.txt)
    - {prompt_name}-user.txt (or {prompt_name}-user-prompt.txt)

    Args:
        prompt_name (str): The base name of the prompt (e.g., 'classification-agent').

    Returns:
        ChatPromptTemplate: A LangChain prompt template with system and human messages.

    Raises:
        FileNotFoundError: If prompt files are missing.
        IOError: If prompt files cannot be read.
    """
    try:
        # Try both naming conventions for backward compatibility
        system_prompt_path = PROMPTS_DIR / f"{prompt_name}-system.txt"
        if not system_prompt_path.exists():
            system_prompt_path = PROMPTS_DIR / f"{prompt_name}-system-prompt.txt"

        user_prompt_path = PROMPTS_DIR / f"{prompt_name}-user.txt"
        if not user_prompt_path.exists():
            user_prompt_path = PROMPTS_DIR / f"{prompt_name}-user-prompt.txt"

        logger.debug("Loading system prompt from: %s", system_prompt_path)
        system_prompt = system_prompt_path.read_text(encoding="utf-8").strip()

        logger.debug("Loading user prompt from: %s", user_prompt_path)
        user_prompt = user_prompt_path.read_text(encoding="utf-8").strip()

        # Create ChatPromptTemplate with proper message roles
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


@lru_cache(maxsize=10)
def get_prompt_template(prompt_name: str) -> ChatPromptTemplate:
    """
    Get a prompt template by name (cached with lazy loading).

    This function uses lru_cache to ensure each prompt is loaded only once
    and reused across multiple calls, providing singleton-like behavior.

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
    prompt = load_prompt_template(prompt_name)
    logger.info("Prompt template '%s' loaded successfully", prompt_name)
    return prompt


__all__ = [
    "get_prompt_template",
    "load_prompt_template",
]

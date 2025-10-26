"""
Prompt management using LangChain templates.

This module provides access to LangChain ChatPromptTemplate objects
loaded from text files in the prompts/ directory.
"""

import logging
from pathlib import Path
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# Prompts directory (relative to project root)
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_file_analysis_prompt() -> ChatPromptTemplate:
    """
    Load the file analysis prompt template from text files.

    Returns:
        ChatPromptTemplate: A LangChain prompt template with system and human messages.

    Raises:
        FileNotFoundError: If prompt files are missing.
        IOError: If prompt files cannot be read.
    """
    try:
        system_prompt_path = PROMPTS_DIR / "file-analysis-system-prompt.txt"
        user_prompt_path = PROMPTS_DIR / "file-analysis-user-prompt.txt"

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


# Singleton instance (lazy-loaded)
_file_analysis_prompt: Optional[ChatPromptTemplate] = None


def get_file_analysis_prompt() -> ChatPromptTemplate:
    """
    Get the file analysis prompt template (singleton with lazy loading).

    Returns:
        ChatPromptTemplate: The file analysis prompt template.
    """
    global _file_analysis_prompt
    if _file_analysis_prompt is None:
        _file_analysis_prompt = load_file_analysis_prompt()
        logger.info("File analysis prompt template loaded successfully")
    return _file_analysis_prompt


__all__ = ["get_file_analysis_prompt", "load_file_analysis_prompt"]

"""
Module for loading and formatting AI prompts.

This module provides the `load_and_format_prompt` function, which loads a prompt template
from a specified file and formats it with the provided keyword arguments. It includes
robust error handling to ensure graceful failure and informative logging in case of issues.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["load_and_format_prompt"]


def load_and_format_prompt(file_path: str, **kwargs: Any) -> str:
    """
    Load a prompt from a file and format it with the given keyword arguments.

    Args:
        file_path (str): The path to the prompt file.
        **kwargs: Keyword arguments for formatting the prompt.

    Returns:
        str: The formatted prompt or an empty string if an error occurs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt: str = file.read()
        return prompt.format(**kwargs)
    except FileNotFoundError:
        logger.error("Prompt file not found: %s", file_path)
    except PermissionError:
        logger.error("Permission denied when accessing prompt file: %s",
                     file_path)
    except IOError as e:
        logger.error("IO error when reading prompt file: %s", e)
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        logger.error("Unexpected error loading or formatting prompt: %s", e)
    return ""

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
    formatted_prompt = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt = file.read().strip()
        prompt = ' '.join(prompt.split())
        if kwargs:
            formatted_prompt = prompt.format(**kwargs)
        else:
            formatted_prompt = prompt
    except PermissionError as err:
        logger.error("Permission denied when accessing prompt file %s: %s", file_path, err)
    except (IOError, OSError) as err:
        logger.error("Error reading prompt file %s: %s", file_path, err)
    except KeyError as ke:
        missing_key = ke.args[0]
        logger.error("Missing required keyword argument '%s' in prompt file %s", missing_key, file_path)
    except ValueError as ve:
        logger.error(
            "Value error formatting prompt from %s: %s. Ensure that literal braces are escaped (i.e. use double braces '{{' and '}}').",
            file_path,
            ve,
        )
    except (TypeError, AttributeError) as e:
        logger.error("Unexpected error formatting prompt from %s: %s", file_path, e)
        logger.debug("Prompt content: %r, Arguments: %r", prompt, kwargs)

    return formatted_prompt

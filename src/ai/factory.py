"""
AI Client Factory.

This module provides factory functions for creating AI client instances
based on configuration.
"""

import os
import logging
from typing import Optional

from src.ai.client import AIClient, LangChainClient

__all__ = ["create_ai_client"]

logger = logging.getLogger(__name__)


def create_ai_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs,
) -> AIClient:
    """
    Factory function to create an AI client based on provider configuration.

    Uses LangChain for multi-provider support with structured outputs.

    Args:
        provider (str, optional): The LLM provider ('openai', 'ollama', etc.).
            Defaults to AI_PROVIDER env var or 'openai'.
        model (str, optional): Model name. Defaults based on provider.
        api_key (str, optional): API key for the provider.
        base_url (str, optional): Base URL for the provider API.
        **kwargs: Additional provider-specific arguments.

    Returns:
        AIClient: An initialized LangChainClient instance.

    Examples:
        # Use OpenAI via LangChain (default)
        client = create_ai_client()

        # Use local Ollama with DeepSeek
        client = create_ai_client(provider="ollama", model="deepseek-r1:latest")

        # Use specific OpenAI model
        client = create_ai_client(provider="openai", model="gpt-4")
    """
    # Default to OpenAI provider if not specified
    if provider is None:
        provider = os.getenv("AI_PROVIDER", "openai")

    logger.info("Creating AI client with provider: %s", provider)

    return LangChainClient(
        provider=provider, model=model, api_key=api_key, base_url=base_url, **kwargs
    )

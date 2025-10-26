"""
Module for AI Client Abstractions.

This module defines the abstract base class `AIClient` and its concrete
implementations for interfacing with AI models to analyze file content.

Classes:
    AIClient: Abstract base class outlining the interface for AI clients.
    OpenAIClient: Legacy implementation using OpenAI's deprecated function calling API.
    LangChainClient: Modern implementation using LangChain for multi-provider support.
"""

import os
import logging
from abc import ABC, abstractmethod
import json
from typing import Optional

from pydantic import ValidationError
from openai import OpenAI, OpenAIError
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from src.ai_file_classifier.models import Analysis
__all__ = ["AIClient", "OpenAIClient", "LangChainClient", "create_ai_client"]

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI clients."""

    # pylint: disable=too-few-public-methods
    # This class intentionally has few public methods as it serves as an interface.

    @abstractmethod
    def analyze_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: Optional[int] = None,
    ) -> Analysis:
        """
        Analyze the content using the AI model.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str): The user prompt for the AI.
            model (str): The AI model to use.
            max_tokens (int): The maximum number of tokens for the response.

        Returns:
            Analysis: The analyzed metadata of the file.
        """


class OpenAIClient(AIClient):
    """Concrete implementation of AIClient using OpenAI."""

    # pylint: disable=too-few-public-methods

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI client with the API key from environment variables."""
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.critical(
                "OPENAI_API_KEY not provided or set in environment variables."
            )
            raise ValueError("OPENAI_API_KEY must be provided.")
        self.client = OpenAI(api_key=api_key)

    def analyze_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: Optional[int] = None
    ) -> Analysis:
        """
        Analyze the content using OpenAI's ChatCompletion API.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str): The user prompt for the AI.
            model (str): The AI model to use (e.g., 'gpt-4').
            max_tokens (int, optional): The maximum number of tokens for the response. If not provided,
                defaults to the value of the OPENAI_MAX_TOKENS environment variable (default: 50).

        Returns:
            Analysis: The analyzed metadata of the file.

        Raises:
            RuntimeError: If there's an error communicating with the OpenAI API.
        """
        try:
            if max_tokens is None:
                try:
                    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "50"))
                except ValueError as ve:
                    logger.error(
                        "Invalid OPENAI_MAX_TOKENS environment variable value: %s",
                        os.getenv("OPENAI_MAX_TOKENS")
                    )
                    raise ValueError("OPENAI_MAX_TOKENS must be an integer.") from ve

            functions = [
                {
                    "name": "parse_analysis",
                    "description": "Parses file content analysis into a structured format.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "File category"},
                            "vendor": {"type": "string", "description": "File vendor"},
                            "description": {"type": "string", "description": "File description"},
                            "date": {"type": "string", "description": "File date (optional)"}
                        },
                        "required": ["category", "vendor", "description"]
                    }
                }
            ]

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                functions=functions,
                function_call={"name": "parse_analysis"},
                max_tokens=max_tokens,
            )

            # Retrieve the structured output from the function call field
            function_call_resp = response.choices[0].message.function_call
            if not function_call_resp or not hasattr(function_call_resp, "arguments"):
                logger.error("Structured output not provided by API: %s", response)
                raise RuntimeError("Structured output not provided by API.")

            arguments = json.loads(function_call_resp.arguments)
            analysis = Analysis.parse_obj(arguments)
            return analysis
        except ValidationError as ve:
            logger.error(
                "Validation error while parsing Analysis: %s", ve, exc_info=True
            )
            raise RuntimeError("Validation error while parsing Analysis.") from ve
        except OpenAIError as e:
            logger.exception("Error communicating with OpenAI API.")
            raise RuntimeError("Error communicating with OpenAI API.") from e


class LangChainClient(AIClient):
    """
    Modern implementation of AIClient using LangChain for multi-provider support.

    Supports multiple LLM providers through LangChain's unified interface:
    - OpenAI (ChatOpenAI)
    - Ollama for local models (ChatOllama)
    - Extensible to other providers (Anthropic, Google, etc.)

    Uses structured output extraction via LangChain's with_structured_output().
    """

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the LangChain client with specified provider.

        Args:
            provider (str): The LLM provider to use ('openai', 'ollama', etc.).
            model (str, optional): The model name. Defaults based on provider.
            api_key (str, optional): API key for the provider (if required).
            base_url (str, optional): Base URL for the provider API.
            **kwargs: Additional provider-specific arguments.

        Raises:
            ValueError: If provider is unsupported or required credentials are missing.
        """
        self.provider = provider.lower()
        self.llm = self._initialize_llm(model, api_key, base_url, **kwargs)

    def _initialize_llm(
        self,
        model: Optional[str],
        api_key: Optional[str],
        base_url: Optional[str],
        **kwargs
    ) -> BaseChatModel:
        """
        Initialize the appropriate LangChain LLM based on provider.

        Args:
            model (str, optional): Model name.
            api_key (str, optional): API key.
            base_url (str, optional): Base URL.
            **kwargs: Additional provider-specific arguments.

        Returns:
            BaseChatModel: Initialized LangChain chat model.

        Raises:
            ValueError: If provider is unsupported or configuration is invalid.
        """
        if self.provider == "openai":
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.critical("OPENAI_API_KEY not provided or set in environment variables.")
                raise ValueError("OPENAI_API_KEY must be provided for OpenAI provider.")

            model = model or os.getenv("AI_MODEL", "gpt-4o-mini")
            logger.info("Initializing ChatOpenAI with model: %s", model)
            return ChatOpenAI(api_key=api_key, model=model, **kwargs)

        if self.provider == "ollama":
            base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = model or os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")
            logger.info("Initializing ChatOllama with model: %s at %s", model, base_url)
            return ChatOllama(model=model, base_url=base_url, **kwargs)

        # Future providers can be added here (anthropic, google, etc.)
        logger.error("Unsupported provider: %s", self.provider)
        raise ValueError(f"Unsupported provider: {self.provider}")

    def analyze_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: Optional[int] = None
    ) -> Analysis:
        """
        Analyze the content using LangChain's structured output extraction.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str): The user prompt for the AI.
            model (str): The AI model to use (used for compatibility, actual model set in __init__).
            max_tokens (int, optional): The maximum number of tokens for the response.

        Returns:
            Analysis: The analyzed metadata of the file.

        Raises:
            RuntimeError: If there's an error during analysis.
        """
        try:
            # Create a structured output chain using the Analysis Pydantic model
            structured_llm = self.llm.with_structured_output(Analysis)

            # Combine system and user prompts into a single message
            # LangChain expects a list of messages or a single prompt string
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Invoke the LLM with structured output
            logger.debug("Invoking LLM with provider: %s", self.provider)
            analysis = structured_llm.invoke(full_prompt)

            logger.debug("LLM returned structured analysis: %s", analysis)
            return analysis

        except ValidationError as ve:
            logger.error(
                "Validation error while parsing Analysis: %s", ve, exc_info=True
            )
            raise RuntimeError("Validation error while parsing Analysis.") from ve
        except Exception as e:
            logger.exception("Error communicating with LLM provider: %s", self.provider)
            raise RuntimeError(f"Error communicating with {self.provider} API.") from e


def create_ai_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    use_langchain: bool = True,
    **kwargs
) -> AIClient:
    """
    Factory function to create an AI client based on provider configuration.

    Args:
        provider (str, optional): The LLM provider ('openai', 'ollama', etc.).
            Defaults to AI_PROVIDER env var or 'openai'.
        model (str, optional): Model name. Defaults based on provider.
        api_key (str, optional): API key for the provider.
        base_url (str, optional): Base URL for the provider API.
        use_langchain (bool): Whether to use LangChainClient (default: True).
            Set to False to use legacy OpenAIClient.
        **kwargs: Additional provider-specific arguments.

    Returns:
        AIClient: An initialized AI client instance.

    Examples:
        # Use OpenAI via LangChain (default)
        client = create_ai_client()

        # Use local Ollama with DeepSeek
        client = create_ai_client(provider="ollama", model="deepseek-r1:latest")

        # Use legacy OpenAI client
        client = create_ai_client(use_langchain=False)
    """
    # Default to OpenAI provider if not specified
    if provider is None:
        provider = os.getenv("AI_PROVIDER", "openai")

    logger.info("Creating AI client with provider: %s, use_langchain: %s", provider, use_langchain)

    # Use legacy OpenAIClient if explicitly requested
    if not use_langchain and provider == "openai":
        logger.info("Using legacy OpenAIClient")
        return OpenAIClient(api_key=api_key)

    # Use modern LangChainClient (default)
    return LangChainClient(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )

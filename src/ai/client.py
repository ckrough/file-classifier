"""
AI Client Abstractions.

This module defines the abstract base class `AIClient` and its concrete
implementation for interfacing with AI models to analyze file content.

Classes:
    AIClient: Abstract base class outlining the interface for AI clients.
    LangChainClient: Implementation using LangChain for multi-provider support
                     with structured outputs.
"""

import os
import logging
import time
from abc import ABC, abstractmethod
from typing import NoReturn, Optional, TypeVar, overload

from pydantic import BaseModel, ValidationError
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from src.analysis.models import Analysis

# TypeVar for generic schema support in analyze_content
# Using 'T' prefix per PEP 8 naming convention for TypeVars
T = TypeVar("T", bound=BaseModel)

__all__ = ["AIClient", "LangChainClient"]

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI clients."""

    # pylint: disable=too-few-public-methods
    # This class intentionally has few public methods as it serves as an interface.

    @overload
    def analyze_content(
        self,
        prompt_template: ChatPromptTemplate,
        prompt_values: dict,
        schema: None = None,
    ) -> Analysis:
        """Overload for default Analysis schema."""

    @overload
    def analyze_content(
        self,
        prompt_template: ChatPromptTemplate,
        prompt_values: dict,
        schema: type[T],
    ) -> T:
        """Overload for custom schema."""

    @abstractmethod
    def analyze_content(
        self,
        prompt_template: ChatPromptTemplate,
        prompt_values: dict,
        schema: Optional[type[T]] = None,
    ) -> Analysis | T:
        """
        Analyze the content using the AI model with a prompt template.

        This method uses type overloads to provide proper type safety:
        - When schema=None (default), returns Analysis
        - When schema=SomeModel, returns SomeModel instance

        Args:
            prompt_template (ChatPromptTemplate): LangChain prompt template.
            prompt_values (dict): Variables to format into the template.
            schema (type[BaseModel], optional): Pydantic model class for
                structured output. If None, uses Analysis (legacy behavior).

        Returns:
            Analysis | T: The analyzed metadata in the requested format.
                Type checkers infer the correct type based on schema param.
        """


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
        **kwargs,
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

        # Cache structured output chain for legacy Analysis model
        # (for backward compatibility with existing code)
        self.structured_llm = self.llm.with_structured_output(Analysis)
        logger.debug("Cached structured output chain for Analysis model")

    def _initialize_llm(
        self,
        model: Optional[str],
        api_key: Optional[str],
        base_url: Optional[str],
        **kwargs,
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
                logger.critical(
                    "OPENAI_API_KEY not found in environment or parameters."
                )
                error_msg = (
                    "OPENAI_API_KEY is required for OpenAI provider.\n"
                    "  → Set environment variable: export OPENAI_API_KEY=sk-...\n"
                    "  → Or add to .env file: OPENAI_API_KEY=sk-..."
                )
                raise ValueError(error_msg)

            model = model or os.getenv("AI_MODEL", "gpt-4o-mini")
            logger.info("Initializing ChatOpenAI with model: %s", model)
            return ChatOpenAI(api_key=api_key, model=model, **kwargs)

        if self.provider == "ollama":
            base_url = base_url or os.getenv(
                "OLLAMA_BASE_URL", "http://localhost:11434"
            )
            model = model or os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")
            logger.info("Initializing ChatOllama with model: %s at %s", model, base_url)
            return ChatOllama(model=model, base_url=base_url, **kwargs)

        # Future providers can be added here (anthropic, google, etc.)
        logger.error("Unsupported provider: %s", self.provider)
        error_msg = (
            f"Unsupported AI provider: {self.provider}\n"
            f"  → Supported providers: 'openai', 'ollama'\n"
            f"  → Set AI_PROVIDER in .env file"
        )
        raise ValueError(error_msg)

    @overload
    def analyze_content(
        self,
        prompt_template: ChatPromptTemplate,
        prompt_values: dict,
        schema: None = None,
    ) -> Analysis:
        """Overload for default Analysis schema."""

    # pylint: disable=signature-differs
    # Signature intentionally differs due to @overload providing type safety
    @overload
    def analyze_content(
        self,
        prompt_template: ChatPromptTemplate,
        prompt_values: dict,
        schema: type[T],
    ) -> T:
        """Overload for custom schema."""

    # pylint: disable=signature-differs
    def analyze_content(
        self,
        prompt_template: ChatPromptTemplate,
        prompt_values: dict,
        schema: Optional[type[T]] = None,
    ) -> Analysis | T:
        """
        Analyze content using LangChain's structured output extraction.

        Supports dynamic schema selection for multi-agent workflows. If no
        schema is provided, uses the cached Analysis schema for backward
        compatibility.

        This method uses type overloads to provide proper type safety:
        - When schema=None (default), returns Analysis
        - When schema=SomeModel, returns SomeModel instance

        Args:
            prompt_template (ChatPromptTemplate): LangChain prompt.
            prompt_values (dict): Variables for template (filename, content).
            schema (type[BaseModel], optional): Pydantic model class for
                structured output. If None, uses Analysis (legacy behavior).

        Returns:
            Analysis | T: The analyzed metadata in the requested format.
                Type checkers infer correct type based on schema parameter.

        Raises:
            RuntimeError: If there's an error during analysis.
        """
        start_time = time.perf_counter()
        schema_name = schema.__name__ if schema else "Analysis"

        try:
            # Format the prompt template with the provided values
            # This creates proper SystemMessage and HumanMessage objects
            messages = prompt_template.format_messages(**prompt_values)

            logger.debug("Formatted prompt with values: %s", list(prompt_values.keys()))
            logger.debug("Invoking %s LLM for schema: %s", self.provider, schema_name)

            # Use custom schema if provided, otherwise use cached Analysis schema
            if schema is not None:
                logger.debug("Using custom schema: %s", schema.__name__)
                structured_llm = self.llm.with_structured_output(schema)
                result = structured_llm.invoke(messages)
            else:
                # Use cached structured LLM chain (initialized in __init__)
                result = self.structured_llm.invoke(messages)

            elapsed = time.perf_counter() - start_time
            logger.info("LLM analysis completed for %s (%.2fs)", schema_name, elapsed)
            logger.debug("LLM returned structured result: %s", result)
            return result

        except KeyError as ke:
            self._handle_key_error(ke, start_time, prompt_values)
        except ValidationError as ve:
            self._handle_validation_error(ve, start_time, schema_name)
        except ConnectionError as ce:
            self._handle_connection_error(ce, start_time)
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Intentional catch-all for unexpected errors with specific guidance
            self._handle_generic_error(e, start_time)

    def _handle_key_error(
        self, error: KeyError, start_time: float, prompt_values: dict
    ) -> NoReturn:
        """Handle missing prompt variable errors."""
        elapsed = time.perf_counter() - start_time
        logger.error(
            "Missing required prompt variable: %s (failed after %.2fs). "
            "Available variables: %s",
            error.args[0],
            elapsed,
            list(prompt_values.keys()),
        )
        error_msg = (
            f"Missing required prompt variable: {error.args[0]}\n"
            f"  → Check prompt template for required variables\n"
            f"  → Available: {', '.join(prompt_values.keys())}"
        )
        raise RuntimeError(error_msg) from error

    def _handle_validation_error(
        self, error: ValidationError, start_time: float, schema_name: str
    ) -> NoReturn:
        """Handle Pydantic validation errors from LLM output."""
        elapsed = time.perf_counter() - start_time
        logger.error(
            "LLM output validation failed for %s (failed after %.2fs): %s",
            schema_name,
            elapsed,
            error,
            exc_info=True,
        )
        error_msg = (
            f"LLM returned invalid {schema_name} data.\n"
            f"  → The LLM may not support structured output correctly\n"
            f"  → Try a different model or check prompt template\n"
            f"  → Validation errors: {error.error_count()} field(s)"
        )
        raise RuntimeError(error_msg) from error

    def _handle_connection_error(
        self, error: ConnectionError, start_time: float
    ) -> NoReturn:
        """Handle network connection errors."""
        elapsed = time.perf_counter() - start_time
        logger.error(
            "Network error connecting to %s (failed after %.2fs): %s",
            self.provider,
            elapsed,
            error,
            exc_info=True,
        )
        if self.provider == "ollama":
            error_msg = (
                f"Failed to connect to Ollama server (after {elapsed:.1f}s).\n"
                f"  → Is Ollama running? Try: ollama serve\n"
                f"  → Check OLLAMA_BASE_URL in .env (current: "
                f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')})\n"
                f"  → Verify the server is accessible"
            )
        else:
            error_msg = (
                f"Network error connecting to {self.provider} "
                f"(after {elapsed:.1f}s).\n"
                f"  → Check your internet connection\n"
                f"  → Verify {self.provider} service is available"
            )
        raise RuntimeError(error_msg) from error

    def _handle_generic_error(self, error: Exception, start_time: float) -> NoReturn:
        """Handle unexpected errors with specific guidance based on error type."""
        elapsed = time.perf_counter() - start_time
        error_type = type(error).__name__
        logger.exception(
            "Unexpected error with %s provider (failed after %.2fs): %s",
            self.provider,
            elapsed,
            error_type,
        )

        # Provide specific guidance based on error type
        error_str = str(error).lower()
        if "auth" in error_str or "401" in str(error):
            error_msg = (
                f"Authentication failed with {self.provider} "
                f"(after {elapsed:.1f}s).\n"
                f"  → Verify your API key is correct\n"
                f"  → Check API key has not expired\n"
                f"  → Ensure sufficient API credits/quota"
            )
        elif "timeout" in error_str:
            error_msg = (
                f"Request timeout with {self.provider} "
                f"(after {elapsed:.1f}s).\n"
                f"  → The model may be slow to respond\n"
                f"  → Try a faster model\n"
                f"  → Check network connection"
            )
        else:
            error_msg = (
                f"Error communicating with {self.provider} "
                f"(after {elapsed:.1f}s): {error_type}\n"
                f"  → Check logs for details\n"
                f"  → Verify {self.provider} configuration\n"
                f"  → Error: {str(error)[:200]}"
            )
        raise RuntimeError(error_msg) from error

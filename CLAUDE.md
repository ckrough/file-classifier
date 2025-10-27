# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered document classification and organization system that analyzes text and PDF files to suggest standardized filenames based on content. Uses LangChain for multi-provider LLM support (OpenAI, Ollama) with structured output extraction via Pydantic models.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -e ".[dev]"
```

### Running the Application
```bash
# Analyze a single file
python main.py <path_to_file>

# Analyze a directory
python main.py <path_to_directory>

# Auto-rename without confirmation
python main.py <path> --auto-rename

# Dry run (show changes without applying)
python main.py <path> --dry-run
```

### Testing
```bash
# Run all tests
PYTHONPATH=/Users/crow/Documents/code/file-classifier pytest

# Run specific test file
PYTHONPATH=/Users/crow/Documents/code/file-classifier pytest tests/ai/test_client.py

# Run with coverage
PYTHONPATH=/Users/crow/Documents/code/file-classifier pytest --cov=src --cov-report=term-missing

# Run specific test markers
pytest -m unit          # Unit tests only
pytest -m functional    # Integration tests only
```

### Code Quality
```bash
# Format code (auto-fix)
black .

# Lint code
flake8 src/ tests/

# Run pylint with proper PYTHONPATH
PYTHONPATH=/Users/crow/Documents/code/file-classifier pylint src/

# Security scanning (must specify -c flag; bandit doesn't auto-discover pyproject.toml)
bandit -c pyproject.toml -r src/
```

## Architecture

### Domain-Driven Structure

The codebase follows a domain-driven architecture with clear separation of concerns:

```
src/
├── ai/          # AI provider abstraction and LangChain integration
├── analysis/    # File content analysis and metadata extraction
├── files/       # File operations, processing, and text extraction
├── cli/         # Command-line interface and user interaction
├── config/      # Application configuration and logging
├── recommendations/  # (Reserved for future features)
└── storage/     # (Reserved for future caching/persistence)
```

Tests mirror the `src/` structure exactly (e.g., `tests/ai/` corresponds to `src/ai/`).

### Key Architectural Patterns

**1. Factory Pattern for AI Clients**
- `src/ai/factory.py::create_ai_client()` creates the appropriate LLM client based on `AI_PROVIDER` environment variable
- Currently supports OpenAI (default) and Ollama for local models
- Extensible to additional providers (Anthropic, Google, etc.)

**2. Abstract Base Class for AI Clients**
- `src/ai/client.py::AIClient` defines the interface
- `src/ai/client.py::LangChainClient` implements multi-provider support
- Uses LangChain's `with_structured_output()` for Pydantic model extraction

**3. Structured Output with Pydantic**
- `src/analysis/models.py::Analysis` is the core data model
- LLM responses are automatically validated and parsed into this model
- Ensures type safety and consistent data structure

**4. Workflow Orchestration**
- `main.py` → `src/cli/workflow.py::process_path()` → `src/files/processor.py::process_file()` → `src/analysis/analyzer.py::analyze_file_content()`
- Each layer has a single responsibility and clear boundaries
- `src/cli/display.py` handles all user interaction and output formatting

**5. Prompt Management with LangChain**
- `src/ai/prompts.py::get_file_analysis_prompt()` returns `ChatPromptTemplate` objects
- Uses `@lru_cache` decorator to avoid redundant template parsing
- System and user messages are formatted separately for better LLM understanding

### Data Flow

1. **Input**: User provides file/directory path via CLI (`src/cli/arguments.py`)
2. **AI Client Creation**: Factory creates appropriate LLM client (`src/ai/factory.py`)
3. **File Processing**: Files are validated and text is extracted (`src/files/processor.py`, `src/files/extractors.py`)
4. **Analysis**: Content is sent to LLM with structured prompt (`src/analysis/analyzer.py`)
5. **Structured Output**: LLM response is parsed into `Analysis` Pydantic model
6. **Standardization**: Metadata is normalized (lowercase, hyphens) and filename is generated (`src/analysis/filename.py`)
7. **User Approval**: Changes are displayed and user confirms (`src/cli/display.py`)
8. **Execution**: Files are renamed if approved (`src/files/operations.py`)

## Configuration

### Environment Variables (.env)
```env
# Required
OPENAI_API_KEY=<your_key>           # For OpenAI provider

# Optional
AI_PROVIDER=openai                  # Options: openai, ollama (default: openai)
AI_MODEL=gpt-4o-mini                # Model name (default varies by provider)
OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama
OLLAMA_MODEL=deepseek-r1:latest     # For local Ollama
DEBUG_MODE=false                     # Enable debug logging
```

### Code Quality Configuration

- **Black**: 88 character line length, targets Python 3.11+
- **Flake8**: Configured in `.flake8` (88 chars, ignores E203/W503)
- **Pylint**: Configured in `pyproject.toml` (88 chars, disables C0111/R0903)
- **Pytest**: Optimized for Claude Code with structured output in `conftest.py`

## Important Notes

### PYTHONPATH Requirement
Many commands require `PYTHONPATH` to be set to the project root to ensure proper module imports:
```bash
PYTHONPATH=/Users/crow/Documents/code/file-classifier <command>
```

### Test Structure
- Tests mirror the exact structure of `src/`
- All tests use the `mock_openai_api_key` fixture from `conftest.py` to avoid real API calls
- Claude Code-optimized pytest output includes structured summaries for easier parsing

### Supported File Types
Currently supports:
- `.txt` (text/plain)
- `.pdf` (application/pdf)

Defined in `src/config/settings.py::SUPPORTED_MIMETYPES`

### LangChain Integration
- Prompt templates are created using `ChatPromptTemplate.from_messages()`
- Structured output extraction uses `llm.with_structured_output(Analysis)`
- Messages are formatted before invocation: `prompt_template.format_messages(**values)`

### Recent Architectural Changes
- **Cache Removal**: SQLite caching was removed in favor of in-memory change collection (commit 8dae663)
- **Global State Elimination**: Replaced global statements with `@lru_cache` decorator (commit 8f4b86b)
- **Test Restructuring**: Tests now mirror the domain-driven `src/` structure (commit 26f992f)

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered file classifier that analyzes text and PDF files to suggest intelligent file names and categories. Uses **LangChain** to support multiple LLM providers (OpenAI, local models via Ollama) with structured output extraction to extract metadata (category, vendor, description, date) and generate standardized filenames based on content analysis.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # or .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run a single test file
pytest tests/test_file_analyzer.py

# Run a specific test
pytest tests/test_file_analyzer.py::test_function_name
```

### Linting
```bash
# Run pylint on all source files
pylint src/

# Run pylint on a specific file
pylint src/ai_file_classifier/file_analyzer.py

# Run flake8 (used in CI)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### Running the Application
```bash
# Analyze a single file
python main.py path/to/file.pdf

# Analyze a directory
python main.py path/to/directory

# Dry-run mode (no actual renaming)
python main.py path/to/directory --dry-run

# Auto-rename without user confirmation
python main.py path/to/directory --auto-rename
```

## Architecture

### Core Components

**AIClient Abstraction** (`src/ai_file_classifier/ai_client.py`)
- Abstract base class `AIClient` defines interface for AI providers
- **`LangChainClient`** - Multi-provider implementation using LangChain:
  - Supports OpenAI, Ollama (for local models like DeepSeek), and extensible to other providers
  - Uses LangChain's `with_structured_output()` for clean structured extraction
  - Provider selected via `AI_PROVIDER` environment variable
- **`create_ai_client()`** factory function - Creates LangChainClient based on configuration
- Returns structured `Analysis` Pydantic objects

**Analysis Pipeline**
1. **Text Extraction** (`text_extractor.py`) - Extracts content from .txt and .pdf files
2. **Prompt Management** (`prompt_manager.py`) - Uses LangChain's ChatPromptTemplate for proper message formatting
   - Loads prompts from `prompts/` directory as text files
   - Singleton pattern with lazy loading for performance
   - Supports template variables (filename, content) with validation
3. **AI Analysis** (`file_analyzer.py`) - Coordinates analysis workflow:
   - Gets LangChain prompt template
   - Calls AI client with prompt template and input values
   - Standardizes metadata (lowercase, hyphen-separated)
   - Generates filename: `{vendor}-{category}-{description}-{date}`
4. **File Operations** (`utils.py`) - Handles file processing and renaming

**Cache System** (`src/config/cache_config.py`, `file_inventory.py`)
- SQLite database (`file_cache.db`) stores analyzed file metadata
- Prevents redundant AI analysis of previously processed files
- Cache is deleted on application exit (ephemeral storage)
- Schema: id, file_path, category, description, vendor, date, suggested_name

**Models** (`src/ai_file_classifier/models.py`)
- `Analysis` Pydantic model: category, vendor, description, date (optional)
- Used for validation and type safety throughout the application

### Application Flow

```
main.py
  ↓
get_user_arguments() → parse CLI args (path, --dry-run, --auto-rename)
  ↓
initialize_cache() → create SQLite DB
  ↓
create_ai_client() → initialize LLM client based on AI_PROVIDER
  ↓
process_path() → determine if file or directory
  ↓
process_file() → for each supported file:
  ├─ extract_text_from_{pdf|txt}()
  ├─ get_file_analysis_prompt() → LangChain ChatPromptTemplate
  ├─ AIClient.analyze_content(prompt_template, values) → LangChain structured output
  ├─ standardize_analysis() → lowercase, hyphenate
  └─ generate_filename()
  ↓
handle_suggested_changes() → display suggestions, get user approval
  ↓
rename_files() → apply approved changes
  ↓
delete_cache() → cleanup
```

### Environment Variables

Required in `.env` file:

**General Configuration:**
- `DEBUG_MODE` - Enable debug logging (default: "false")
- `AI_PROVIDER` - LLM provider to use: "openai" or "ollama" (default: "openai")

**OpenAI Configuration** (when `AI_PROVIDER=openai`):
- `OPENAI_API_KEY` - OpenAI API key (required for OpenAI)
- `AI_MODEL` - OpenAI model to use (default: "gpt-4o-mini")

**Ollama Configuration** (when `AI_PROVIDER=ollama`):
- `OLLAMA_BASE_URL` - Ollama server URL (default: "http://localhost:11434")
- `OLLAMA_MODEL` - Model name (default: "deepseek-r1:latest")

**Examples:**

Using OpenAI (cloud):
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
```

Using local Ollama with DeepSeek:
```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:latest
```

### Prompts

Prompts are stored in `prompts/` directory:
- `file-analysis-system-prompt.txt` - System instructions for AI
- `file-analysis-user-prompt.txt` - User prompt template with placeholders for {filename} and {content}

Prompts are loaded via `prompt_manager.py` which uses LangChain's ChatPromptTemplate:
- Proper message role handling (SystemMessage, HumanMessage)
- Template variable validation
- Singleton pattern for performance

## CI/CD

GitHub Actions workflows:
- **python-app.yml** - Runs on push/PR to main:
  - Python 3.10
  - Installs dependencies
  - Runs flake8 linting
  - Runs pytest
- **pylint.yml** - Separate pylint workflow

## Important Notes

- Only `.txt` and `.pdf` files are supported (checked via `is_supported_filetype()`)
- The cache is ephemeral - deleted on exit, not persisted between runs
- File renaming preserves file extension
- Standardization converts category/vendor to lowercase with hyphens (e.g., "Credit Card" → "credit-card")
- **LangChain Integration**: The application uses LangChain for multi-provider LLM support
  - Use `create_ai_client()` factory to initialize the AI client
  - Supports both cloud (OpenAI) and local (Ollama) model providers
  - Local models like DeepSeek can run via Ollama for zero API costs
  - All providers use LangChain's structured output API for reliable metadata extraction

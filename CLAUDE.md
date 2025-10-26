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

# Run domain-specific tests
pytest tests/ai/           # AI client & prompts
pytest tests/analysis/     # Analysis logic
pytest tests/files/        # File operations
pytest tests/storage/      # Database & cache
pytest tests/cli/          # CLI arguments

# Run a specific test
pytest tests/ai/test_client.py::test_langchain_client_init_openai
```

### Linting
```bash
# Run pylint on all source files
pylint src/

# Run pylint on a specific domain
pylint src/ai/

# Run flake8 (used in CI)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format with Black
black src/ tests/
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

### Domain-Driven Structure

The codebase uses a **domain-driven architecture** optimized for AI tool context and human comprehension:

```
src/
├── ai/               # AI/LLM provider abstraction
│   ├── client.py         # AIClient abstract class & LangChainClient implementation
│   ├── factory.py        # create_ai_client() factory function
│   └── prompts.py        # LangChain prompt template loading & caching
│
├── analysis/         # Core analysis logic
│   ├── models.py         # Analysis Pydantic model (category, vendor, description, date)
│   ├── analyzer.py       # analyze_file_content(), standardize_analysis()
│   └── filename.py       # generate_filename() from metadata
│
├── files/            # File I/O operations
│   ├── extractors.py     # extract_text_from_pdf(), extract_text_from_txt()
│   ├── operations.py     # is_supported_filetype(), rename_files()
│   └── processor.py      # process_file(), process_directory()
│
├── storage/          # Database & caching
│   ├── cache.py          # initialize_cache(), delete_cache()
│   └── database.py       # connect_to_db(), insert_or_update_file(), get_all_suggested_changes()
│
├── cli/              # User interaction
│   ├── arguments.py      # parse_arguments() - CLI argument parsing
│   ├── display.py        # handle_suggested_changes() - Display & user prompts
│   └── workflow.py       # process_path() - Main orchestration
│
├── config/           # Configuration
│   ├── settings.py       # DB_FILE, SUPPORTED_MIMETYPES constants
│   └── logging.py        # setup_logging()
│
└── recommendations/  # Folder suggestions
    └── recommender.py    # recommend_folder_structure()
```

### Test Structure (Mirrors src/)

Tests are organized in a **domain-driven structure** matching src/:

```
tests/
├── ai/
│   ├── test_client.py       # Tests for ai/client.py & ai/factory.py
│   └── test_prompts.py      # Tests for ai/prompts.py
├── analysis/
│   └── test_analyzer.py     # Tests for analysis/analyzer.py
├── files/
│   ├── test_extractors.py   # Tests for files/extractors.py
│   ├── test_operations.py   # Tests for files/operations.py
│   └── test_processor.py    # Tests for files/processor.py
├── storage/
│   ├── test_cache.py        # Tests for storage/cache.py
│   ├── test_database.py     # Tests for storage/database.py
│   └── test_inventory.py    # Integration tests
└── cli/
    └── test_arguments.py    # Tests for cli/arguments.py
```

### Core Components

**AI Client Abstraction** (`src/ai/`)
- `client.py`: Abstract base class `AIClient` + `LangChainClient` implementation
  - Supports OpenAI, Ollama (for local models like DeepSeek), extensible to other providers
  - Uses LangChain's `with_structured_output()` for structured extraction
  - Provider selected via `AI_PROVIDER` environment variable
- `factory.py`: `create_ai_client()` factory function
- `prompts.py`: LangChain ChatPromptTemplate loading with singleton pattern
- Returns structured `Analysis` Pydantic objects

**Analysis Pipeline** (`src/analysis/`)
1. `models.py`: `Analysis` Pydantic model (category, vendor, description, date)
2. `analyzer.py`: Coordinates analysis workflow
   - `analyze_file_content()`: Orchestrates extraction → AI analysis → standardization
   - `standardize_analysis()`: Converts to lowercase, hyphen-separated format
3. `filename.py`: `generate_filename()` creates format: `{vendor}-{category}-{description}-{date}`

**File Operations** (`src/files/`)
1. `extractors.py`: Text extraction from .txt and .pdf files
2. `operations.py`: File validation (`is_supported_filetype()`) and bulk renaming
3. `processor.py`: File processing orchestration (`process_file()`, `process_directory()`)

**Storage** (`src/storage/`)
- `cache.py`: SQLite cache initialization and cleanup
- `database.py`: All SQL operations (connect, insert/update, query)
- Schema: id, file_path, category, description, vendor, date, suggested_name
- Cache is ephemeral (deleted on exit)

**CLI** (`src/cli/`)
- `arguments.py`: CLI argument parsing
- `display.py`: User prompts and suggested changes display
- `workflow.py`: Main application orchestration

### Application Flow

```
main.py
  ↓
cli/arguments.py: parse_arguments() → parse CLI args (path, --dry-run, --auto-rename)
  ↓
storage/cache.py: initialize_cache() → create SQLite DB
  ↓
ai/factory.py: create_ai_client() → initialize LLM client based on AI_PROVIDER
  ↓
cli/workflow.py: process_path() → determine if file or directory
  ↓
files/processor.py: process_file() → for each supported file:
  ├─ files/extractors.py: extract_text_from_{pdf|txt}()
  ├─ ai/prompts.py: get_file_analysis_prompt() → LangChain ChatPromptTemplate
  ├─ ai/client.py: AIClient.analyze_content() → LangChain structured output
  ├─ analysis/analyzer.py: standardize_analysis() → lowercase, hyphenate
  ├─ analysis/filename.py: generate_filename()
  └─ storage/database.py: insert_or_update_file()
  ↓
cli/display.py: handle_suggested_changes() → display suggestions, get user approval
  ↓
files/operations.py: rename_files() → apply approved changes
  ↓
storage/cache.py: delete_cache() → cleanup
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

Prompts are loaded via `src/ai/prompts.py` which uses LangChain's ChatPromptTemplate:
- Proper message role handling (SystemMessage, HumanMessage)
- Template variable validation
- Singleton pattern for performance

## Working with the Codebase

### AI-Optimized Context Loading

The domain-driven structure allows focused AI context:

- **Working on AI providers?** → `@src/ai/` loads only AI-related code
- **Working on file operations?** → `@src/files/` loads only file I/O code
- **Working on database?** → `@src/storage/` loads only storage code
- **Working on tests?** → `@tests/ai/` loads only AI tests

This reduces context noise by 70-80% compared to flat structure!

### Module Dependencies

Clean, acyclic dependency graph:

```
cli/           → depends on: analysis/, files/, storage/
analysis/      → depends on: ai/, files/
ai/            → depends on: analysis/models.py only
files/         → isolated (no internal dependencies)
storage/       → isolated (no internal dependencies)
config/        → isolated (leaf node)
```

### Adding New Features

**Adding a new file type (e.g., DOCX):**
1. Update `config/settings.py`: Add MIME type to `SUPPORTED_MIMETYPES`
2. Add `extract_text_from_docx()` to `files/extractors.py`
3. Update `analysis/analyzer.py`: Add file type dispatch logic
4. Add tests to `tests/files/test_extractors.py`

**Adding a new LLM provider (e.g., Anthropic):**
1. Update `ai/client.py`: Add provider case in `_initialize_llm()`
2. Update `ai/factory.py`: Document new provider in docstring
3. Add tests to `tests/ai/test_client.py`

**Adding a new CLI flag:**
1. Update `cli/arguments.py`: Add argument to parser
2. Update `cli/workflow.py` or `cli/display.py`: Handle new flag
3. Add tests to `tests/cli/test_arguments.py`

## CI/CD

GitHub Actions workflows:
- **python-app.yml** - Runs on push/PR to main:
  - Python 3.10
  - Installs dependencies
  - Runs flake8 linting
  - Runs pytest (46 tests)
- **pylint.yml** - Separate pylint workflow

## Important Notes

- Only `.txt` and `.pdf` files are supported (checked via `is_supported_filetype()`)
- The cache is ephemeral - deleted on exit, not persisted between runs
- File renaming preserves file extension
- Standardization converts category/vendor to lowercase with hyphens (e.g., "Credit Card" → "credit-card")
- **LangChain Integration**: The application uses LangChain for multi-provider LLM support
  - Use `create_ai_client()` factory (in `src/ai/factory.py`) to initialize the AI client
  - Supports both cloud (OpenAI) and local (Ollama) model providers
  - Local models like DeepSeek can run via Ollama for zero API costs
  - All providers use LangChain's structured output API for reliable metadata extraction
- **Code Style**: All code formatted with Black (88-character line limit)
- **Test Coverage**: 46 tests, 100% pass rate

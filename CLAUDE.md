# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered file classifier that analyzes text and PDF files to suggest intelligent file names and categories. Uses OpenAI APIs (with structured outputs via function calling) to extract metadata (category, vendor, description, date) and generate standardized filenames based on content analysis.

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
- `OpenAIClient` implements OpenAI integration using function calling (not structured outputs API)
- Uses deprecated function calling approach: `functions` parameter + `function_call` response parsing
- Returns structured `Analysis` objects parsed from function call arguments

**Analysis Pipeline**
1. **Text Extraction** (`text_extractor.py`) - Extracts content from .txt and .pdf files
2. **Prompt Loading** (`prompt_loader.py`) - Loads and formats prompts from `prompts/` directory
3. **AI Analysis** (`file_analyzer.py`) - Coordinates analysis workflow:
   - Loads system/user prompts
   - Calls AI client to analyze content
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
process_path() → determine if file or directory
  ↓
process_file() → for each supported file:
  ├─ extract_text_from_{pdf|txt}()
  ├─ load_and_format_prompt()
  ├─ AIClient.analyze_content() → OpenAI function calling
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
- `OPENAI_API_KEY` - OpenAI API key (required)
- `AI_MODEL` - Model to use (default: "gpt-4o-mini")
- `DEBUG_MODE` - Enable debug logging (default: "false")
- `OPENAI_MAX_TOKENS` - Max response tokens (default: 50)

### Prompts

Prompts are stored in `prompts/` directory:
- `file-analysis-system-prompt.txt` - System instructions for AI
- `file-analysis-user-prompt.txt` - User prompt template with placeholders for {filename} and {content}

Prompts are loaded via `prompt_loader.py` which supports variable substitution.

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
- The application uses OpenAI's older function calling approach, not the newer structured outputs API

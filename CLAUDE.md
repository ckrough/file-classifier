# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered file classifier that analyzes text and PDF files using a **multi-agent document processing pipeline**. Uses **LangChain** to support multiple LLM providers (OpenAI, local models via Ollama) with structured output extraction across 4 specialized agents:

1. **Classification Agent** - Semantic analysis and metadata extraction
2. **Standards Enforcement Agent** - Naming convention normalization
3. **Path Construction Agent** - Directory structure and filename assembly
4. **Conflict Resolution Agent** - Edge case handling and ambiguity resolution

Generates intelligent directory paths and filenames based on deep content analysis.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (includes both runtime and dev dependencies)
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage (terminal + HTML report)
pytest --cov=src --cov-report=term-missing --cov-report=html

# Run domain-specific tests
pytest tests/ai/           # AI client & prompts
pytest tests/analysis/     # Analysis logic
pytest tests/files/        # File operations
pytest tests/cli/          # CLI arguments

# Run tests by marker (configured in pyproject.toml)
pytest -m "unit"                              # Unit tests only
pytest -m "not slow and not benchmark"        # Fast tests (matches CI)
pytest -m "functional"                        # Integration tests

# Run a specific test
pytest tests/ai/test_client.py::test_langchain_client_init_openai

# Run with verbose output
pytest -v --tb=long
```

### Benchmark Testing
```bash
# Run all benchmark tests
pytest -m benchmark

# Run benchmarks for specific domain
pytest tests/benchmarks/ai/           # AI component benchmarks
pytest tests/benchmarks/files/        # File operation benchmarks

# Run specific benchmark test
pytest tests/benchmarks/ai/test_bench_prompts.py

# Generate performance baseline (save current performance as reference)
./scripts/generate_baseline.sh

# Run performance gate (compare against baseline)
./scripts/run_performance_gate.sh

# Update baseline after approved performance changes
./scripts/update_baseline.sh

# Detect which benchmarks to run based on git changes
python scripts/detect_benchmark_targets.py
```

### Code Quality

#### Pre-Commit Checklist
Run these commands before git staging file changes (recommended order):

```bash
# 1. Format code (auto-fixes issues)
black src/ tests/

# 2. Lint - Flake8 (two-pass approach, matches CI)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics  # Critical errors
flake8 . --count --exit-zero --max-complexity=10 --statistics        # All warnings

# 3. Lint - Pylint (requires PYTHONPATH)
PYTHONPATH=/Users/crow/Documents/code/file-classifier pylint src/

# 4. Security scan
bandit -r src/ -c pyproject.toml

# 5. Run tests with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html
```

#### Configuration Files
- **Black**: Configured in `pyproject.toml` (line-length=88)
- **Flake8**: Auto-reads `.flake8` config (extends Black compatibility)
- **Pylint**: Configured in `pyproject.toml` (max-line-length=88)
- **Bandit**: Configured in `pyproject.toml` (excludes tests, allows assertions)
- **Pytest**: Configured in `pyproject.toml` (markers: unit, functional, slow, benchmark, integration)

#### Individual Tool Commands
```bash
# Black - Code formatting
black src/ tests/
black --check src/ tests/  # Check without modifying

# Flake8 - Linting (auto-reads .flake8)
flake8 .                   # Use .flake8 config
flake8 src/                # Check only src/

# Pylint - Deep analysis
PYTHONPATH=$(pwd) pylint src/

# Bandit - Security scanning
bandit -r src/ -c pyproject.toml
bandit -r src/ -ll         # Low severity only

# Pytest - Testing
pytest                                           # All tests
pytest --cov=src --cov-report=term-missing      # With coverage
pytest -m "not slow and not benchmark"          # Exclude slow tests (matches CI)
```

### Running the Application
```bash
# Classify a single file (JSON output to stdout)
python main.py path/to/file.pdf

# Process multiple files via find + batch mode
find . -name "*.pdf" | python main.py --batch
find . -type f \( -name "*.pdf" -o -name "*.txt" \) | python main.py --batch

# Output in CSV/TSV format
python main.py file.pdf --format=csv
find . -type f | python main.py --batch --format=csv
find . -type f | python main.py --batch --format=tsv

# Verbosity control
python main.py file.pdf --quiet      # Only errors
python main.py file.pdf --verbose    # Detailed progress
python main.py file.pdf --debug      # Full technical logging

# Performance tuning: Use full content extraction (slower, higher accuracy)
python main.py file.pdf --full-extraction

# Performance tuning: Use specific extraction strategy
python main.py file.pdf --extraction-strategy=adaptive
python main.py file.pdf --extraction-strategy=first_n_pages
python main.py file.pdf --extraction-strategy=char_limit
python main.py file.pdf --extraction-strategy=full

# Unix-style composability examples
# Extract field with jq
python main.py file.pdf | jq -r '.suggested_name'

# Filter by domain
find . -type f | python main.py --batch | jq 'select(.metadata.domain == "financial")'

# Generate move script
find . -name "*.pdf" | python main.py --batch | \
  jq -r '"mv \"\\(.original)\" \"\\(.full_path)\""' > moves.sh

# Count classifications by category
find . -type f | python main.py --batch | jq -r '.metadata.category' | sort | uniq -c
```

**Performance Optimization CLI Flags:**
- `--full-extraction` - Extract full document content (overrides CLASSIFICATION_STRATEGY env var to "full")
- `--extraction-strategy=STRATEGY` - Override extraction strategy for this run
  - Choices: `full`, `first_n_pages`, `char_limit`, `adaptive`
  - Overrides CLASSIFICATION_STRATEGY environment variable

The adaptive strategy (default) provides intelligent extraction based on document characteristics:
- Small documents (<3 pages or <1MB): Full extraction
- Standard documents (3-50 pages): First 2-3 pages + last page
- Large compilations (>50 pages or >10MB): Sparse sampling (first 3, middle, last)

Expected performance gains with adaptive strategy:
- **API Cost Reduction**: 60-80% for large multi-page documents
- **Response Latency**: 30-50% faster processing
- **Accuracy**: Minimal impact (<5% degradation estimated)

## Architecture

### Domain-Driven Structure

The codebase uses a **domain-driven architecture** optimized for AI tool context and human comprehension:

```
src/
├── agents/           # Multi-agent document processing pipeline
│   ├── pipeline.py           # process_document_multi_agent() - Orchestrates 4-agent flow
│   ├── classification.py     # classify_document() - Semantic analysis
│   ├── standards.py          # standardize_metadata() - Naming conventions
│   ├── path_construction.py  # construct_path() - Directory & filename assembly
│   └── conflict_resolution.py # resolve_conflicts() - Edge case handling
│
├── ai/               # AI/LLM provider abstraction
│   ├── client.py         # AIClient abstract class & LangChainClient implementation
│   ├── factory.py        # create_ai_client() factory function
│   └── prompts.py        # LangChain prompt template loading & caching
│
├── analysis/         # Data models and compatibility layer
│   ├── models.py         # Multi-agent Pydantic models (RawMetadata, NormalizedMetadata, etc.)
│   └── analyzer.py       # analyze_file_content() - Entry point to multi-agent pipeline
│
├── files/            # File I/O operations
│   ├── extractors.py     # extract_text_from_pdf(), extract_text_from_txt()
│   ├── operations.py     # is_supported_filetype() - File type validation
│   └── processor.py      # process_file(), process_directory() - Returns ClassificationResult
│
├── cli/              # Command-line interface
│   ├── arguments.py      # parse_arguments() - CLI argument parsing
│   └── workflow.py       # process_path(), process_stdin_batch() - Main orchestration
│
├── output/           # Structured output formatting
│   ├── models.py         # ClassificationResult, ClassificationMetadata Pydantic models
│   ├── formatter.py      # OutputFormatter - JSON/CSV/TSV formatting
│   └── __init__.py       # Module exports
│
├── config/           # Configuration
│   ├── settings.py       # SUPPORTED_MIMETYPES constants
│   └── logging.py        # setup_logging()
│
└── recommendations/  # Folder suggestions
    └── recommender.py    # recommend_folder_structure() - Accepts change list
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
├── cli/
│   └── test_arguments.py    # Tests for cli/arguments.py
├── output/
│   ├── test_models.py       # Tests for output/models.py
│   └── test_formatter.py    # Tests for output/formatter.py
└── benchmarks/          # Performance benchmark tests
    ├── ai/
    │   └── test_bench_prompts.py          # Prompt template caching benchmarks
    ├── files/
    │   └── test_bench_mime_detection.py   # MIME detection singleton benchmarks
    ├── analysis/        # (empty - placeholder)
    ├── cli/             # (empty - placeholder)
    └── conftest.py      # Shared benchmark fixtures (sample data, content)
```

### Core Components

**Multi-Agent Pipeline** (`src/agents/`)
A 4-stage pipeline for intelligent document processing:

1. **Classification Agent** (`classification.py`)
   - Function: `classify_document(content, filename, ai_client)`
   - Returns: `RawMetadata` (domain, category, doctype, vendor_raw, dates_raw, subject_raw)
   - Performs semantic analysis of document content
   - Identifies document type, vendor, dates, and subject matter

2. **Standards Enforcement Agent** (`standards.py`)
   - Function: `standardize_metadata(raw, ai_client)`
   - Returns: `NormalizedMetadata` (standardized vendor_name, date YYYYMMDD, subject)
   - Applies naming conventions (lowercase, underscores)
   - Selects primary date from multiple options
   - Normalizes vendor names to standard format

3. **Path Construction Agent** (`path_construction.py`)
   - Function: `construct_path(normalized, ai_client, file_extension)`
   - Returns: `PathMetadata` (directory_path, filename, full_path)
   - Builds directory taxonomy: Domain/Category/Vendor/
   - Assembles filename: doctype-vendor-subject-YYYYMMDD.ext
   - Handles special cases (Tax/Federal/YYYY/, etc.)

4. **Conflict Resolution Agent** (`conflict_resolution.py`)
   - Function: `resolve_conflicts(path, raw, ai_client, conflict_flags)`
   - Returns: `ResolvedMetadata` (final_path, alternative_paths, resolution_notes)
   - Handles edge cases and ambiguities
   - Provides alternative paths for multi-purpose documents
   - Makes final placement decisions

**Pipeline Orchestrator** (`pipeline.py`)
- Function: `process_document_multi_agent(content, filename, ai_client)`
- Coordinates the 4-agent flow
- Detects conflicts between agent outputs
- Returns final `ResolvedMetadata` with path and alternatives

**AI Client Abstraction** (`src/ai/`)
- `client.py`: Abstract base class `AIClient` + `LangChainClient` implementation
  - Supports OpenAI, Ollama (for local models like DeepSeek), extensible to other providers
  - Uses LangChain's `with_structured_output()` for structured extraction
  - Provider selected via `AI_PROVIDER` environment variable
- `factory.py`: `create_ai_client()` factory function
- `prompts.py`: LangChain ChatPromptTemplate loading with singleton pattern

**Data Models** (`src/analysis/models.py`)
- `RawMetadata`: Classification Agent output
- `NormalizedMetadata`: Standards Enforcement Agent output
- `PathMetadata`: Path Construction Agent output
- `ResolvedMetadata`: Conflict Resolution Agent output (final)
- `Analysis`: DEPRECATED - Legacy model for backward compatibility

**File Operations** (`src/files/`)
1. `extractors.py`: Text extraction from .txt and .pdf files
2. `operations.py`: File type validation only
   - `is_supported_filetype()`: Validates file type support using MIME detection
3. `processor.py`: File processing orchestration
   - `process_file()`: Returns `Optional[ClassificationResult]` with classification data

**Output Formatting** (`src/output/`)
- `models.py`: Pydantic models for structured output
  - `ClassificationResult`: Complete classification result with metadata
  - `ClassificationMetadata`: Extracted metadata (domain, category, vendor, date, doctype, subject)
- `formatter.py`: OutputFormatter class
  - Supports JSON (newline-delimited), CSV, and TSV formats
  - Methods: `format_single()`, `format_batch()`, `write_result()`, `write_batch()`

**CLI** (`src/cli/`)
- `arguments.py`: CLI argument parsing (--batch, --format, --quiet, --verbose, --debug, extraction options)
- `workflow.py`: Main application orchestration
  - `process_path()`: Process single file
  - `process_stdin_batch()`: Process file paths from stdin (batch mode)

### Application Flow

```
main.py
  ↓
cli/arguments.py: parse_arguments()
  → CLI args (path, --batch, --format, --quiet, --verbose, --debug, extraction options)
  ↓
ai/factory.py: create_ai_client()
  → Initialize LLM client (OpenAI/Ollama) based on AI_PROVIDER
  ↓
output/formatter.py: OutputFormatter(format_type)
  → Initialize formatter (JSON/CSV/TSV)
  ↓
cli/workflow.py: process_path() OR process_stdin_batch()
  → Process single file or read file paths from stdin
  ↓
files/processor.py: process_file() → for each file:
  ├─ files/extractors.py: extract_text_from_{pdf|txt}()
  │   → Extract document content
  │
  ├─ analysis/analyzer.py: analyze_file_content()
  │   ↓
  │   agents/pipeline.py: process_document_multi_agent()
  │     │
  │     ├─ agents/classification.py: classify_document()
  │     │   ├─ ai/prompts.py: get_prompt_template('classification-agent')
  │     │   ├─ ai/client.py: analyze_content(schema=RawMetadata)
  │     │   └─ Returns: RawMetadata (domain, category, doctype, vendor, dates, subject)
  │     │
  │     ├─ agents/standards.py: standardize_metadata()
  │     │   ├─ ai/prompts.py: get_prompt_template('standards-enforcement-agent')
  │     │   ├─ ai/client.py: analyze_content(schema=NormalizedMetadata)
  │     │   └─ Returns: NormalizedMetadata (normalized vendor, date YYYYMMDD, subject)
  │     │
  │     ├─ agents/path_construction.py: construct_path()
  │     │   ├─ ai/prompts.py: get_prompt_template('path-construction-agent')
  │     │   ├─ ai/client.py: analyze_content(schema=PathMetadata)
  │     │   └─ Returns: PathMetadata (directory_path, filename, full_path)
  │     │
  │     ├─ Conflict Detection
  │     │   → Check for: multiple dates, unknown vendors, multi-purpose docs
  │     │
  │     └─ agents/conflict_resolution.py: resolve_conflicts() (if conflicts detected)
  │         ├─ ai/prompts.py: get_prompt_template('conflict-resolution-agent')
  │         ├─ ai/client.py: analyze_content(schema=ResolvedMetadata)
  │         └─ Returns: ResolvedMetadata (final_path, alternatives, notes)
  │
  └─ Returns ClassificationResult (original, suggested_path, suggested_name, full_path, metadata)
  ↓
cli/workflow.py: Collect results into list[ClassificationResult]
  → Return to main
  ↓
main.py: formatter.write_batch(results, file=sys.stdout)
  → Output structured JSON/CSV/TSV to stdout (logs to stderr)
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

**Performance Tuning** (Content Extraction Optimization):
- `CLASSIFICATION_STRATEGY` - Extraction strategy: "full", "first_n_pages", "char_limit", or "adaptive" (default: "adaptive")
  - `full`: Extract all content (highest accuracy, slowest, most expensive)
  - `first_n_pages`: Extract first N pages only
  - `char_limit`: Extract until character limit reached
  - `adaptive`: Smart strategy based on document size (recommended)
- `CLASSIFICATION_MAX_PAGES` - Maximum pages to extract for page-based strategies (default: 3)
- `CLASSIFICATION_MAX_CHARS` - Maximum characters to extract (safety net, default: 10000)
- `CLASSIFICATION_INCLUDE_LAST_PAGE` - Include last page in extraction (default: "true")

These settings control how much document content is extracted and sent to the AI for classification. The adaptive strategy can reduce API costs by 60-80% and improve response times by 30-50% for large documents while maintaining high classification accuracy.

**Examples:**

Using OpenAI (cloud):
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
# Optional performance tuning (defaults shown)
CLASSIFICATION_STRATEGY=adaptive
CLASSIFICATION_MAX_PAGES=3
CLASSIFICATION_MAX_CHARS=10000
CLASSIFICATION_INCLUDE_LAST_PAGE=true
```

Using local Ollama with DeepSeek:
```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:latest
# Optional performance tuning
CLASSIFICATION_STRATEGY=adaptive
```

### Prompts

Prompts are stored in `prompts/` directory for each agent:

**Classification Agent:**
- `classification-agent-system.txt` - Semantic analysis instructions
- `classification-agent-user.txt` - User prompt with {filename} and {content}

**Standards Enforcement Agent:**
- `standards-enforcement-agent-system.txt` - Naming convention rules
- `standards-enforcement-agent-user.txt` - User prompt with raw metadata

**Path Construction Agent:**
- `path-construction-agent-system.txt` - Directory taxonomy rules
- `path-construction-agent-user.txt` - User prompt with normalized metadata

**Conflict Resolution Agent:**
- `conflict-resolution-agent-system.txt` - Edge case handling logic
- `conflict-resolution-agent-user.txt` - User prompt with conflicts

Prompts are loaded via `src/ai/prompts.py` using LangChain's ChatPromptTemplate:
- Proper message role handling (SystemMessage, HumanMessage)
- Template variable validation
- Singleton pattern with LRU cache for performance

## Working with the Codebase

### AI-Optimized Context Loading

The domain-driven structure allows focused AI context:

- **Working on multi-agent pipeline?** → `@src/agents/` loads only agent-related code
- **Working on AI providers?** → `@src/ai/` loads only AI client and prompt code
- **Working on file operations?** → `@src/files/` loads only file I/O code
- **Working on CLI/workflow?** → `@src/cli/` loads only CLI code
- **Working on data models?** → `@src/analysis/models.py` loads only Pydantic schemas
- **Working on tests?** → `@tests/ai/` or `@tests/agents/` loads only relevant tests

This reduces context noise by 70-80% compared to flat structure!

### Module Dependencies

Clean, acyclic dependency graph:

```
cli/           → depends on: analysis/, files/, output/
output/        → isolated (Pydantic models only)
analysis/      → depends on: agents/, files/
agents/        → depends on: ai/, analysis/models.py
ai/            → depends on: analysis/models.py only
files/         → isolated (no internal dependencies)
config/        → isolated (leaf node)
```

### Adding New Features

**Adding a new file type (e.g., DOCX):**
1. Update `config/settings.py`: Add MIME type to `SUPPORTED_MIMETYPES`
2. Add `extract_text_from_docx()` to `files/extractors.py`
3. Update `analysis/analyzer.py`: Add file type extraction logic
4. Add tests to `tests/files/test_extractors.py`

**Adding a new agent or modifying the pipeline:**
1. Update `agents/pipeline.py`: Add new agent call or modify flow
2. Create agent module in `agents/` (e.g., `agents/new_agent.py`)
3. Add corresponding Pydantic model to `analysis/models.py`
4. Create prompts in `prompts/` directory (`new-agent-system.txt`, `new-agent-user.txt`)
5. Add tests for the new agent

**Adding a new LLM provider (e.g., Anthropic):**
1. Update `ai/client.py`: Add provider case in `_initialize_llm()`
2. Update `ai/factory.py`: Document new provider in docstring
3. Add tests to `tests/ai/test_client.py`

**Adding a new CLI flag:**
1. Update `cli/arguments.py`: Add argument to parser
2. Update `cli/workflow.py` or `main.py`: Handle new flag
3. Add tests to `tests/cli/test_arguments.py`

**Adding a new output format:**
1. Update `output/formatter.py`: Add new format type and formatting method
2. Update `cli/arguments.py`: Add new format choice to --format argument
3. Add tests to `tests/output/test_formatter.py`

## CI/CD

GitHub Actions workflows:
- **python-app.yml** - Runs on push/PR to main:
  - Python 3.11 (minimum version, as specified in pyproject.toml)
  - Installs dependencies via `pip install -e ".[dev]"`
  - Runs flake8 linting (two-pass: critical errors + all warnings)
  - Runs pytest (excludes `slow`, `functional`, `benchmark`, and `integration` tests)
- **pylint.yml** - Separate pylint workflow:
  - Python 3.11
  - Sets PYTHONPATH for import resolution
  - Runs `pylint src/` with pyproject.toml configuration

**Performance Testing Infrastructure:**
- Benchmark tests available via `pytest -m benchmark` (not run in CI)
- Performance baseline generation: `./scripts/generate_baseline.sh`
- Performance gate validation: `./scripts/run_performance_gate.sh`
- Automatic benchmark target detection: `python scripts/detect_benchmark_targets.py`

## Important Notes

- Only `.txt` and `.pdf` files are supported (checked via `is_supported_filetype()`)
- **Unix-Style Output**: Tool outputs structured data to stdout, logs to stderr
  - JSON (newline-delimited), CSV, or TSV formats
  - Composable with standard Unix tools (jq, xargs, etc.)
  - Does not perform file operations - metadata only
- **Verbosity Levels**: Four levels available (all logs go to stderr):
  - `--quiet` - Suppress all logs except errors
  - Normal (default) - Standard progress logging
  - `--verbose` - Detailed progress and timing information
  - `--debug` - Full technical logging for troubleshooting
- **Batch Mode**: Supports stdin input for pipeline processing
  - `--batch` flag reads file paths from stdin (one per line)
  - Ideal for use with `find`, `xargs`, and other Unix tools
- **Unix Philosophy**: Single-file processing, composable with standard tools
  - Processes individual files only (no built-in directory walking)
  - Directory processing via `find`: `find . -type f | python main.py --batch`
  - Delegates directory traversal to Unix tools for maximum flexibility
- **Multi-Agent Pipeline**: Document processing uses a 4-stage agent pipeline
  - Each agent has specialized expertise and structured output schema
  - Conflict detection identifies edge cases requiring resolution
  - Alternative paths provided for multi-purpose documents
- **Directory Structure**: Suggests hierarchical taxonomy
  - Format: `Domain/Category/Vendor/doctype-vendor-subject-YYYYMMDD.ext`
  - Examples: `Financial/Banking/chase/statement-chase-checking-20240115.pdf`
  - Special cases: `Tax/Federal/2024/1040-irs-tax-return-20240415.pdf`
- **Naming Conventions**: Standards Enforcement Agent applies consistent rules
  - Lowercase with underscores for multi-word values
  - Vendor names standardized (e.g., "bank_of_america", "smith_john_md")
  - Dates in YYYYMMDD format
  - Subjects concise (1-3 words)
- **Output Models**: Classification results are Pydantic models
  - `ClassificationResult`: Complete result with metadata
  - `ClassificationMetadata`: Domain, category, vendor, date, doctype, subject
  - Returned as `list[ClassificationResult]` from processing functions
- **Performance Benchmarks**: Benchmark infrastructure for performance testing
  - Tests marked with `@pytest.mark.benchmark` measure locally-developed code only
  - Baseline generation and performance gates available via `scripts/` directory
  - Not run in CI by default (excluded with other slow tests)
- **LangChain Integration**: The application uses LangChain for multi-provider LLM support
  - Use `create_ai_client()` factory (in `src/ai/factory.py`) to initialize the AI client
  - Supports both cloud (OpenAI) and local (Ollama) model providers
  - Local models like DeepSeek can run via Ollama for zero API costs
  - All agents use LangChain's `with_structured_output()` for schema validation
- **Extraction Optimization**: Configurable content extraction for performance tuning
  - Adaptive strategy (default) reduces API costs by 60-80% for large documents
  - Intelligently samples document pages based on size and type
  - Configurable via environment variables or CLI flags (`--full-extraction`, `--extraction-strategy`)
  - Minimal accuracy impact (<5% degradation) with significant speed/cost benefits
  - See "Performance Tuning" section in Environment Variables for details
- **Code Style**: All code formatted with Black (88-character line limit)
- **Test Coverage**: Comprehensive test suite with pytest

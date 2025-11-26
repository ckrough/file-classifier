# AGENTS.md

AI-powered document classifier using a multi-agent LLM pipeline.
Analyzes text and PDF files, outputs JSON metadata with suggested file paths.

## Setup

```zsh
setup_venv() {
  setopt localoptions errexit nounset pipefail

  # Create venv if needed
  if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
  fi

  # Activate venv
  source .venv/bin/activate

  # Upgrade pip and install dev deps
  python -m pip install --upgrade pip
  python -m pip install -e ".[dev]"
}

setup_venv
```

## Commands

```zsh
# Run classifier
python main.py document.pdf
python main.py document.pdf --quiet
python main.py document.pdf --verbose
find ~/Documents -type f \( -name "*.pdf" -o -name "*.txt" \) | python main.py --quiet --batch

# Override defaults
python main.py document.pdf --taxonomy household --naming-style descriptive_nara
python main.py document.pdf --ai-provider ollama --ai-model llama3.1:latest

# Test
pytest
pytest -m "not slow and not benchmark"
pytest tests/ai/test_client.py::test_name
pytest --cov=src --cov-report=term-missing

# Lint (run in order before every commit)
black src/ tests/
flake8 . --max-complexity=10 --max-line-length=88
PYTHONPATH=$(pwd) pylint src/ --output-format=json --score=n --reports=n
bandit -r src/ -f json --severity-level medium --confidence-level medium --quiet -c pyproject.toml
```

## Architecture

### Pipeline

1. **Classification Agent** (`src/agents/classification.py`): Extracts semantic metadata from content. Output: `RawMetadata` (domain, category, doctype, vendor_raw, date_raw, subject_raw)
2. **Standards Agent** (`src/agents/standards.py`): Normalizes naming, validates vendor. Output: `NormalizedMetadata` (canonical slugs, formatted date, vendor_name)
3. **Path Builder** (`src/path/builder.py`): Deterministic assembly of filesystem path. Output: `PathMetadata` (directory_path, filename, full_path)

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/ai/client.py` | LangChain client (OpenAI, Ollama). Structured output via `with_structured_output`. |
| `src/analysis/models.py` | Pydantic schemas for AI output validation |
| `src/files/extractors.py` | Text extraction with strategy-aware sampling |
| `src/taxonomy/` | Domain/category/doctype vocabulary, alias resolution |
| `src/naming/` | Pluggable naming styles (descriptive_nara, compact_gpo) |
| `src/config/settings.py` | Global constraints (path length, hierarchy depth, supported mimetypes) |

### Taxonomy Behavior

- **Domain**: strict, must exist in `taxonomies/*.yaml`
- **Category/doctype**: flexible, canonicalizes when possible, creates new slug otherwise
- Prompts inject taxonomy via `{taxonomy_xml}` partial variable

### Data Models

- Pydantic models (`src/analysis/models.py`): AI-facing schemas requiring validation
- Dataclasses (`src/path/builder.py:PathMetadata`): Internal structs for deterministic operations

## Code Style

- Black formatter, 88-char line limit
- Identifiers: `lowercase_with_underscores`
- Dates in filenames: `YYYYMMDD`
- Require `PYTHONPATH=$(pwd)` for pylint

## Extension Points

### New file type

1. Add MIME type to `src/config/settings.py:SUPPORTED_MIMETYPES`
2. Implement extractor in `src/files/extractors.py`
3. Route extension in `src/analysis/analyzer.py`
4. Add tests in `tests/files/`

### New agent

1. Create module in `src/agents/`
2. Add Pydantic models in `src/analysis/models.py`
3. Create prompts in `prompts/` (XML format)
4. Wire into `src/agents/pipeline.py:process_document_multi_agent()`
5. Add tests in `tests/agents/`

### New LLM provider

1. Add case in `src/ai/client.py:_initialize_llm()`
2. Update `src/ai/factory.py`, document env vars
3. Add tests in `tests/ai/test_client.py`

### New CLI flag

1. Add argument in `src/cli/arguments.py`
2. Handle in `main.py` or `src/cli/workflow.py`
3. Add tests in `tests/cli/test_arguments.py`

## Tests

Test layout mirrors `src/`. Markers: `unit`, `integration`, `functional`, `slow`, `benchmark`. Benchmarks not run in CI.
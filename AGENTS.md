# AGENTS.md

Concise guidance for AI coding agents on project standards, styles, and workflows.

For architecture details and a full command reference, see `WARP.md`.

## Dev environment tips

- Use `PYTHONPATH=$(pwd)` when running Pylint so imports resolve correctly.
- This is a Python project; do not change the Python version or tooling without being asked.
- Taxonomy configuration is externalized under `taxonomies/*.yaml` (e.g., `taxonomies/household.yaml`).
  - The active taxonomy is selected via:
    - CLI flag: `--taxonomy <name>`
    - or env var: `TAXONOMY_NAME=<name>`
- Prompts inject taxonomy via the `{taxonomy_xml}` partial variable; **no manual prompt cache clearing** is needed after `set_taxonomy()`.

## Testing instructions

- CI workflows live in `.github/workflows/python-app.yml` and `.github/workflows/pylint.yml`.
- Fast tests (matches CI focus):
  - `pytest -m "not slow and not benchmark"`
- Single test while iterating:
  - `pytest tests/ai/test_client.py::test_langchain_client_init_openai`
- Coverage (recommended before merging):
  - `pytest --cov=src --cov-report=term-missing`
- Benchmarks (optional; not run in CI):
  - `pytest -m benchmark`
- Always add or update tests for the behavior you change, and ensure **all relevant tests pass** before you consider a change complete.

## Code quality & security

Run these in order before committing or opening a PR:

```bash
black src/ tests/
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --statistics
PYTHONPATH=$(pwd) pylint src/
bandit -r src/ -c pyproject.toml
pytest --cov=src --cov-report=term-missing
```

Tool configuration lives in `pyproject.toml` (Black, Pylint, Bandit, Pytest) and `.flake8`.

## Code style

- **Formatter**: Black, 88-char line limit.
- **Naming**: `lowercase_with_underscores` for agent-produced identifiers; path-builder utilities convert to `Title_Case` as needed.
- **Dates**: Always `YYYYMMDD` in filenames and paths.
- **Pydantic models**: Use for AI-facing schemas (`RawMetadata`, `NormalizedMetadata`).
- **Dataclasses**: Use for internal structs (`PathMetadata`, `PathResult`).
- **Docstrings**: Required on all public functions, classes, and modules.
- Keep functions focused and reasonably small (aim for <50 lines); extract reusable logic instead of duplicating it.
- Use f-strings for formatting, comprehensions for simple transformations, and context managers (`with`) for resources.

## Taxonomy & prompts

- Canonical domains, categories, doctypes, and aliases are defined in `taxonomies/*.yaml`.
- Active taxonomy selection:
  - CLI: `--taxonomy <name>`
  - Env: `TAXONOMY_NAME=<name>`
- Strictness and validation:
  - `TAXONOMY_STRICT_MODE` (env or `--strict-taxonomy`):
    - **True** → raise on unknown values.
    - **False** → allow unknown values but log warnings.
  - `--validate-taxonomy` flag: validates the active taxonomy, prints a schema report, and exits with non-zero status on failure.
- Prompts use `{taxonomy_xml}` injected via LangChain `partial_variables`:
  - Do **not** reintroduce manual placeholder replacement or ad-hoc prompt caches.
  - When adding new taxonomy-aware prompts, include a `{taxonomy_xml}` placeholder in the system prompt and use the existing prompt loader utilities.

## Adding features

**New file type (e.g., DOCX):**
1. Add the MIME type to `config/settings.py:SUPPORTED_MIMETYPES`.
2. Implement an extractor in `files/extractors.py` (e.g., `extract_text_from_docx()`).
3. Update `analysis/analyzer.py` to call the new extractor.
4. Add tests in `tests/files/test_extractors.py`.

**New agent:**
1. Create a module in `agents/` (e.g., `agents/my_agent.py`).
2. Add or update Pydantic models in `analysis/models.py`.
3. Create prompts in `prompts/` (`my-agent-system.xml`, `my-agent-user.xml`).
4. Wire the agent into `agents/pipeline.py`.
5. Add tests for both agent logic and pipeline integration.

**New LLM provider:**
1. Add a case in `ai/client.py:_initialize_llm()`.
2. Document it in the `ai/factory.py` docstring.
3. Add tests in `tests/ai/test_client.py`.

**New CLI flag:**
1. Add the argument in `cli/arguments.py`.
2. Handle it in `cli/workflow.py` or `main.py`.
3. Add tests in `tests/cli/test_arguments.py` (and integration tests if needed).

## PR instructions

- Title format: `[component] Short description` (e.g., `[taxonomy] Add strict mode`).
- Before requesting review:
  - Run `black`, `flake8`, `pylint`, `bandit`, and the relevant `pytest` commands above.
  - Ensure linters and tests are green.
- Do **not** commit or merge without running the full checklist above, unless explicitly instructed otherwise for a throwaway or spike branch.

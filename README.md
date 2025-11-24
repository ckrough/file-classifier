# File Classifier

## Overview

A command-line tool that analyzes text documents and outputs JSON metadata with suggested file paths based on document content and context. Designed for composability with `jq` and other JSON-aware tools.

**What it does:**
- Reads and understands document content using AI
- Identifies document metadata; type, purpose, vendor, dates, and subject matter
- Outputs JSON metadata to stdout for piping
- Generates organized paths with configurable naming styles (folders and filenames)

**Supported file types:** `.txt` and `.pdf`

**AI provider options:** OpenAI (cloud) or Ollama (local models)

## Quick Start

### Installation

```sh
# Clone and navigate to repository
git clone <repository_url>
cd file-classifier

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file with your AI provider settings:

**Using OpenAI:**
```env
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=<your_api_key>
```

**Using Ollama (local):**
```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:latest
```

For Ollama, install and pull the model first:
```sh
ollama pull deepseek-r1:latest
```

### Basic Usage

**Requires jq:** `brew install jq` (macOS) or `apt install jq` (Linux)

```sh
# Classify a single file (outputs JSON with metadata)
python main.py document.pdf
# Output: {"original": "document.pdf", "suggested_path": "financial/invoices/statement/statement-acme-services-20240115.pdf", "domain": "financial", "category": "invoices", "doctype": "statement", "vendor": "acme", "date": "20240115", "subject": "services"}

# Extract just the suggested path
python main.py document.pdf | jq -r .suggested_path
# Output: financial/invoices/statement/statement-acme-services-20240115.pdf

# Move file to suggested path
mv document.pdf "$(python main.py document.pdf | jq -r .suggested_path)"

# Process multiple files via find + batch mode (JSON Lines output)
find ~/Documents -type f \( -name "*.pdf" -o -name "*.txt" \) | python main.py --batch
# Output: One JSON object per line (newline-delimited JSON)

# Quiet mode (errors only to stderr)
python main.py document.pdf --quiet
```

## More Examples

The tool outputs JSON to stdout and logs to stderr, making it composable with `jq` and other JSON tools:

### Move Files to Suggested Paths

```sh
# Single file - get suggested path and move
new_path="$(python main.py invoice.pdf | jq -r .suggested_path)"
mkdir -p "$(dirname "$new_path")"
mv invoice.pdf "$new_path"

# Or in one command
mv invoice.pdf "$(python main.py invoice.pdf | jq -r .suggested_path)"
```

### Batch Processing with Move Script

```sh
# Generate and execute move commands from batch mode
find . -name "*.pdf" | python main.py --batch | \
  jq -r '"echo \"Moving: " + .original + " → " + .suggested_path + "\" && mkdir -p \"" + (.suggested_path | dirname) + "\" && mv \"" + .original + "\" \"" + .suggested_path + "\""' | \
  bash
```

### Filter by Domain or Category

```sh
# Find all financial documents
find . -type f | python main.py --batch | jq 'select(.domain == "financial")'

# Find tax documents (tax is a category under financial domain)
find . -type f | python main.py --batch | jq 'select(.domain == "financial" and .category == "tax")'

# Get unique domains
find . -type f | python main.py --batch | jq -r .domain | sort -u

# Get unique vendors
find . -name "*.pdf" | python main.py --batch | jq -r .vendor | sort -u

# Filter by date range (e.g., 2024)
find . -type f | python main.py --batch | jq 'select(.date | startswith("2024"))'
```

### Parallel Processing

```sh
# Process files in parallel using xargs
find . -name "*.pdf" | xargs -P 4 -I {} python main.py {}

# GNU parallel for better load balancing
find . -name "*.pdf" | parallel -j 4 python main.py {}

# Parallel with batch mode and filtering
find . -name "*.pdf" | parallel -j 4 python main.py {} | jq 'select(.domain == "financial")'
```

### Build Custom Workflows

```sh
# Create directory structure before moving
find ~/Downloads -type f | python main.py --batch | \
  jq -r .suggested_path | xargs -I {} dirname {} | sort -u | \
  xargs -I {} mkdir -p ~/Organized/{}

# Then move files
find ~/Downloads -type f | python main.py --batch | \
  jq -r '"mkdir -p \"~/Organized/" + (.suggested_path | dirname) + "\" && mv \"" + .original + "\" \"~/Organized/" + .suggested_path + "\""' | \
  bash
```

## Naming Styles

Two styles are available (select via env var `NAMING_STYLE` or CLI `--naming-style`):

- descriptive_nara (default)
  - Folder path: `Domain/Category/Doctypes/` (Title Case; doctype pluralized)
  - Filename: `doctype_vendor[_subject][_YYYY|YYYYMM|YYYYMMDD][_vNN|_final|_draft].ext` (lowercase_with_underscores)
  - Example: `Financial/Banking/Statements/statement_chase_checking_20250131.pdf`

- compact_gpo
  - Folder path: `Domain/Category/Doctypes/` (Title Case; doctype pluralized)
  - Filename: `vendor[_YYYY|YYYYMM|YYYYMMDD].ext` (lowercase_with_underscores)
  - Example: `Financial/Banking/Statements/chase_20250131.pdf`

Configure:
- Env var: `NAMING_STYLE=descriptive_nara` (default) or `NAMING_STYLE=compact_gpo`
- CLI override: `--naming-style descriptive_nara` or `--naming-style compact_gpo`

## Output Format

The tool outputs JSON metadata (JSON Lines format for batch):

**JSON Fields:**
```json
{
  "original": "document.pdf",
  "suggested_path": "financial/banking/statement/statement-chase-checking-20240115.pdf",
  "domain": "financial",
  "category": "banking",
  "doctype": "statement",
  "vendor": "chase",
  "date": "20240115",
  "subject": "checking"
}
```

**Single File Mode:**
Outputs one JSON object:
```json
{"original": "doc.pdf", "suggested_path": "financial/banking/statement/statement-chase-checking-20240115.pdf", "domain": "financial", "category": "banking", "doctype": "statement", "vendor": "chase", "date": "20240115", "subject": "checking"}
```

**Batch Mode:**
Outputs JSON Lines (one JSON object per line):
```json
{"original": "doc1.pdf", "suggested_path": "financial/banking/statement/statement-chase-checking-20240115.pdf", "domain": "financial", "category": "banking", "doctype": "statement", "vendor": "chase", "date": "20240115", "subject": "checking"}
{"original": "doc2.pdf", "suggested_path": "financial/tax/1040/1040-irs-return-20240415.pdf", "domain": "financial", "category": "tax", "doctype": "1040", "vendor": "irs", "date": "20240415", "subject": "return"}
```

Metadata is provided both as structured JSON fields and encoded in the path:
- **Domain**: JSON field + first path component (`financial/`)
- **Category**: JSON field + second path component (`banking/`)
- **Doctype**: JSON field + third path component (`statement/`)
- **Vendor, Subject, Date**: Encoded in filename (`statement-chase-checking-20240115.pdf`)

## Organization Structure

The tool suggests a hierarchical structure based on document content:

```
Domain/Category/Doctype/doctype-vendor-subject-YYYYMMDD.ext
```

### Example Output Structure

```
financial/banking/statement/
├── statement-chase-checking-20250131.pdf
├── statement-chase-savings-20250131.pdf
├── statement-bofa-checking-20250131.pdf

financial/credit_cards/statement/
├── statement-amex-platinum-20250115.pdf
├── statement-visa-rewards-20250115.pdf

financial/tax/1040/
├── 1040-irs-tax_return-20240415.pdf

financial/tax/w2/
├── w2-acme_corp-wages-20250131.pdf

medical/records/receipt/
├── receipt-city_hospital-surgery-20250110.pdf
├── receipt-county_clinic-checkup-20250215.pdf

medical/records/bill/
├── bill-city_hospital-emergency-20250320.pdf

insurance/auto/policy/
├── policy-state_farm-auto_insurance-20250101.pdf
```

### Supported Domains

- **Financial**: Banking, Credit Cards, Loans, Investments, Tax (Federal, State, Property)
- **Medical**: Records, Bills, Insurance
- **Property**: Real Estate, Rental, Ownership
- **Legal**: Contracts, Court Documents, Estate Planning
- **Insurance**: Auto, Home, Life, Health

## How It Works

1. **Extract Text**: Reads content from `.txt` and `.pdf` files
2. **Analyze Content**: AI examines the document using a 2-agent pipeline
3. **Generate Structure**: Creates directory path and filename based on content
4. **Output Metadata**: Prints structured JSON to stdout

The tool performs semantic analysis to understand document meaning, not just keyword matching. It normalizes vendor names, formats dates consistently (YYYYMMDD), and determines specific vendors from document content.

**2-Agent Pipeline:**
- **Classification Agent**: Semantic analysis and metadata extraction
- **Standards Enforcement Agent**: Naming convention normalization and vendor determination
- **Deterministic Path Builder**: Directory structure and filename assembly (no AI)

## Command-Line Options

```
python main.py [PATH] [OPTIONS]

Positional Arguments:
  PATH                  File to analyze (required unless --batch)

Input/Output:
  --batch               Read file paths from stdin (one per line)

Performance Tuning:
  --full-extraction     Extract full document content (highest accuracy, slower)
  --extraction-strategy {full,first_n_pages,char_limit,adaptive}
                        Override extraction strategy (default: adaptive)

Verbosity (logs to stderr):
  --quiet, -q           Only show errors
  --verbose, -v         Show detailed progress and timing
  --debug               Show full technical logging

Naming:
  --naming-style {compact_gpo,descriptive_nara}
                        Override naming style for this run (default: compact_gpo)
```

## Performance Optimization

The tool supports adaptive content extraction to reduce API costs and improve speed:

```sh
# Use adaptive strategy (default) - smart sampling based on document size
python main.py document.pdf

# Force full content extraction for maximum accuracy
python main.py document.pdf --full-extraction

# Use specific strategy for batch processing
find ~/Documents -type f | python main.py --batch --extraction-strategy=first_n_pages
```

**Adaptive strategy benefits:**
- **60-80% API cost reduction** for large documents
- **30-50% faster processing**
- **<5% accuracy impact** in most cases

Configure via environment variables in `.env`:
```env
CLASSIFICATION_STRATEGY=adaptive
CLASSIFICATION_MAX_PAGES=3
CLASSIFICATION_MAX_CHARS=10000
CLASSIFICATION_INCLUDE_LAST_PAGE=true
```

## Development

### Running Tests

```sh
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suites
pytest tests/ai/           # AI client & prompts
pytest tests/files/        # File operations
pytest tests/cli/          # CLI functionality
pytest tests/analysis/     # Analysis logic
pytest tests/output/       # Output formatting

# Run benchmark tests
pytest -m benchmark
```

### Code Quality

Run before committing (in order):

```sh
# 1. Format code
black src/ tests/

# 2. Lint - Flake8 (two-pass)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics  # Critical
flake8 . --count --exit-zero --max-complexity=10 --statistics        # Warnings

# 3. Lint - Pylint
PYTHONPATH=$(pwd) pylint src/

# 4. Security scan
bandit -r src/ -c pyproject.toml

# 5. Tests with coverage
pytest --cov=src --cov-report=term-missing
```

### Project Structure

```
src/
├── agents/           # Multi-agent document processing pipeline
├── ai/               # LLM provider abstraction (OpenAI, Ollama)
├── analysis/         # Data models and analysis logic
├── files/            # File I/O and text extraction
├── cli/              # Command-line interface
├── config/           # Configuration and logging
└── output/           # JSON/CSV/TSV formatters

tests/
├── ai/               # AI client tests
├── agents/           # Pipeline tests
├── files/            # File operation tests
├── analysis/         # Analysis logic tests
├── cli/              # CLI tests
├── output/           # Formatter tests
└── benchmarks/       # Performance tests
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation and development workflows.

## Configuration

### Environment Variables

**General:**
- `DEBUG_MODE` - Enable debug logging (default: false)
- `AI_PROVIDER` - AI provider: "openai" or "ollama" (default: openai)

**OpenAI (when `AI_PROVIDER=openai`):**
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `AI_MODEL` - Model to use (default: gpt-4o-mini)

**Ollama (when `AI_PROVIDER=ollama`):**
- `OLLAMA_BASE_URL` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model name (default: deepseek-r1:latest)

**Performance Tuning:**
- `CLASSIFICATION_STRATEGY` - Extraction strategy: "full", "first_n_pages", "char_limit", or "adaptive" (default: adaptive)
- `CLASSIFICATION_MAX_PAGES` - Maximum pages to extract (default: 3)
- `CLASSIFICATION_MAX_CHARS` - Maximum characters to extract (default: 10000)
- `CLASSIFICATION_INCLUDE_LAST_PAGE` - Include last page in extraction (default: true)

**Naming:**
- `NAMING_STYLE` - Naming style: `compact_gpo` (default) or `descriptive_nara`

## Naming Conventions

The tool applies consistent naming standards:

- **Lowercase with underscores**: Multi-word values use underscores (e.g., `bank_of_america`, `credit_cards`)
- **Date format**: YYYYMMDD for all dates
- **Vendor normalization**: Standardizes vendor names (e.g., "BofA" → `bank_of_america`)
- **Concise subjects**: 1-3 word descriptions (e.g., `annual_physical`, `tax_return`)

## Limitations

- Only supports `.txt` and `.pdf` files
- Requires AI API access (OpenAI) or local model setup (Ollama)
- Quality depends on document content clarity and AI model capabilities
- Processes individual files only - use `find` for directory traversal
- Each file requires AI analysis (may be slow for large batches)
- Does not perform file operations - outputs metadata only (use with `mv`, `cp`, etc.)

## Troubleshooting

**"No API key found"**: Ensure `.env` file exists with `OPENAI_API_KEY` or Ollama configuration

**"Unsupported file type"**: Only `.txt` and `.pdf` files are processed; others are skipped

**"Connection error"**: For Ollama, verify the server is running: `ollama serve`

**Unexpected classifications**: Try with `--debug` flag to see detailed analysis

**Empty output**: Check stderr for errors (add `--debug` for detailed logging)

## License

MIT License - Copyright (c) 2024 Chris Krough

See LICENSE file for full details.

## Contributing

Contributions welcome! Please:
1. Create an issue to discuss major changes
2. Follow the code quality standards (Black, Flake8, Pylint)
3. Add tests for new functionality
4. Ensure all tests pass before submitting PR

## Contact

Questions or issues? Open an issue in the repository's Issues section.

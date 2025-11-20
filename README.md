# File Classifier

## Overview

A Unix-style command-line tool that analyzes documents and outputs structured classification metadata in JSON, CSV, or TSV format. Designed for composability with standard Unix tools like `jq`, `xargs`, and shell scripts.

**What it does:**
- Reads and understands document content using AI
- Identifies document type, vendor, dates, and subject matter
- Outputs structured JSON/CSV/TSV to stdout for piping
- Generates organized paths: `Domain/Category/Vendor/`
- Creates standardized filenames: `doctype-vendor-subject-YYYYMMDD.ext`

**Supported file types:** `.txt` and `.pdf`

**AI provider options:** OpenAI (cloud) or Ollama (local models)

**Unix philosophy:** Do one thing well, output structured data, compose with other tools.

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

```sh
# Classify a single file (JSON output to stdout)
python main.py document.pdf

# Process multiple files via find + batch mode
find ~/Documents -type f \( -name "*.pdf" -o -name "*.txt" \) | python main.py --batch

# Output in CSV format
python main.py document.pdf --format=csv
find . -type f | python main.py --batch --format=csv

# Quiet mode (errors only to stderr)
python main.py document.pdf --quiet
```

## Unix-Style Examples

The tool outputs structured data to stdout and logs to stderr, making it composable with Unix tools:

### Extract Specific Fields with jq

```sh
# Get just the suggested filename
python main.py invoice.pdf | jq -r '.suggested_name'
# Output: invoice-acme-services-20240115.pdf

# Get the full suggested path
python main.py invoice.pdf | jq -r '.full_path'
# Output: business/invoices/acme_corp/invoice-acme-services-20240115.pdf

# Extract all metadata
python main.py document.pdf | jq '.metadata'
```

### Generate Move/Rename Scripts

```sh
# Create a shell script to move files
find . -name "*.pdf" | python main.py --batch | \
  jq -r '"mv \"\\(.original)\" \"\\(.full_path)\""' > moves.sh

# Review the generated script
cat moves.sh

# Execute after review
bash moves.sh
```

### Filter by Domain or Category

```sh
# Find all financial documents
find . -type f | python main.py --batch | \
  jq -r 'select(.metadata.domain == "financial")'

# Find all bank statements
find . -type f | python main.py --batch | \
  jq -r 'select(.metadata.category == "banking" and .metadata.doctype == "statement")'

# Get unique vendors
find . -name "*.pdf" | python main.py --batch | \
  jq -r '.metadata.vendor' | sort -u
```

### CSV/TSV for Spreadsheet Import

```sh
# Generate CSV for import to Excel/Google Sheets
find ~/Documents -type f | python main.py --batch --format=csv > classifications.csv

# TSV format for tab-delimited
find ~/Documents -type f | python main.py --batch --format=tsv > classifications.tsv

# Process large archive in CSV
find /archive -type f | python main.py --batch --format=csv > archive-index.csv
```

### Parallel Processing

```sh
# Process files in parallel using xargs
find . -name "*.pdf" | \
  xargs -P 4 -I {} python main.py {} | \
  jq -s '.'  # Combine into single JSON array

# GNU parallel for better load balancing
find . -name "*.pdf" | \
  parallel -j 4 python main.py {} | \
  jq -s 'map(select(.metadata.domain == "financial"))'
```

### Build Custom Workflows

```sh
# Create directory structure before moving
find ~/Downloads -type f | python main.py --batch | \
  jq -r '.suggested_path' | \
  sort -u | \
  xargs -I {} mkdir -p ~/Organized/{}

# Then move files
find ~/Downloads -type f | python main.py --batch | \
  jq -r '"mv \"\\(.original)\" \"~/Organized/\\(.full_path)\""' | \
  bash
```

## Output Formats

### JSON (default)

Newline-delimited JSON (NDJSON) for streaming:

```json
{"original": "doc.pdf", "suggested_path": "financial/banking/chase", "suggested_name": "statement-chase-checking-20240115.pdf", "full_path": "financial/banking/chase/statement-chase-checking-20240115.pdf", "metadata": {"domain": "financial", "category": "banking", "vendor": "chase", "date": "20240115", "doctype": "statement", "subject": "checking"}}
```

### CSV

Comma-separated with header row:

```csv
original,suggested_path,suggested_name,full_path,domain,category,vendor,date,doctype,subject
doc.pdf,financial/banking/chase,statement-chase-checking-20240115.pdf,financial/banking/chase/statement-chase-checking-20240115.pdf,financial,banking,chase,20240115,statement,checking
```

### TSV

Tab-separated with header row (same fields as CSV).

## Organization Structure

The tool suggests a hierarchical structure based on document content:

```
Domain/Category/Vendor/doctype-vendor-subject-YYYYMMDD.ext
```

### Example Output Structure

```
Financial/Banking/chase/
├── statement-chase-checking-20250131.pdf
├── statement-chase-savings-20250131.pdf

Financial/Credit_Cards/amex/
├── statement-amex-platinum-20250115.pdf

Tax/Federal/2024/
├── 1040-irs-tax-return-20240415.pdf
├── w2-acme_corp-wages-20250131.pdf

Medical/Records/city_hospital/
├── receipt-city_hospital-surgery-20250110.pdf
├── bill-city_hospital-emergency-20250320.pdf

Insurance/Auto/state_farm/
├── policy-state_farm-auto_insurance-20250101.pdf
```

### Supported Domains

- **Financial**: Banking, Credit Cards, Loans, Investments
- **Tax**: Federal, State, Property
- **Medical**: Records, Bills, Insurance
- **Property**: Real Estate, Rental, Ownership
- **Legal**: Contracts, Court Documents, Estate Planning
- **Insurance**: Auto, Home, Life, Health

## How It Works

1. **Extract Text**: Reads content from `.txt` and `.pdf` files
2. **Analyze Content**: AI examines the document using a multi-agent pipeline
3. **Generate Structure**: Creates directory path and filename based on content
4. **Output Metadata**: Prints structured JSON/CSV/TSV to stdout

The tool performs semantic analysis to understand document meaning, not just keyword matching. It normalizes vendor names, formats dates consistently (YYYYMMDD), and handles edge cases like documents with multiple purposes.

**Multi-Agent Pipeline:**
- **Classification Agent**: Semantic analysis and metadata extraction
- **Standards Enforcement Agent**: Naming convention normalization
- **Path Construction Agent**: Directory structure and filename assembly
- **Conflict Resolution Agent**: Edge case handling

## Command-Line Options

```
python main.py [PATH] [OPTIONS]

Positional Arguments:
  PATH                  File to analyze (required unless --batch)

Input/Output:
  --batch               Read file paths from stdin (one per line)
  --format {json,csv,tsv}
                        Output format (default: json)

Performance Tuning:
  --full-extraction     Extract full document content (highest accuracy, slower)
  --extraction-strategy {full,first_n_pages,char_limit,adaptive}
                        Override extraction strategy (default: adaptive)

Verbosity (logs to stderr):
  --quiet, -q           Only show errors
  --verbose, -v         Show detailed progress and timing
  --debug               Show full technical logging
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

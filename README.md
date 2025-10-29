# File Classifier

## Overview

Automatically organize and rename your documents based on their content. This tool analyzes text and PDF files using AI to understand what they are, then generates organized directory structures and standardized filenames.

**What it does:**
- Reads and understands document content
- Identifies document type, vendor, dates, and subject matter
- Generates organized paths: `Domain/Category/Vendor/`
- Creates standardized filenames: `doctype-vendor-subject-YYYYMMDD.ext`
- Lets you review and approve changes before applying them

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

```sh
# Analyze and rename files in current location
python main.py path/to/directory

# Preview changes without applying (recommended first run)
python main.py path/to/directory --dry-run

# Move files to organized archive structure
python main.py path/to/directory --move --destination ~/archive
```

## Usage Examples

### Rename Mode (Default)

Renames files in their current location:

```sh
# Basic usage
python main.py ~/Downloads

# Preview first
python main.py ~/Downloads --dry-run

# With verbose output
python main.py ~/Downloads --verbose
```

### Move Mode

Organizes files into archive directory structure:

```sh
# Move to archive
python main.py ~/Downloads --move --destination ~/Documents/archive

# Preview the move
python main.py ~/Downloads --move --destination ~/Documents/archive --dry-run

# Quiet mode (only show errors)
python main.py ~/Downloads --move --destination ~/Documents/archive --quiet
```

### Output Control

Control the amount of output:

```sh
--quiet    # Only show errors
           # (default: normal output)
--verbose  # Show detailed progress and timing
--debug    # Show full technical logging
```

## Organization Structure

The tool creates a hierarchical structure based on document content:

```
Domain/Category/Vendor/doctype-vendor-subject-YYYYMMDD.ext
```

### Example Output

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
2. **Analyze Content**: AI examines the document to understand what it is
3. **Generate Structure**: Creates directory path and filename based on content
4. **Review Changes**: Shows you all proposed changes
5. **Apply Changes**: Renames or moves files after your approval

The tool performs semantic analysis to understand document meaning, not just keyword matching. It normalizes vendor names, formats dates consistently (YYYYMMDD), and handles edge cases like documents with multiple purposes.

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
├── agents/           # Document processing pipeline
├── ai/               # LLM provider abstraction
├── analysis/         # Data models and analysis logic
├── files/            # File I/O operations
├── cli/              # User interface and workflow
├── config/           # Configuration
└── recommendations/  # Folder suggestions

tests/
├── ai/               # AI client tests
├── agents/           # Pipeline tests
├── files/            # File operation tests
├── analysis/         # Analysis logic tests
├── cli/              # CLI tests
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
- Large directories may take time to process (each file requires AI analysis)

## Troubleshooting

**"No API key found"**: Ensure `.env` file exists with `OPENAI_API_KEY` or Ollama configuration

**"Unsupported file type"**: Only `.txt` and `.pdf` files are processed; others are skipped

**"Connection error"**: For Ollama, verify the server is running: `ollama serve`

**Unexpected classifications**: Try with `--debug` flag to see detailed analysis

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

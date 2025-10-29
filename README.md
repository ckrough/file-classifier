# File Classifier Application

## Overview

AI-powered file classifier that analyzes text and PDF files using a **multi-agent document processing pipeline**. The application uses specialized AI agents to perform deep content analysis and generate intelligent directory structures and filenames based on semantic understanding of documents.

**Key Capabilities:**
- Semantic document classification (Financial, Medical, Tax, Property, Legal, Insurance domains)
- Intelligent vendor identification and normalization
- Automatic directory taxonomy generation (`Domain/Category/Vendor/`)
- Standardized filename generation (`doctype-vendor-subject-YYYYMMDD.ext`)
- Support for both cloud (OpenAI) and local (Ollama) LLM providers

## Features

- **Multi-Agent Processing**: 4-stage AI pipeline for intelligent document analysis
  - **Classification Agent**: Semantic analysis and metadata extraction
  - **Standards Enforcement Agent**: Naming convention normalization
  - **Path Construction Agent**: Directory structure and filename assembly
  - **Conflict Resolution Agent**: Edge case handling and ambiguity resolution

- **Flexible AI Providers**: Choose between OpenAI (cloud) or Ollama (local models like DeepSeek)

- **Smart Organization**: Generates hierarchical directory structures based on document content
  - Financial documents: `Financial/Banking/chase/statement-chase-checking-20250131.pdf`
  - Tax documents: `Tax/Federal/2024/1040-irs-tax-return-20240415.pdf`
  - Medical records: `Medical/Records/smith_john_md/report-smith_john_md-annual_physical-20250201.pdf`

- **Flexible File Operations**: Two operation modes
  - **Rename mode** (default): Rename files in their current location
  - **Move mode** (`--move --destination`): Move files to organized archive directory structure

- **User Control**: Review all suggested changes before applying
  - Interactive approval workflow
  - Dry-run mode for testing
  - Verbosity control (quiet, normal, verbose, debug)

- **Supported Formats**: `.txt` and `.pdf` files

## Setup Instructions

### 1. Clone the Repository
```sh
git clone <repository_url>
cd file-classifier
```

### 2. Create a Virtual Environment
```sh
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```sh
# Install runtime and development dependencies
pip install -e ".[dev]"

# Or install only runtime dependencies
pip install -e .
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory with one of the following configurations:

#### Option A: Using OpenAI (Cloud)
```env
# AI Provider Configuration
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=<your_openai_api_key>

# Optional
DEBUG_MODE=false
```

#### Option B: Using Ollama (Local)
```env
# AI Provider Configuration
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:latest

# Optional
DEBUG_MODE=false
```

**Note**: For Ollama, ensure you have Ollama installed and running locally. Install models with:
```sh
ollama pull deepseek-r1:latest
```

## Usage

### Command Line Interface

#### Analyze a Single File
```sh
python main.py path/to/file.pdf
```

#### Analyze an Entire Directory
```sh
python main.py path/to/directory
```

#### Dry-Run Mode (Preview Changes)
Preview suggested changes without actually applying them:
```sh
python main.py path/to/directory --dry-run
```

#### Move Files to Archive Structure
Move files to an organized archive directory instead of renaming in-place:
```sh
python main.py path/to/directory --move --destination ~/archive
```

#### Verbosity Control
Control output detail level:
```sh
# Quiet mode (only errors)
python main.py path/to/directory --quiet

# Verbose mode (detailed progress)
python main.py path/to/directory --verbose

# Debug mode (full technical logging)
python main.py path/to/directory --debug
```

#### Combined Flags
```sh
# Preview move operation with verbose output
python main.py path/to/directory --move --destination ~/archive --dry-run --verbose
```

### Example Output

```
Financial/Banking/chase/
├── statement-chase-checking-20250131.pdf
├── statement-chase-savings-20250131.pdf

Tax/Federal/2024/
├── 1040-irs-tax-return-20240415.pdf
├── w2-acme_corp-wages-20250131.pdf

Medical/Records/city_hospital/
├── receipt-city_hospital-surgery-20250110.pdf
├── eob-bcbs-hospital_visit-20250320.pdf
```

## How It Works

The application uses a sophisticated **4-agent pipeline** for intelligent document processing:

### 1. Classification Agent
- Performs semantic analysis of document content
- Identifies document domain (Financial, Medical, Tax, etc.)
- Determines category (Banking, Real_Estate, Health, etc.)
- Extracts document type (statement, receipt, invoice, policy)
- Identifies vendor and subject matter
- Selects most relevant date (invoice date > transaction date)

### 2. Standards Enforcement Agent
- Applies naming conventions (lowercase, underscores)
- Standardizes vendor names (`Bank of America` → `bank_of_america`)
- Formats dates to YYYYMMDD
- Normalizes subjects to 1-3 concise words
- Ensures consistent document type vocabulary

### 3. Path Construction Agent
- Builds directory taxonomy: `Domain/Category/Vendor/`
- Assembles filename: `doctype-vendor-subject-YYYYMMDD.ext`
- Handles special cases (Tax/Federal/YYYY/, property addresses, etc.)
- Applies archival system rules

### 4. Conflict Resolution Agent
- Handles edge cases and ambiguities
- Resolves unknown vendors
- Provides alternative paths for multi-purpose documents
- Makes final placement decisions with explanatory notes

### Workflow
1. **File Discovery**: Scans directory for `.txt` and `.pdf` files
2. **Text Extraction**: Extracts content from documents
3. **Multi-Agent Analysis**: Processes each document through 4-agent pipeline
4. **User Review**: Displays suggested changes for approval
5. **Batch Renaming**: Applies approved changes to files

## Architecture

The codebase uses a **domain-driven architecture** with clear separation of concerns:

```
src/
├── agents/          # Multi-agent processing pipeline
├── ai/              # AI/LLM provider abstraction (OpenAI, Ollama)
├── analysis/        # Data models and compatibility layer
├── files/           # File I/O operations (extraction, renaming, moving)
├── cli/             # User interaction and workflow orchestration
├── config/          # Configuration and settings
└── recommendations/ # Folder structure suggestions
```

For detailed architecture documentation, see [CLAUDE.md](CLAUDE.md).

## Testing

```sh
# Run all tests (excludes slow, benchmark, functional, integration tests)
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test domains
pytest tests/ai/           # AI client & prompts
pytest tests/agents/       # Multi-agent pipeline
pytest tests/files/        # File operations
pytest tests/cli/          # CLI arguments

# Run benchmark tests (performance testing)
pytest -m benchmark
pytest tests/benchmarks/   # All benchmarks
```

## Development

```sh
# Install development dependencies
pip install -e ".[dev]"

# Format code (always run first)
black src/ tests/

# Run linting (two-pass approach)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics  # Critical errors
flake8 . --count --exit-zero --max-complexity=10 --statistics        # All warnings
PYTHONPATH=$(pwd) pylint src/

# Security scanning
bandit -r src/ -c pyproject.toml

# Run tests with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html
```

For complete development workflows and configuration details, see [CLAUDE.md](CLAUDE.md).

## License

MIT License

Copyright (c) [2024] [Chris Krough]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact

For questions or issues, please reach out via the repository's Issues section.

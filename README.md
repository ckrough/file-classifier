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

# Move files to organized output directory structure
python main.py path/to/directory --move --destination ~/output
```

## Docker Usage (Recommended)

Docker provides a consistent environment without requiring Python installation on your system.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

### Quick Start with Docker

1. **Clone the repository:**
   ```sh
   git clone <repository_url>
   cd file-classifier
   ```

2. **Configure environment:**
   ```sh
   # Copy the example configuration
   cp .env.example .env

   # Edit .env with your preferred AI provider settings
   # For OpenAI: Set OPENAI_API_KEY
   # For Ollama: Configure OLLAMA_BASE_URL and OLLAMA_MODEL
   ```

3. **Build the Docker image:**
   ```sh
   docker-compose build
   ```

4. **Run the application:**
   ```sh
   # Analyze files in the ./files directory (default)
   docker-compose run --rm file-classifier /app/input

   # Preview changes first (recommended)
   docker-compose run --rm file-classifier /app/input --dry-run
   ```

### Easy Mode: Using the Wrapper Script

The simplest way to use Docker is with the included `classify.sh` wrapper script. It's designed for processing **single files** in automated scripts:

```sh
# Process a single file
./classify.sh ./invoice.pdf

# Preview changes without applying
./classify.sh ./invoice.pdf --dry-run

# Use in iteration scripts
for file in /ingest/dir/*.pdf; do
    ./classify.sh "$file" --dry-run
done

# The script automatically:
#   - Converts relative paths to absolute paths
#   - Mounts the parent directory as a Docker volume
#   - Renames files in-place (no --move support)
#   - Handles file permissions correctly
#   - Builds the Docker image if needed
```

**Note:** The wrapper script is intentionally minimal and only supports:
- Single file processing (not directories)
- Dry-run mode
- Rename in-place (no --move/--destination)

For directory processing or move operations, use `docker-compose` directly (see below).

### Docker Usage Patterns

#### Method 1: Wrapper Script (For Single Files)

**Process individual files:**
```sh
# Basic usage
./classify.sh ./invoice.pdf

# Preview changes first
./classify.sh ./invoice.pdf --dry-run

# Works with absolute and relative paths
./classify.sh /Users/username/Documents/tax-form.pdf --dry-run

# Perfect for automation scripts
for file in ~/ingest/*.pdf; do
    ./classify.sh "$file" --dry-run
done
```

**Limitations:** The wrapper script only supports single files with rename-in-place. For directories or move operations, use Method 2 below.

#### Method 2: Docker Compose (For Directories and Move Operations)

**Process entire directories using environment variables:**
```sh
# Set INPUT_DIR to process any directory
INPUT_DIR=./sample-documents docker-compose run --rm file-classifier /app/input --dry-run
INPUT_DIR=/Users/username/Downloads docker-compose run --rm file-classifier /app/input

# Use both INPUT_DIR and OUTPUT_DIR
INPUT_DIR=./documents OUTPUT_DIR=./my-output \
  docker-compose run --rm file-classifier /app/input --move --destination /app/output
```

**Use the default ./files directory:**
```sh
# Copy files to the default location
mkdir -p ./files
cp /path/to/your/documents/* ./files/

# Run analysis
docker-compose run --rm file-classifier /app/input --dry-run
docker-compose run --rm file-classifier /app/input
```

**Different output verbosity levels:**
```sh
# Using docker-compose for verbosity control
INPUT_DIR=./documents docker-compose run --rm file-classifier /app/input --quiet
INPUT_DIR=./documents docker-compose run --rm file-classifier /app/input --verbose
INPUT_DIR=./documents docker-compose run --rm file-classifier /app/input --debug
```

### Volume Mounting

The docker-compose.yml configuration supports flexible directory mounting:

**Default mounts** (when using `docker-compose` without environment variables):
- **`./files`** → `/app/input` - Place documents to classify here
- **`./output`** → `/app/output` - Destination for `--move` operations
- **`./.env`** → `/app/.env` - Configuration file (read-only)

**Custom mounts** using environment variables:
```sh
# Override input directory
INPUT_DIR=./sample-documents docker-compose run --rm file-classifier /app/input

# Override both input and output directories
INPUT_DIR=/Users/username/Documents OUTPUT_DIR=/Users/username/Output \
  docker-compose run --rm file-classifier /app/input --move --destination /app/output
```

**Using standalone Docker** (without docker-compose):
```sh
# Directly mount any directory
docker run --rm \
  -v /path/to/my/docs:/app/input:rw \
  -v /path/to/output:/app/output:rw \
  -v $(pwd)/.env:/app/.env:ro \
  file-classifier:latest /app/input

# Or use the wrapper script for single files (easiest)
./classify.sh /path/to/my/docs/invoice.pdf
```

### Using Docker with Ollama

To use local models via Ollama in Docker:

1. **Uncomment the Ollama service** in `docker-compose.yml`

2. **Update your `.env`:**
   ```env
   AI_PROVIDER=ollama
   OLLAMA_BASE_URL=http://ollama:11434
   OLLAMA_MODEL=deepseek-r1:latest
   ```

3. **Start Ollama and pull the model:**
   ```sh
   docker-compose up -d ollama
   docker-compose exec ollama ollama pull deepseek-r1:latest
   ```

4. **Run the classifier:**
   ```sh
   docker-compose run --rm file-classifier /app/files
   ```

### Standalone Docker (without docker-compose)

If you prefer using Docker directly:

```sh
# Build the image
docker build -t file-classifier:latest .

# Run with volume mounts
docker run --rm \
  -v $(pwd)/files:/app/input:rw \
  -v $(pwd)/output:/app/output:rw \
  -v $(pwd)/.env:/app/.env:ro \
  file-classifier:latest /app/input --dry-run
```

### Docker Troubleshooting and Notes

#### File Permission Issues

The docker-compose.yml configuration runs the container as your current user (UID:GID) to ensure files are owned by you. By default, it uses `1000:1000`. If you encounter permission issues:

**Check your UID/GID:**
```sh
id -u  # Shows your user ID
id -g  # Shows your group ID
```

**If your UID/GID is not 1000, export them before running docker-compose:**
```sh
export UID=$(id -u)
export GID=$(id -g)
docker-compose run --rm file-classifier /app/input --dry-run
```

**Or set them inline:**
```sh
UID=$(id -u) GID=$(id -g) docker-compose run --rm file-classifier /app/input
```

#### Log Persistence

By default, application logs are written to `/tmp/app.log` inside the container, which means they are **ephemeral** and disappear when the container stops.

**To preserve logs across container runs**, uncomment the log volume mount in `docker-compose.yml`:
```yaml
volumes:
  # Uncomment this line:
  - ${LOG_DIR:-./logs}:/tmp:rw
```

Then create the logs directory and run:
```sh
mkdir -p ./logs
docker-compose run --rm file-classifier /app/input
# Logs will be saved to ./logs/app.log on your host machine
```

#### Resource Limits

The docker-compose.yml configuration includes resource limits to prevent unbounded memory/CPU usage during AI processing:
- **Memory limit**: 2GB maximum
- **CPU limit**: 2.0 cores
- **Memory reservation**: 512MB minimum

If you need to adjust these limits for your hardware, edit the `deploy.resources` section in `docker-compose.yml`.

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

Organizes files into output directory structure:

```sh
# Move to output directory
python main.py ~/Downloads --move --destination ~/Documents/output

# Preview the move
python main.py ~/Downloads --move --destination ~/Documents/output --dry-run

# Quiet mode (only show errors)
python main.py ~/Downloads --move --destination ~/Documents/output --quiet
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

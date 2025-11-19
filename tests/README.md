# File Classifier Application

## Overview
AI-powered file classifier that analyzes text and PDF files using a **multi-agent document processing pipeline**. Uses **LangChain** to support multiple LLM providers (OpenAI, local models via Ollama) with structured output extraction across 4 specialized agents for intelligent file organization.

## Features
- **Multi-Agent AI Pipeline**: 4-stage document processing (Classification → Standards → Path Construction → Conflict Resolution)
- **Multiple LLM Providers**: Support for OpenAI (cloud) and Ollama (local models like DeepSeek)
- **Intelligent File Renaming**: Renames files in their current location based on AI analysis
- **Intelligent Path Construction**: Generates hierarchical directory structures and filenames based on document analysis
  - Example: `Financial/Banking/chase/statement-chase-checking-20250131.pdf`
- **User Control**: Interactive approval workflow with dry-run mode and verbosity control
- **In-Memory Processing**: No database required - all processing happens in memory for simplicity

## Setup Instructions

1. **Clone the Repository**:
   ```sh
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a Virtual Environment**:
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```sh
   # Install runtime and development dependencies
   pip install -e ".[dev]"
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the root directory with one of the following configurations:

   **Using OpenAI (cloud):**
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=<your_openai_api_key>
   AI_MODEL=gpt-4o-mini
   DEBUG_MODE=false
   ```

   **Using Ollama (local models):**
   ```env
   AI_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=deepseek-r1:latest
   DEBUG_MODE=false
   ```

## Usage

### Basic Commands

- **Analyze a Single File**:
  ```sh
  python main.py path/to/file.pdf
  ```

- **Analyze a Directory**:
  ```sh
  python main.py path/to/directory
  ```

### Advanced Options

- **Dry-Run Mode** (preview changes without applying):
  ```sh
  python main.py path/to/directory --dry-run
  ```

- **Verbosity Control**:
  ```sh
  python main.py path/to/directory --quiet    # Only errors
  python main.py path/to/directory --verbose  # Detailed progress
  python main.py path/to/directory --debug    # Full logging
  ```

- **Combined Flags**:
  ```sh
  python main.py path/to/directory --dry-run --verbose
  ```

## How It Works

### Multi-Agent Processing Pipeline
1. **File Discovery**: Inventories all `.txt` and `.pdf` files in the specified path
2. **Content Extraction**: Extracts text from documents (supports PDF and plain text)
3. **Multi-Agent Analysis**: Processes each document through 4 specialized AI agents:
   - **Classification Agent**: Identifies document type, vendor, dates, and subject
   - **Standards Enforcement Agent**: Normalizes naming conventions and formats
   - **Path Construction Agent**: Builds directory structure and filename
   - **Conflict Resolution Agent**: Handles edge cases and ambiguities
4. **User Review**: Presents suggested changes with clear before/after comparison
5. **File Operations**: Applies approved changes (renames files in current location)

### Architecture
- **In-Memory Processing**: All changes collected in memory for batch review
- **No Database**: Simplified architecture without persistent storage between runs
- **Domain-Driven Design**: Clean separation of concerns across modules (agents/, ai/, files/, cli/)

For detailed architecture and development documentation, see [../CLAUDE.md](../CLAUDE.md).

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact
For questions or issues, please reach out via the repository's Issues section.


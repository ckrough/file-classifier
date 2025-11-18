#!/bin/bash
set -e

# Simple wrapper for classifying a single file
# Usage: classify.sh <file> [--dry-run]

# Check if file argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file> [--dry-run]" >&2
    echo "Classify and rename a single file using AI analysis." >&2
    exit 1
fi

# Get the input file (first argument)
INPUT_FILE="$1"
shift  # Remove first argument, leaving only options

# Check if file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File does not exist: $INPUT_FILE" >&2
    exit 1
fi

# Convert to absolute path and resolve symbolic links
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"
fi

# Resolve symbolic links to prevent symlink attacks
if command -v readlink &> /dev/null; then
    INPUT_FILE="$(readlink -f "$INPUT_FILE" 2>/dev/null || echo "$INPUT_FILE")"
fi

# Security: Check for path traversal attempts
if [[ "$INPUT_FILE" == *".."* ]]; then
    echo "Error: Path traversal detected in file path" >&2
    exit 1
fi

# Security: Block system directories to prevent exposure of sensitive files
BLOCKED_PATHS=("/etc" "/root" "/sys" "/proc" "/dev" "/boot" "/var/run" "/run")
for blocked in "${BLOCKED_PATHS[@]}"; do
    if [[ "$INPUT_FILE" == "$blocked"* ]]; then
        echo "Error: Cannot process files in system directory: $blocked" >&2
        exit 1
    fi
done

# Mount the parent directory
INPUT_DIR="$(dirname "$INPUT_FILE")"
INPUT_FILENAME="$(basename "$INPUT_FILE")"
CONTAINER_PATH="/app/input/$INPUT_FILENAME"

# Build Docker run command
DOCKER_CMD=(docker run --rm)

# Add user mapping to avoid permission issues
DOCKER_CMD+=(-u "$(id -u):$(id -g)")

# Mount parent directory
DOCKER_CMD+=(-v "$INPUT_DIR:/app/input:rw")

# Mount .env file if it exists
if [ -f "$(pwd)/.env" ]; then
    DOCKER_CMD+=(-v "$(pwd)/.env:/app/.env:ro")
elif [ -f "$(dirname "$0")/.env" ]; then
    DOCKER_CMD+=(-v "$(dirname "$0")/.env:/app/.env:ro")
fi

# Add image name
DOCKER_CMD+=(file-classifier:latest)

# Add container path and forwarded arguments (e.g., --dry-run)
DOCKER_CMD+=("$CONTAINER_PATH" "$@")

# Check if image exists, build if missing
if ! docker image inspect file-classifier:latest &> /dev/null; then
    echo "Building Docker image..." >&2
    docker build -t file-classifier:latest "$(dirname "$0")" >&2
fi

# Run the Docker command
"${DOCKER_CMD[@]}"

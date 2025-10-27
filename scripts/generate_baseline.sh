#!/bin/bash
# Generate initial performance baseline for all benchmark tests
# Run this once to establish baseline, or after major refactoring

set -e

PROJECT_ROOT="/Users/crow/Documents/code/file-classifier"
BENCHMARKS_DIR=".benchmarks"
PYTHONPATH="$PROJECT_ROOT"

echo "[INFO] Generating comprehensive performance baseline..."
echo ""

# Check if baseline already exists
BASELINE_EXISTS=$(find "$BENCHMARKS_DIR" -name "*baseline.json" 2>/dev/null | head -n 1)

if [ -n "$BASELINE_EXISTS" ]; then
    echo "[WARNING] Baseline already exists"
    echo "[WARNING] This will overwrite the existing baseline."
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Cancelled."
        exit 0
    fi
    # Remove all baseline files
    find "$BENCHMARKS_DIR" -name "*baseline.json" -delete 2>/dev/null || true
fi

# Create .benchmarks directory if it doesn't exist
mkdir -p "$BENCHMARKS_DIR"

# Run all benchmark tests and save as baseline
PYTHONPATH="$PYTHONPATH" pytest \
    tests/benchmarks/ \
    -m benchmark \
    --benchmark-only \
    --benchmark-autosave \
    --benchmark-save=baseline \
    --benchmark-min-rounds=5 \
    --benchmark-warmup=on \
    --benchmark-disable-gc \
    --benchmark-columns=min,max,mean,stddev,ops \
    --benchmark-sort=name \
    -v

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Baseline generated successfully"
    echo ""
    NEW_BASELINE=$(find "$BENCHMARKS_DIR" -name "*baseline.json" 2>/dev/null | head -n 1)
    if [ -n "$NEW_BASELINE" ]; then
        echo "Baseline saved to: $NEW_BASELINE"
    fi
    echo ""
    echo "Next steps:"
    echo "  - Make code changes"
    echo "  - Run: ./scripts/run_performance_gate.sh"
    echo "  - Compare performance against this baseline"
    echo ""
else
    echo ""
    echo "[ERROR] Failed to generate baseline"
    exit 1
fi

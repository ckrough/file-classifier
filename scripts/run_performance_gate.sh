#!/bin/bash
# Performance Quality Gate - Automated performance regression detection
# This script is triggered by Claude Code before staging changes

set -e

# Configuration
PROJECT_ROOT="/Users/crow/Documents/code/file-classifier"
BENCHMARKS_DIR=".benchmarks"
PYTHONPATH="$PROJECT_ROOT"
REGRESSION_THRESHOLD="mean:15%"  # Fail if >15% slower

echo "[INFO] Detecting performance-critical changes..."

# Step 1: Detect which benchmarks to run based on staged changes
BENCHMARK_PATTERN=$(python3 "$PROJECT_ROOT/scripts/detect_benchmark_targets.py" 2>&1)

# Check if detection script had errors
if [ $? -ne 0 ]; then
    echo "[WARNING] Error detecting benchmark targets"
    echo "$BENCHMARK_PATTERN"
    exit 0  # Don't block on detection errors
fi

# Check if any benchmarks need to run
if [ -z "$BENCHMARK_PATTERN" ]; then
    echo "[SUCCESS] No performance-critical code changed. Skipping benchmarks."
    exit 0
fi

echo "[INFO] Detected changes - will run benchmarks matching pattern:"
echo "  $BENCHMARK_PATTERN"
echo ""

# Step 2: Check for baseline
# pytest-benchmark stores baselines in platform-specific subdirectories
BASELINE_EXISTS=$(find "$BENCHMARKS_DIR" -name "*baseline.json" 2>/dev/null | head -n 1)

if [ -z "$BASELINE_EXISTS" ]; then
    echo "[WARNING] No baseline found. Generating initial baseline..."
    echo ""

    PYTHONPATH="$PYTHONPATH" pytest \
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
        echo "[SUCCESS] Baseline established"
        echo "[INFO] Run this script again to compare future changes against this baseline."
    else
        echo ""
        echo "[ERROR] Failed to generate baseline"
        exit 1
    fi
    exit 0
fi

# Step 3: Run targeted benchmarks and compare against baseline
echo "[INFO] Running benchmarks for changed code..."
echo ""

# Find the most recent baseline file number
PLATFORM_DIR=$(find "$BENCHMARKS_DIR" -type d -name "*-CPython-*" | head -n 1)
if [ -n "$PLATFORM_DIR" ]; then
    LATEST_BASELINE=$(cd "$PLATFORM_DIR" && ls *_baseline.json 2>/dev/null | tail -1 | sed 's/_baseline.json//')
else
    echo "[ERROR] Could not find platform-specific benchmark directory"
    exit 1
fi

if [ -z "$LATEST_BASELINE" ]; then
    echo "[ERROR] Could not determine baseline reference"
    exit 1
fi

echo "[INFO] Comparing against baseline: $LATEST_BASELINE"
echo ""

# Run pytest with benchmark comparison using -k filter
PYTHONPATH="$PYTHONPATH" pytest \
    tests/benchmarks/ \
    -m benchmark \
    -k "$BENCHMARK_PATTERN" \
    --benchmark-only \
    --benchmark-compare="$LATEST_BASELINE" \
    --benchmark-compare-fail="$REGRESSION_THRESHOLD" \
    --benchmark-min-rounds=5 \
    --benchmark-warmup=on \
    --benchmark-disable-gc \
    --benchmark-columns=min,max,mean,stddev,ops \
    --benchmark-sort=name \
    --benchmark-json="$BENCHMARKS_DIR/latest_result.json" \
    -v

RESULT=$?

echo ""
echo "========================================================================"

if [ $RESULT -eq 0 ]; then
    echo "[SUCCESS] PERFORMANCE CHECK PASSED"
    echo ""
    echo "All benchmarks completed within acceptable performance threshold."
    echo "No regressions detected (threshold: $REGRESSION_THRESHOLD)."
    echo ""
    echo "Ready to stage changes."
    echo "========================================================================"
    exit 0
else
    echo "[WARNING] PERFORMANCE REGRESSION DETECTED"
    echo ""
    echo "One or more functions are significantly slower than baseline."
    echo "Threshold: >$REGRESSION_THRESHOLD"
    echo ""
    echo "Options:"
    echo "  1. Optimize - Review and improve performance of changed code"
    echo "  2. Accept - If regression is acceptable trade-off, update baseline:"
    echo "     ./scripts/update_baseline.sh"
    echo "  3. Investigate - Review benchmark details above for specific slowdowns"
    echo ""
    echo "Tip: Run individual benchmarks for detailed analysis:"
    echo "  PYTHONPATH=$PROJECT_ROOT pytest <benchmark_file> -m benchmark -v"
    echo ""
    echo "========================================================================"
    exit 1  # Soft block: warns but allows override
fi

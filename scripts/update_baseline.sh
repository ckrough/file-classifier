#!/bin/bash
# Update performance baseline after intentional performance changes
# Use this when you've made changes that legitimately affect performance

set -e

PROJECT_ROOT="/Users/crow/Documents/code/file-classifier"
BENCHMARKS_DIR=".benchmarks"
BACKUP_DIR=".benchmarks/backups"
BACKUP_FILE="$BACKUP_DIR/baseline_backup_$(date +%Y%m%d_%H%M%S).json"
PYTHONPATH="$PROJECT_ROOT"

echo "[INFO] Updating performance baseline..."
echo ""

# Check if baseline exists
BASELINE_EXISTS=$(find "$BENCHMARKS_DIR" -name "*baseline.json" 2>/dev/null | head -n 1)

if [ -z "$BASELINE_EXISTS" ]; then
    echo "[ERROR] No existing baseline found"
    echo ""
    echo "Run this first to create initial baseline:"
    echo "  ./scripts/generate_baseline.sh"
    exit 1
fi

# Create backup directory and backup existing baseline
mkdir -p "$BACKUP_DIR"
echo "[INFO] Creating backup of existing baseline..."
cp "$BASELINE_EXISTS" "$BACKUP_FILE"
echo "  - Backup saved to: $BACKUP_FILE"
echo ""

# Confirm update
echo "[WARNING] This will replace the current baseline with new measurements."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "[INFO] Cancelled."
    rm "$BACKUP_FILE"
    exit 0
fi

# Remove old baselines
find "$BENCHMARKS_DIR" -name "*baseline.json" -not -path "*/backups/*" -delete 2>/dev/null || true

# Generate new baseline
echo ""
echo "[INFO] Running all benchmarks to establish new baseline..."
echo ""

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
    echo "[SUCCESS] Baseline updated successfully"
    echo ""
    NEW_BASELINE=$(find "$BENCHMARKS_DIR" -name "*baseline.json" -not -path "*/backups/*" 2>/dev/null | head -n 1)
    if [ -n "$NEW_BASELINE" ]; then
        echo "New baseline saved to: $NEW_BASELINE"
    fi
    echo "Backup available at: $BACKUP_FILE"
    echo ""
else
    echo ""
    echo "[ERROR] Failed to update baseline"
    echo ""
    echo "Restoring previous baseline from backup..."
    # Extract platform-specific directory from backup path
    PLATFORM_DIR=$(dirname "$BASELINE_EXISTS")
    cp "$BACKUP_FILE" "$PLATFORM_DIR/"
    rm "$BACKUP_FILE"
    exit 1
fi

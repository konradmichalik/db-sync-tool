#!/bin/bash
# Interactive CLI output testing with Docker
# Usage: ./test-cli-output.sh [output-mode] [options]
#
# Examples:
#   ./test-cli-output.sh                    # Interactive mode (default)
#   ./test-cli-output.sh interactive -v     # Verbose interactive mode
#   ./test-cli-output.sh ci                 # CI mode with annotations
#   ./test-cli-output.sh json               # JSON output
#   ./test-cli-output.sh quiet              # Quiet mode (errors only)
#
set -e

cd "$(dirname "$0")"
PROJECT_ROOT="$(cd .. && pwd)"

OUTPUT_MODE="${1:-interactive}"
shift 2>/dev/null || true
EXTRA_ARGS="$@"

echo "=== CLI Output Test ==="
echo "Mode: $OUTPUT_MODE"
[ -n "$EXTRA_ARGS" ] && echo "Args: $EXTRA_ARGS"
echo ""

# Setup virtual environment if needed
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate and install dependencies
source "$VENV_DIR/bin/activate"
if ! python3 -c "import yaml, rich" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r "$PROJECT_ROOT/requirements.txt"
fi

# Start containers if needed (--wait handles healthchecks)
if ! docker compose -f integration/docker/docker-compose.yml ps --status running 2>/dev/null | grep -q "www1"; then
    echo "Starting Docker containers..."
    docker compose -f integration/docker/docker-compose.yml up -d --wait
fi

CONFIG="$PROJECT_ROOT/tests/integration/scenario/receiver/typo3/typo3_env.json"
echo "Running: python3 -m db_sync_tool -f $CONFIG --output $OUTPUT_MODE $EXTRA_ARGS"
echo ""

cd "$PROJECT_ROOT"
python3 -m db_sync_tool \
    -f "$CONFIG" \
    --output "$OUTPUT_MODE" \
    $EXTRA_ARGS

echo ""
echo "Done."

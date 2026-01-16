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

OUTPUT_MODE="${1:-interactive}"
shift 2>/dev/null || true
EXTRA_ARGS="$@"

echo "=== CLI Output Test ==="
echo "Mode: $OUTPUT_MODE"
[ -n "$EXTRA_ARGS" ] && echo "Args: $EXTRA_ARGS"
echo ""

# Install dependencies if needed
if ! python3 -c "import yaml, rich" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install --user -q -r ../requirements.txt 2>/dev/null || pip3 install --user -q pyyaml rich
fi

# Start containers if needed (--wait handles healthchecks)
if ! docker compose -f integration/docker/docker-compose.yml ps --status running 2>/dev/null | grep -q "www1"; then
    echo "Starting Docker containers..."
    docker compose -f integration/docker/docker-compose.yml up -d --wait
fi

# Run from project root
cd ..

echo "Running: python3 -m db_sync_tool -f tests/integration/scenario/receiver/typo3/typo3_env.json --output $OUTPUT_MODE $EXTRA_ARGS"
echo ""

python3 -m db_sync_tool \
    -f tests/integration/scenario/receiver/typo3/typo3_env.json \
    --output "$OUTPUT_MODE" \
    $EXTRA_ARGS

echo ""
echo "Done."

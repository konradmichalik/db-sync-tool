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

# Build and start containers if needed
if ! docker compose -f integration/docker/docker-compose.yml ps --status running 2>/dev/null | grep -q "www1"; then
    echo "Building and starting Docker containers..."
    docker compose -f integration/docker/docker-compose.yml build
    docker compose -f integration/docker/docker-compose.yml up -d --wait
fi

# Config path inside container
CONFIG="/var/www/html/tests/integration/configs/typo3_env/sync-www1-to-local.json"

echo "Running inside container: db_sync_tool -f $CONFIG --output $OUTPUT_MODE $EXTRA_ARGS"
echo ""

# Run inside www1 container using mounted source code
docker compose -f integration/docker/docker-compose.yml exec -T www1 \
    python3 -m db_sync_tool -f "$CONFIG" --output "$OUTPUT_MODE" -y $EXTRA_ARGS

echo ""
echo "Done."

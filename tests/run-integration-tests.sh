#!/bin/bash
# Run integration tests (requires Docker)
set -e

cd "$(dirname "$0")"

# Determine pytest command (prefer python3 -m pytest, fallback to pipx)
if python3 -c "import pytest" 2>/dev/null; then
    PYTEST_CMD="python3 -m pytest"
else
    PYTEST_CMD="pipx run pytest"
fi

# Start containers if needed
if ! docker compose -f integration/docker/docker-compose.yml ps --status running 2>/dev/null | grep -q "www1"; then
    echo "Starting Docker containers..."
    docker compose -f integration/docker/docker-compose.yml up -d --wait
    sleep 5
fi

# Run tests
echo "Running integration tests..."
$PYTEST_CMD integration/ -v "$@"

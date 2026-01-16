#!/bin/bash
# Run integration tests (requires Docker)
set -e

cd "$(dirname "$0")"

# Start containers if needed
if ! docker compose -f docker/docker-compose.yml ps --status running 2>/dev/null | grep -q "www1"; then
    echo "Starting Docker containers..."
    docker compose -f docker/docker-compose.yml up -d --wait
    sleep 5
fi

# Run tests
echo "Running integration tests..."
python3 -m pytest integration/ -v "$@"

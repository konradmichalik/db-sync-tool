#!/bin/bash
# Run db-sync-tool integration tests (require Docker)
# For unit tests only, use: ./run_unit_tests.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate or create venv
if [ -d "$PROJECT_DIR/.venv" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
else
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/.venv"
    source "$PROJECT_DIR/.venv/bin/activate"
    pip install -q pytest
fi

# Start containers if needed
cd "$SCRIPT_DIR/docker"
if ! docker compose ps --status running 2>/dev/null | grep -q "www1"; then
    echo "Starting Docker containers..."
    docker compose up -d --wait
    sleep 5
fi

# Run integration tests
cd "$SCRIPT_DIR"
echo "Running integration tests..."
pytest integration/ "$@"

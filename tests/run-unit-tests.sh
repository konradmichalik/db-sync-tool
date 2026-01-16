#!/bin/bash
# Run unit tests (no Docker required)
# Usage: ./run-unit-tests.sh [--cov] [pytest-args]
set -e

cd "$(dirname "$0")"

# Determine pytest command (prefer python3 -m pytest, fallback to pipx)
if python3 -c "import pytest" 2>/dev/null; then
    PYTEST_CMD="python3 -m pytest"
else
    PYTEST_CMD="pipx run pytest"
fi

PYTEST_ARGS=""
if [[ "$1" == "--cov" ]]; then
    shift
    PYTEST_ARGS="--cov=db_sync_tool.utility.security --cov=db_sync_tool.utility.pure --cov=db_sync_tool.utility.config --cov=db_sync_tool.recipes.parsing --cov-report=term-missing"
    # Coverage requires pytest-cov
    if [[ "$PYTEST_CMD" == "pipx run pytest" ]]; then
        PYTEST_CMD="pipx run --spec pytest-cov pytest"
    fi
    echo "Running unit tests with coverage..."
else
    echo "Running unit tests..."
fi

$PYTEST_CMD unit/ -v $PYTEST_ARGS "$@"

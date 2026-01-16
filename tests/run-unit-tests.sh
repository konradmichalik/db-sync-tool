#!/bin/bash
# Run unit tests (no Docker required)
# Usage: ./run-unit-tests.sh [--cov] [pytest-args]
set -e

cd "$(dirname "$0")"

PYTEST_ARGS=""
if [[ "$1" == "--cov" ]]; then
    shift
    PYTEST_ARGS="--cov=db_sync_tool.utility.security --cov-report=term-missing"
    echo "Running unit tests with coverage..."
else
    echo "Running unit tests..."
fi

python3 -m pytest unit/ -v $PYTEST_ARGS "$@"

#!/bin/bash
# Run unit tests (no Docker required)
# These tests are fast and don't require any external dependencies

set -e

cd "$(dirname "$0")/.."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
pip install -q pytest

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v "$@"

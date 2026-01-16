#!/bin/bash
# Run unit tests (no Docker required)
set -e

cd "$(dirname "$0")"

echo "Running unit tests..."
python3 -m pytest unit/ -v "$@"

#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get script's parent directory and navigate to the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=== Cleaning old builds ==="
rm -rf dist/ build/ *.egg-info/ flow2code.egg-info/

echo "=== Creating temporary virtual environment ==="
VENV_DIR=".publish_venv"
python3 -m venv "$VENV_DIR"

# Ensure venv is cleaned up on exit (success, failure, or cancellation)
cleanup() {
    echo "=== Cleaning up virtual environment ==="
    rm -rf "$VENV_DIR"
}
trap cleanup EXIT

echo "=== Installing/Updating build and twine inside venv ==="
"$VENV_DIR/bin/pip" install --upgrade build twine

echo "=== Building package ==="
"$VENV_DIR/bin/python3" -m build

echo "=== Checking package ==="
"$VENV_DIR/bin/twine" check dist/*

echo ""
echo "Choose where to publish:"
echo "1) TestPyPI (sandbox - recommended first)"
echo "2) PyPI (live registry)"
echo "3) Cancel"
read -rp "Enter choice [1-3]: " choice

case $choice in
    1)
        echo "=== Uploading to TestPyPI ==="
        "$VENV_DIR/bin/twine" upload --repository testpypi dist/*
        ;;
    2)
        echo "=== Uploading to PyPI ==="
        "$VENV_DIR/bin/twine" upload dist/*
        ;;
    *)
        echo "Publish cancelled."
        exit 0
        ;;
esac

echo "=== Done! ==="

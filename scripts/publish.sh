#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get script's parent directory and navigate to the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=== Cleaning old builds ==="
rm -rf dist/ build/ *.egg-info/ flow2code.egg-info/

echo "=== Installing/Updating build and twine ==="
python3 -m pip install --upgrade build twine

echo "=== Building package ==="
python3 -m build

echo "=== Checking package ==="
python3 -m twine check dist/*

echo ""
echo "Choose where to publish:"
echo "1) TestPyPI (sandbox - recommended first)"
echo "2) PyPI (live registry)"
echo "3) Cancel"
read -rp "Enter choice [1-3]: " choice

case $choice in
    1)
        echo "=== Uploading to TestPyPI ==="
        python3 -m twine upload --repository testpypi dist/*
        ;;
    2)
        echo "=== Uploading to PyPI ==="
        python3 -m twine upload dist/*
        ;;
    *)
        echo "Publish cancelled."
        exit 0
        ;;
esac

echo "=== Done! ==="

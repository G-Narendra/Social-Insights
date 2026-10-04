#!/bin/bash
# Bootstrap script for Unix/macOS/Linux
# Creates the virtual environment and installs all dependencies locally.
# Usage: bash scripts/bootstrap.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=== Social Insights Bootstrap ==="

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Verify we're using the venv
VENV_PYTHON=".venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: venv python not found at $VENV_PYTHON"
    exit 1
fi

echo "Using Python: $($VENV_PYTHON --version)"
echo "sys.prefix: $($VENV_PYTHON -c 'import sys; print(sys.prefix)')"

# Install dependencies
echo "Installing runtime dependencies..."
$VENV_PYTHON -m pip install --upgrade pip
$VENV_PYTHON -m pip install -r requirements.txt

echo "Installing dev dependencies..."
$VENV_PYTHON -m pip install -r requirements-dev.txt

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo ""
echo "=== Bootstrap complete ==="
echo "Activate the venv: source .venv/bin/activate"
echo "Run tests: .venv/bin/python -m pytest"
echo "Start server: .venv/bin/python -m uvicorn app.main:app --reload --app-dir backend"

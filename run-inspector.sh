#!/usr/bin/env bash
# Linux/macOS equivalent of run-inspector.ps1: launch the MCP Inspector against server.py.
set -euo pipefail

# Operate from the directory where this script lives
cd "$(dirname "${BASH_SOURCE[0]}")"

# Prefer python3 (the usual name on Linux/macOS), fall back to python
PYTHON="${PYTHON:-$(command -v python3 || command -v python || true)}"

if [[ -z "$PYTHON" ]]; then
    echo "Error: neither python3 nor python was found on your PATH." >&2
    echo "Install Python 3.12+, or point to one with: PYTHON=/path/to/python ./run-inspector.sh" >&2
    exit 1
fi

echo -e "\033[36mStarting MCP Inspector...\033[0m"

# Run the Inspector with the Python server
exec npx @modelcontextprotocol/inspector "$PYTHON" server.py

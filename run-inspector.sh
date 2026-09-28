#!/usr/bin/env bash
# Linux/macOS equivalent of run-inspector.ps1: launch the MCP Inspector against server.py.
set -euo pipefail

# Operate from the directory where this script lives
cd "$(dirname "${BASH_SOURCE[0]}")"

# Prefer python3 (the usual name on Linux/macOS), fall back to python
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"

echo -e "\033[36mStarting MCP Inspector...\033[0m"

# Run the Inspector with the Python server
exec npx @modelcontextprotocol/inspector "$PYTHON" server.py

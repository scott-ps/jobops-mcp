# Ensure the terminal operates from the directory where this script lives
Set-Location $PSScriptRoot

Write-Host "Starting MCP Inspector..." -ForegroundColor Cyan

# Run the Inspector with your Python server
npx @modelcontextprotocol/inspector python server.py
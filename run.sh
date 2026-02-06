#!/bin/bash
# Run script - automatically uses venv if present

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run main
if [ "$1" == "original" ] || [ "$1" == "-o" ]; then
    python3 main_original.py
else
    python3 main.py
fi

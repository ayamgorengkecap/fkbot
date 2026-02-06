#!/bin/bash
# VKSerbot Unified - Installation Script
# Supports: Direct install, venv, or break-system-packages

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================="
echo "VKSerbot Unified - Installer"
echo "=================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found!"
    echo "Install: sudo apt install python3 python3-pip"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Check if externally managed
IS_MANAGED=$(python3 -c "import sys; print('managed' if hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix or sys.version_info >= (3, 11) else 'normal')" 2>/dev/null)

install_packages() {
    local PIP_CMD="$1"
    echo "Installing dependencies..."
    echo ""
    
    # Core (required)
    $PIP_CMD install requests --quiet && echo "✓ requests" || echo "✗ requests (required!)"
    
    # Optional dependencies
    $PIP_CMD install instagrapi pydantic Pillow --quiet 2>/dev/null && echo "✓ Instagram support" || echo "⚠ Instagram support skipped"
    $PIP_CMD install Telethon cryptography pyaes rsa --quiet 2>/dev/null && echo "✓ Telegram support" || echo "⚠ Telegram support skipped"
    $PIP_CMD install faker --quiet 2>/dev/null && echo "✓ faker"
}

# Option 1: Use existing venv if present
if [ -d "venv" ]; then
    echo "Found existing venv, using it..."
    source venv/bin/activate
    install_packages "pip"
    echo ""
    echo "Usage: source venv/bin/activate && python3 main.py"
    
# Option 2: Create new venv
elif [ "$1" == "--venv" ] || [ "$1" == "-v" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    install_packages "pip"
    echo ""
    echo "Usage: source venv/bin/activate && python3 main.py"

# Option 3: Force system install
elif [ "$1" == "--system" ] || [ "$1" == "-s" ]; then
    echo "Installing to system Python (--break-system-packages)..."
    install_packages "pip3 --break-system-packages"
    echo ""
    echo "Usage: python3 main.py"

# Default: Try direct install, fallback to venv
else
    echo "Trying direct install..."
    if pip3 install requests --quiet 2>/dev/null; then
        install_packages "pip3"
        echo ""
        echo "Usage: python3 main.py"
    else
        echo ""
        echo "Direct install failed (externally managed environment)"
        echo ""
        echo "Options:"
        echo "  1. Create venv:    ./install.sh --venv"
        echo "  2. Force system:   ./install.sh --system"
        echo ""
        echo "Or manually:"
        echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
fi

echo ""
echo "=================================="
echo "Installation complete!"
echo "=================================="

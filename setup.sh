#!/bin/bash
set -e

echo "🚀 Setting up Daily AI Newspaper..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel > /dev/null
pip install -r requirements.txt > /dev/null
echo "✓ Dependencies installed"

# Setup environment file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Created .env from .env.example - please fill in your API keys"
    else
        echo "❌ .env.example not found"
        exit 1
    fi
else
    echo "✓ .env already exists"
fi

# Create output directory structure
mkdir -p output/current output/images frontend backend
echo "✓ Directory structure created"

# Create output/.gitkeep files
touch output/.gitkeep output/current/.gitkeep output/images/.gitkeep

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Test: python backend/main.py"
echo ""
echo "For GitHub Actions:"
echo "1. Add these secrets to your GitHub repository:"
echo "   - GEMINI_API_KEY"
echo "   - META_AI_COOKIE (optional)"
echo "   - NETLIFY_AUTH_TOKEN (optional)"
echo "   - NETLIFY_SITE_ID (optional)"
echo ""

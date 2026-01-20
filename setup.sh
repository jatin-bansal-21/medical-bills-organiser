#!/bin/bash

# Setup script for Intelligent Medical File Sorter
# This script sets up the development environment

set -e

echo "🔧 Setting up Medical File Sorter..."
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Found Python $PYTHON_VERSION"

# Check for Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed."
    echo "   Install it with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

POETRY_VERSION=$(poetry --version)
echo "✓ Found $POETRY_VERSION"

# Check for poppler (required for pdf2image)
if ! command -v pdftoppm &> /dev/null; then
    echo ""
    echo "⚠️  poppler is not installed (required for PDF processing)."
    echo "   Install it with: brew install poppler"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Found poppler"
fi

# Configure Poetry to use in-project virtualenv
echo ""
echo "📦 Configuring Poetry..."
poetry config virtualenvs.in-project true --local

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
poetry install

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your OpenAI API key"
echo "  2. Activate the virtual environment: poetry shell"
echo "  3. Run the tool: medical-sorter /path/to/documents"
echo ""
echo "Or run directly: poetry run medical-sorter /path/to/documents"

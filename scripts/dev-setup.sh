#!/bin/bash
# Development setup script for Synapse

set -e

echo "🔧 Setting up Synapse development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.11"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
    echo "✅ Python $python_version detected (>= 3.11 required)"
else
    echo "❌ Python 3.11+ required. Current version: $python_version"
    exit 1
fi

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install -e ".[dev]"

# Install build tools
echo "🏗️ Installing build tools..."
pip install build

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🚀 Next steps:"
echo "  • Run quality checks: ./scripts/quality-check.sh"
echo "  • Run tests: ./scripts/test.sh"
echo "  • Build package: ./scripts/build.sh"
echo "  • See all scripts: ls scripts/"
#!/bin/bash
# Quality check script for Synapse

set -e

echo "🔍 Running quality checks..."

echo ""
echo "1. 🎨 Code formatting (black)..."
black synapse/

echo ""
echo "2. 🔧 Code linting (ruff)..."
ruff check . --fix

echo ""
echo "3. 🔒 Type checking (mypy)..."
mypy synapse/

echo ""
echo "4. 🧪 Running tests..."
pytest --tb=short

echo ""
echo "✅ All quality checks passed!"
echo ""
echo "📊 Optional: Run with coverage:"
echo "  pytest --cov=synapse --cov-report=html"
echo "  open htmlcov/index.html"
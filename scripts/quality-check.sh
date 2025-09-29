#!/bin/bash
# Quality check script for Synapse

set -e

echo "🔍 Running quality checks..."

echo ""
echo "1. 🎨 Code formatting and linting (ruff)..."
ruff check .

echo ""
echo "2. 🔒 Type checking (mypy)..."
mypy synapse/

echo ""
echo "3. 🧪 Running tests..."
pytest --tb=short

echo ""
echo "✅ All quality checks passed!"
echo ""
echo "📊 Optional: Run with coverage:"
echo "  pytest --cov=synapse --cov-report=html"
echo "  open htmlcov/index.html"
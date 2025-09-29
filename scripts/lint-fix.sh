#!/bin/bash
# Auto-fix linting issues

set -e

echo "🎨 Auto-fixing code style issues..."

echo "1. 🔧 Fixing ruff issues..."
ruff check --fix .

echo "2. 🎯 Formatting code..."
ruff format .

echo ""
echo "✅ Auto-fixes applied!"
echo ""
echo "🔍 Run quality checks to verify:"
echo "  ./scripts/quality-check.sh"
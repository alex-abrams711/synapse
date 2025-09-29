#!/bin/bash
# Test script for Synapse

set -e

# Default to all tests if no arguments provided
TEST_PATH=${1:-"tests/"}

echo "🧪 Running tests..."

if [ "$1" = "--coverage" ] || [ "$1" = "-c" ]; then
    echo "📊 Running tests with coverage..."
    pytest --cov=synapse --cov-report=html --cov-report=term-missing tests/
    echo ""
    echo "📋 Coverage report generated: htmlcov/index.html"
    echo "🌐 Open coverage report: open htmlcov/index.html"
elif [ "$1" = "--contracts" ]; then
    echo "📋 Running contract tests..."
    pytest specs/001-poc-use-specify/contracts/ -v
elif [ "$1" = "--integration" ]; then
    echo "🔗 Running integration tests..."
    pytest tests/integration/ -v
elif [ "$1" = "--unit" ]; then
    echo "🔧 Running unit tests..."
    pytest tests/unit/ -v
elif [ "$1" = "--cli" ]; then
    echo "⚡ Running CLI tests..."
    pytest tests/cli/ -v
else
    echo "🏃 Running all tests: $TEST_PATH"
    pytest "$TEST_PATH" -v
fi

echo ""
echo "✅ Tests completed!"
echo ""
echo "📚 Available test options:"
echo "  ./scripts/test.sh --coverage     # Run with coverage report"
echo "  ./scripts/test.sh --contracts    # Run contract tests only"
echo "  ./scripts/test.sh --integration  # Run integration tests only"
echo "  ./scripts/test.sh --unit         # Run unit tests only"
echo "  ./scripts/test.sh --cli          # Run CLI tests only"
echo "  ./scripts/test.sh tests/specific # Run specific test path"
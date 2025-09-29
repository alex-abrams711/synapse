#!/bin/bash
# Build script for Synapse

set -e

echo "🏗️ Building Synapse package..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Run quality checks first
echo "🔍 Running quality checks..."
./scripts/quality-check.sh

echo ""
echo "📦 Building distribution packages..."
python -m build

echo ""
echo "📋 Build artifacts:"
ls -la dist/

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "🚀 Next steps:"
echo "  • Install locally: pip install dist/synapse_workflow-*.whl"
echo "  • Test installation: synapse --version"
echo "  • Upload to PyPI: twine upload dist/*"
echo ""
echo "🧪 Test the built package:"
echo "  pip install --force-reinstall dist/synapse_workflow-*.whl"
echo "  cd /tmp && mkdir test && cd test"
echo "  synapse init --project-name 'Test Build'"
#!/bin/bash
# Demo script showing Synapse capabilities

set -e

echo "🎬 Synapse Demo - Agent Workflow System"
echo "======================================"

# Create a temporary demo directory
DEMO_DIR="/tmp/synapse-demo-$(date +%s)"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

echo ""
echo "📁 Demo directory: $DEMO_DIR"

echo ""
echo "1. 🚀 Initializing Synapse project..."
synapse init --project-name "Demo Project"

echo ""
echo "2. 📂 Project structure created:"
echo "├── .claude/agents/     (AI agent templates)"
echo "├── .claude/commands/   (Claude Code slash commands)"
echo "├── .synapse/          (Workflow configuration)"
echo "└── CLAUDE.md          (Main context file)"

echo ""
echo "3. 📋 Generated files:"
find . -type f -name "*.md" -o -name "*.yaml" -o -name "*.json" | sort

echo ""
echo "4. ⚙️ Configuration preview:"
echo "--- .synapse/config.yaml ---"
head -10 .synapse/config.yaml

echo ""
echo "5. 📊 Task log structure:"
echo "--- .synapse/task_log.json ---"
cat .synapse/task_log.json

echo ""
echo "✅ Demo completed!"
echo ""
echo "🎯 What you can do next:"
echo "  • Open this project in Claude Code"
echo "  • Use /status, /workflow, /validate, /agent commands"
echo "  • Let the DEV, AUDITOR, DISPATCHER agents collaborate"
echo ""
echo "📁 Demo files location: $DEMO_DIR"
echo "🧹 Clean up: rm -rf $DEMO_DIR"
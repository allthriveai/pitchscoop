#!/bin/bash
# Quick install script for PitchScoop FastMCP server with Claude Desktop

echo "🚀 Installing PitchScoop MCP Server for Claude Desktop"
echo "========================================================"
echo ""

# Create Claude config directories
echo "📁 Creating Claude config directories..."
mkdir -p ~/.config/Claude
mkdir -p ~/Library/Application\ Support/Claude

# Copy config to both locations (Claude Desktop checks both)
echo "📋 Copying MCP configuration..."
cp config/claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json
cp config/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json 2>/dev/null || true

if [ $? -eq 0 ]; then
    echo "✅ Configuration installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Quit Claude Desktop completely (Cmd+Q)"
    echo "2. Reopen Claude Desktop"
    echo "3. Look for the MCP connection indicator"
    echo ""
    echo "Try asking Claude:"
    echo "  - 'What PitchScoop tools do you have?'"
    echo "  - 'Start onboarding for me as an organizer'"
    echo "  - 'Help me create a pitch competition'"
    echo ""
    echo "📚 See docs/setup/FASTMCP_MIGRATION.md for more info"
else
    echo "❌ Installation failed"
    exit 1
fi

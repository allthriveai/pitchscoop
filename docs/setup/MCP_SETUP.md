# PitchScoop MCP Server Setup Guide

Your PitchScoop MCP server is built and ready! Here's how to activate it with Claude Desktop.

## What You Have

- ✅ **MCP Server**: `api/mcp_server.py` - Fully functional with all tools
- ✅ **Docker Services**: Running and healthy (Redis, PostgreSQL, MinIO, API)
- ✅ **Configuration**: `config/claude_desktop_config.json` - Ready to install
- ✅ **Onboarding Tools**: Just integrated and ready to use!

## Quick Setup (3 Steps)

### Step 1: Test the MCP Server

First, let's make sure it works:

```bash
chmod +x test_mcp_local.sh
./test_mcp_local.sh
```

You should see JSON output with tool definitions. If you see errors, let me know!

### Step 2: Install Configuration in Claude Desktop

Copy the config to Claude Desktop's expected location:

```bash
# Create the Claude config directory
mkdir -p ~/.config/Claude

# Copy your MCP server configuration
cp config/claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json
```

### Step 3: Restart Claude Desktop

- Quit Claude Desktop completely (Cmd+Q)
- Reopen Claude Desktop
- Look for a 🔌 (plug) icon or "MCP" indicator in the interface

## Verify It's Working

Once Claude Desktop restarts, you should be able to ask Claude things like:

- "What PitchScoop tools do you have available?"
- "Start the onboarding process for me as a participant"
- "Help me create a new pitch competition event"

## Available Tools

Your MCP server exposes these domains:

1. **System Tools** - Setup, diagnostics, environment checks
2. **Onboarding Tools** ⭐ (NEW!) - Interactive onboarding flows
3. **Events Tools** - Create and manage competitions
4. **Pitches Tools** - Video analysis with Hume AI emotions
5. **Scoring Tools** - AI-powered pitch scoring
6. **Chat Tools** - RAG-powered conversations over data
7. **Market Tools** - Market research and analysis

## Troubleshooting

### MCP Server Won't Start

```bash
# Check if Docker services are running
docker compose ps

# If not, start them
docker compose up -d

# Check API logs
docker compose logs api
```

### Claude Desktop Doesn't Show MCP Connection

1. Make sure the config file is at `~/.config/Claude/claude_desktop_config.json`
2. Verify the path in the config matches your actual project path
3. Completely quit and restart Claude Desktop (not just close the window)
4. Check Claude Desktop logs (if available in the app)

### "Module not found" or Import Errors

This means the MCP server can't find dependencies. Check:

```bash
# Install MCP dependencies in the Docker container
docker compose exec api pip install mcp anthropic-mcp
```

## How It Works

1. **Claude Desktop** reads `~/.config/Claude/claude_desktop_config.json`
2. When you chat, it runs: `docker compose exec api python mcp_server.py`
3. **MCP server** exposes all PitchScoop tools via stdio protocol
4. **Claude** can now call any tool (create events, analyze pitches, run onboarding, etc.)
5. Results flow back through the MCP protocol to Claude's responses

## Next Steps

Once connected, try:
- "Walk me through the onboarding as an event organizer"
- "What information do you need to create a pitch competition?"
- "Show me how to analyze a pitch video"

## Need Help?

If something isn't working:
1. Run the test script: `./test_mcp_local.sh`
2. Check Docker logs: `docker compose logs api`
3. Verify config path: `cat ~/.config/Claude/claude_desktop_config.json`

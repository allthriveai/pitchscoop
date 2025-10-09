# ChatGPT MCP Setup Guide

## Overview

This guide helps you connect ChatGPT to PitchScoop via an MCP bridge, allowing ChatGPT to use PitchScoop's pitch competition tools directly.

⚠️ **Note**: ChatGPT doesn't have native MCP support yet, so we use community MCP bridges.

## Prerequisites

1. **Docker Desktop** installed and running
2. **Node.js** (for MCP bridge installation)
3. **ChatGPT Plus subscription** (recommended for best experience)

## Setup Steps

### 1. Install MCP-ChatGPT Bridge

```bash
# Install the community MCP bridge
npm install -g mcp-chatgpt

# Or clone and build from source
git clone https://github.com/wong2/mcp-chatgpt
cd mcp-chatgpt
npm install
npm run build
```

### 2. Install PitchScoop

```bash
# Clone PitchScoop
git clone <pitchscoop-repo-url>
cd pitchscoop

# Start services
docker compose up -d
```

### 3. Configure MCP Bridge

Create MCP bridge configuration file:

```bash
# Create config directory
mkdir -p ~/.config/mcp-chatgpt

# Copy our config template
cp config/chatgpt_mcp_config.json ~/.config/mcp-chatgpt/config.json
```

**Important**: Update the file paths in the config to match your PitchScoop location.

### 4. Start MCP Bridge

```bash
# Start the bridge
mcp-chatgpt --config ~/.config/mcp-chatgpt/config.json
```

The bridge should output something like:
```
✅ Connected to PitchScoop MCP server
🔗 Bridge running on port 3001
```

### 5. Connect ChatGPT

1. Open ChatGPT in your browser
2. Look for MCP connection options (this varies by bridge implementation)
3. Connect to `http://localhost:3001` (or the port shown by your bridge)

### 6. Test Connection

In ChatGPT, try:

> "Help me set up my pitch competition platform"

ChatGPT should respond with system status and setup guidance.

## Available Commands

Once connected, you can ask ChatGPT to:

### System Management
- "Check if PitchScoop is running"
- "Start the PitchScoop services"
- "Run system diagnostics"
- "Generate MCP config for Claude Desktop"

### Competition Management  
- "Create a hackathon called 'AI Innovation Challenge'"
- "Add Team Alpha to the competition"
- "Start the hackathon event"

### Pitch Analysis
- "Start recording a pitch for Team Alpha"
- "Score the latest pitch recording"
- "Compare all team pitches"

## Troubleshooting

### Bridge Connection Issues

**"MCP server not found"**
1. Check Docker services: `docker compose ps`
2. Verify PitchScoop is running: `docker compose logs api`
3. Restart the MCP bridge

**"Tools not available"**
1. Check bridge logs for errors
2. Verify config file paths are correct
3. Try restarting both bridge and Docker services

### ChatGPT Integration Issues

**"Can't connect to MCP bridge"**
1. Verify bridge is running and accessible
2. Check firewall/network settings
3. Try a different port in bridge config

**"Limited functionality compared to Claude"**
- This is expected - MCP bridges may have limitations
- Some advanced features might not work perfectly
- Consider Claude Desktop for full MCP experience

## Limitations

- **Community Solution**: ChatGPT MCP bridges are third-party tools
- **Compatibility**: May not support all MCP features
- **Stability**: Less stable than native MCP support (Claude Desktop)
- **Performance**: Additional layer may slow responses

## Alternative: Use Claude Desktop

For the best PitchScoop MCP experience, consider using Claude Desktop with native MCP support:

```bash
# Generate Claude config
# (via ChatGPT with system tools connected)
"Generate MCP configuration for claude-desktop platform"

# Then follow Claude Desktop setup guide
```

## Getting Help

- **PitchScoop Issues**: Check `docker compose logs api`
- **Bridge Issues**: Check bridge documentation and logs  
- **ChatGPT Issues**: Verify browser console for errors

The MCP bridge approach works but Claude Desktop provides the most reliable experience for PitchScoop's MCP tools.
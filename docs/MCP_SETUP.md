# PitchScoop MCP Server Setup

This guide shows you how to connect Claude Desktop to your PitchScoop MCP server so Claude can manage pitch competitions directly.

## What You'll Get

Once connected, Claude Desktop can:
- ✅ Create and manage pitch events (hackathons, VC pitches, practice sessions)  
- ✅ Record and transcribe pitches using Gladia STT
- ✅ Score pitches with AI-powered analysis
- ✅ Have RAG-powered conversations about competition data
- ✅ Generate leaderboards and feedback (when implemented)

## Quick Setup (5 minutes)

### 1. Test the MCP Server

```bash
# From the pitchscoop directory
python test_mcp_server.py
```

You should see:
```
🎉 All tests passed! MCP server is ready.
```

### 2. Start Docker Environment

```bash
docker compose up -d
```

### 3. Configure Claude Desktop

Open Claude Desktop's MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "pitchscoop": {
      "command": "docker",
      "args": [
        "compose",
        "-f", "/Users/allierays/Sites/pitchscoop/docker-compose.yml",
        "exec",
        "-T",
        "api",
        "python", 
        "mcp_server.py"
      ]
    }
  }
}
```

**Important**: Update the file path to match your actual pitchscoop directory location.

### 4. Restart Claude Desktop

Completely quit and restart Claude Desktop for the configuration to take effect.

### 5. Test the Connection

In Claude Desktop, try:

> "Create a new hackathon event called 'AI Innovation Challenge'"

Claude should respond with event creation details and an event ID.

## Available Tools

Once connected, Claude has access to these tools:

### Events Domain
- `events.create_event` - Create competitions
- `events.list_events` - Browse events  
- `events.join_event` - Add participants
- `events.start_event` - Begin competitions
- `events.end_event` - Finalize results
- `events.get_event_details` - Get event info
- `events.delete_event` - Clean up test events

### Recordings Domain  
- `pitches.start_recording` - Start pitch recording
- `pitches.stop_recording` - Stop and save recording
- `pitches.get_session` - Get session details
- `pitches.get_playback_url` - Generate audio URLs
- `pitches.list_sessions` - Browse recordings
- `pitches.delete_session` - Clean up sessions

### Scoring Domain
- `analysis.score_pitch` - AI-powered scoring
- `analysis.score_idea` - Idea analysis  
- `analysis.score_technical` - Technical review
- `analysis.score_tools` - Tool usage analysis
- `analysis.score_presentation` - Delivery analysis
- `analysis.compare_pitches` - Multi-pitch comparison

### Chat Domain
- `chat.start_conversation` - Begin RAG conversation
- `chat.send_message` - Chat with context
- `chat.search_documents` - Search competition data
- `chat.ask_about_pitch` - Pitch-specific Q&A
- `chat.compare_sessions` - Compare multiple pitches
- `chat.get_conversation_history` - View chat history

## Example Workflows

### Create and Run a Competition

```
You: "Create a 2-day hackathon called 'Fintech Innovation Challenge' with 50 participants"

Claude: [Creates event and returns details]

You: "Add Team Alpha to the event"

Claude: [Adds participant]

You: "Start the event"

Claude: [Activates event for recordings]

You: "Team Alpha wants to record their pitch about a crypto trading bot"

Claude: [Starts recording session]
```

### Analyze Pitches

```  
You: "Score the last recorded pitch using all criteria"

Claude: [Provides detailed AI analysis with scores]

You: "How does this compare to other teams?"

Claude: [Provides comparative analysis]

You: "Start a conversation to discuss this pitch in detail"

Claude: [Creates RAG-powered chat about the pitch]
```

## Troubleshooting

### Connection Issues

**"MCP server not found"**
- Check that Docker is running: `docker compose ps`
- Verify file paths in Claude Desktop config
- Restart Claude Desktop completely

**"Tool execution failed"**  
- Check Docker logs: `docker compose logs api`
- Verify Redis/MinIO are running: `docker compose ps`
- Test with: `python test_mcp_server.py`

### Tool Issues

**"Redis connection failed"**
```bash
docker compose up redis -d
```

**"Gladia API errors"**
- Tools work in mock mode without API key
- Set `GLADIA_API_KEY` in environment for real STT

## Development Testing

Test tools directly:
```bash
# Test all domains
python test_mcp_server.py

# Test specific integration
docker compose exec api python tests/test_mcp_integration.py
```

## What's Next

Once the MCP server is working:

1. **Create your first event** via Claude Desktop
2. **Record a test pitch** (works with mock audio)
3. **Score the pitch** using AI analysis  
4. **Try the chat features** for Q&A about the competition
5. **Implement leaderboards and feedback** domains (coming next)

The MCP server provides the foundation - now you can experience the full AI-powered pitch competition workflow!
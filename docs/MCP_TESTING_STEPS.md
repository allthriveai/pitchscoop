# How to Test Your PitchScoop MCP Server

## ✅ What We Just Set Up
- [x] Docker containers running (api, redis, minio)
- [x] MCP server working with 18 tools
- [x] Claude Desktop config file installed

---

## **Step-by-Step Testing**

### **Step 1: Open Claude Desktop**

1. **Launch Claude Desktop app** on your Mac
2. **Completely quit and restart** Claude Desktop (very important!)
   - Click Claude → Quit Claude (or Cmd+Q)
   - Open Claude Desktop again
3. Look for any MCP connection indicators in the interface

### **Step 2: Test MCP Connection**

In Claude Desktop, type exactly this:

```
What tools do you have access to?
```

**✅ Expected Response:** Claude should list your tools:
- `events.create_event` - Create competitions
- `events.list_events` - Browse events
- `pitches.start_recording` - Start recording
- `analysis.score_pitch` - AI scoring
- And 14 more tools...

**❌ If Claude says "I don't have access to any tools":**
- See Troubleshooting section below

### **Step 3: Create Your First Event**

Try this message:

```
Create a new hackathon event called "AI Innovation Challenge" that runs for 2 days with up to 50 participants
```

**✅ Expected Response:** Claude should:
1. Use the `events.create_event` tool
2. Return an event_id (like `evt_abc123...`)
3. Show event details with status "upcoming"

**Example good response:**
```json
{
  "event_id": "evt_12345",
  "event_name": "AI Innovation Challenge",
  "event_type": "hackathon", 
  "status": "upcoming",
  "max_participants": 50,
  "duration_minutes": 2880
}
```

### **Step 4: Test Event Management**

Try these commands one by one:

```
List all events
```

```
Add a team called "Team Alpha" with email "alpha@example.com" to the AI Innovation Challenge
```

```
Start the AI Innovation Challenge event
```

Each should work and show the results.

### **Step 5: Test Recording Workflow**

```
Start a recording session for Team Alpha pitching their "Revolutionary Trading Bot" project
```

**Expected:** Returns session_id and recording details.

Then:
```
Stop that recording session
```

```
Show me the details of that recording session
```

### **Step 6: Test AI Scoring**

```
Score Team Alpha's pitch using all available criteria
```

**Expected:** Claude uses AI analysis to score the pitch across multiple criteria like innovation, technical quality, presentation skills, etc.

### **Step 7: Test Complex Workflow**

Try a multi-step workflow:

```
Create a VC pitch event called "Startup Showcase", add Team Beta to it, have them record a pitch about "Next-Gen Fintech", then score their pitch and show me the results
```

Claude should chain multiple tools together automatically.

---

## **Troubleshooting**

### **🚫 Problem: "I don't have access to any tools"**

**Solutions (try in order):**

1. **Verify Docker is running:**
   ```bash
   cd /Users/allierays/Sites/pitchscoop
   docker compose ps
   ```
   Should show 3 containers running.

2. **Completely restart Claude Desktop:**
   - Quit Claude completely (not just close window)
   - Wait 5 seconds
   - Open Claude Desktop again

3. **Check the config file:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
   Should show the pitchscoop MCP server config.

4. **Test server manually:**
   ```bash
   docker compose exec api python -c "from mcp_server_simple import PitchScoopMCPServerSimple; print('✅ Server works')"
   ```

### **🚫 Problem: "Tool execution failed"**

1. **Check Docker logs:**
   ```bash
   docker compose logs api
   ```

2. **Restart all containers:**
   ```bash
   docker compose down
   docker compose up -d
   ```

3. **Wait a few seconds** then try again in Claude

### **🚫 Problem: Tools return "Redis connection error"**

This is normal if Redis isn't fully started. Wait 30 seconds and try again.

---

## **What Success Looks Like**

### **🎯 Minimum Success:**
- ✅ Claude sees your tools
- ✅ Can create an event
- ✅ Can list events
- ✅ Can start/stop recording
- ✅ Can score a pitch

### **🚀 Full Success:**
- ✅ All individual tools work
- ✅ Multi-step workflows work
- ✅ Error messages are helpful
- ✅ Can manage complete pitch competition

---

## **Real-World Test Scenario**

Once basic tools work, try this complete scenario:

```
I want to run a 3-day startup competition called "TechCrunch Battlefield". Create the event, add three teams (Team Alpha, Team Beta, Team Gamma), start the event, have each team record a 5-minute pitch (Alpha: AI platform, Beta: green energy, Gamma: health tech), score all the pitches, and show me how they compare.
```

If Claude can execute this full workflow, your MCP integration is working perfectly!

---

## **Next Steps After Testing**

Once this works:

1. **🎉 Celebrate!** You have a working AI-powered pitch platform
2. **Demo it** to stakeholders/investors
3. **Add missing domains** (leaderboards, feedback, chat)
4. **Get real Gladia API key** for actual audio recording
5. **Deploy to production** environment

**You've successfully built the bridge between AI assistants and your pitch competition platform!** 🚀
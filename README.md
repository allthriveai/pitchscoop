# PitchScoop

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![FastMCP 2.0](https://img.shields.io/badge/FastMCP-2.0-purple.svg)](https://github.com/jlowin/fastmcp)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/redis-7.2+-red.svg)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**MCP-First AI-Powered Pitch Competition Platform**

A modern platform built around **Model Context Protocol (MCP)** using **FastMCP 2.0** for AI-assisted pitch competition management. Expose event creation, onboarding, scoring, and market research through **18 standardized MCP tools** for seamless Claude Desktop integration.

## 🏆 Key Features

- **🔌 MCP-First Architecture**: 18 tools via FastMCP 2.0 for AI assistant integration
- **🎯 Smart Onboarding**: Guided event creation and participant registration
- **🧠 AI-Powered Analysis**: Multi-dimensional pitch scoring using Azure OpenAI
- **📊 Market Research**: Competitive intelligence and industry analysis
- **☁️ Cloud-Native**: Containerized with PostgreSQL, Redis, and MinIO

## 🚀 Quick Start for Developers

### Prerequisites
- Docker Desktop installed and running
- Python 3.11+ (for local testing)
- Claude Desktop (optional, for MCP integration)

### 1. Start the Application

```bash
# Clone and setup
git clone <repository-url>
cd pitchscoop

# Copy environment configuration
cp .env.example .env

# Start all services
docker compose up --build
```

### 2. Verify Setup

```bash
# Test API health
curl localhost:8000/api/healthz
# Expected: {"ok": true}

# Test MCP server (shows 18 available tools)
docker compose exec api python api/mcp_server.py
```

**Key URLs:**
- 🌐 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🐘 **PostgreSQL**: localhost:5433 (username: `postgres`, password: `postgres`, database: `pitchscoop`)
- 🗄️ **MinIO Console**: http://localhost:9001 (username: `pitchscoop`, password: `pitchscoop123`)
- 🔴 **RedisInsight**: http://localhost:8001

## 🔌 Claude Desktop MCP Setup

### 1. Install MCP Configuration

Run the installation script to configure Claude Desktop:

```bash
./install_mcp.sh
```

This installs the MCP server configuration at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### 2. Restart Claude Desktop

Completely quit and restart Claude Desktop (Cmd+Q on macOS, then reopen).

### 3. Verify Connection

In Claude Desktop, ask:
- *"What PitchScoop tools do you have?"*
- *"Start onboarding for me as an organizer"*

You should see 18 available MCP tools across domains like `system`, `onboarding`, `events`, `scoring`, `chat`, `market`, and `pitches`.

### Troubleshooting MCP Connection

```bash
# Verify config is installed
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Check MCP server works directly
docker compose exec api python api/mcp_server.py

# Restart Claude Desktop completely
```

## 🔧 Development Workflow

```bash
# Start services in background
docker compose up -d --build

# View API logs
docker compose logs -f api

# Run tests
docker compose exec api pytest tests/

# Test onboarding flow
./test.sh

# Access PostgreSQL
docker compose exec postgres psql -U postgres -d pitchscoop

# Stop services
docker compose down
```


## 🏗️ Technical Architecture

### Core Technology Stack

| Layer | Technology | Purpose |
|-------|------------|----------|
| **API Framework** | FastAPI 0.115+ | High-performance async API |
| **MCP Integration** | FastMCP 2.0 | Model Context Protocol for AI assistants |
| **AI Analysis** | Azure OpenAI GPT-4 | Pitch scoring and market research |
| **Database** | PostgreSQL | Event data, onboarding, user profiles |
| **Cache & Search** | Redis Stack 7.2 | Session storage, vector search |
| **Object Storage** | MinIO | Document and file storage |
| **Containerization** | Docker Compose | Multi-service orchestration |
| **Language** | Python 3.11+ | Type-safe with Pydantic models |

### Infrastructure Services

```yaml
Services:
  api:          # FastAPI application (Port 8000)
  postgres:     # PostgreSQL database (Port 5433)
  redis:        # Redis Stack with vector search (Port 6379, 8001)
  minio:        # S3-compatible storage (Ports 9000, 9001)
```


## 🔌 MCP Tools Reference

PitchScoop exposes **18 MCP tools** using **FastMCP 2.0** for clean, type-safe AI assistant integration.

### Available Tools

**System (3)**
- `system_check_environment()` - Verify Docker, API, database health
- `system_verify_setup()` - Complete environment validation
- `system_get_help(topic)` - Get help documentation

**Onboarding (4)**
- `onboarding_start(user_id, role, event_id?)` - Start organizer or participant onboarding
- `onboarding_submit_step(session_id, step_data)` - Submit step data in onboarding flow
- `onboarding_get_current_step(session_id)` - Get current step state
- `onboarding_get_help(topic)` - Context-aware onboarding help

**Events (3)**
- `events_create(...)` - Create new pitch competition
- `events_list(status?, type?)` - List events with filters
- `events_get_details(event_id)` - Get full event information

**Scoring (2 - needs to be redone)**
- `scoring_analyze_pitch(pitch_id, event_id?)` - AI-powered pitch analysis
- `scoring_get_scores(pitch_id)` - Retrieve scoring results

**Chat (1)**
- `chat_query(question, event_id?, context?)` - Ask questions about events and pitches

**Market (2)**
- `market_research(query, focus_areas?)` - Market intelligence analysis
- `market_analyze_competitors(company, industry?)` - Competitive analysis

**Pitches (3)**
- `pitches_upload(event_id, team_name, video_url?)` - Upload pitch recording
- `pitches_analyze(pitch_id, analyze_emotions?)` - Analyze pitch content
- `pitches_get_feedback(pitch_id)` - Get AI-generated feedback

### Using MCP Tools with Claude Desktop

Once configured (see setup above), simply ask Claude:

```
"Start onboarding me as an event organizer"
"Create a hackathon event called 'AI Innovation Challenge'"
"Show me all upcoming events"
"Analyze the pitch from team 'Tech Innovators'"
```

## 📚 Additional Documentation

For more detailed technical documentation, see the [`/docs`](./docs) directory.

---

**Built with FastMCP 2.0** | [Documentation](./docs) | [Issues](https://github.com/yourusername/pitchscoop/issues)

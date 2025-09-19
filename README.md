# PitchScoop

AI-powered hackathon intelligence platform with MCP (Model Context Protocol) integration.

## Quick Start

```bash
# Copy environment variables
cp .env.example .env

# Start all services (Redis, MinIO, API)
docker compose up --build

# API available at: http://localhost:8000
# FastAPI docs: http://localhost:8000/docs
```

## Documentation

All project documentation is located in the [`/docs`](./docs) folder:

- **[WARP.md](./docs/WARP.md)** - Development guidelines and architecture overview
- **[IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md)** - Complete implementation plan
- **[MCP_BUSINESS_CASE.md](./docs/MCP_BUSINESS_CASE.md)** - Business strategy and positioning
- **[Domain Documentation](./docs)** - Technical architecture and API documentation

## Project Structure

```
pitchscoop/
├── api/                    # FastAPI backend application
├── docs/                   # All project documentation
├── docker-compose.yml      # Multi-service orchestration
└── README.md              # This file
```

## Key Features

- **MCP Integration**: Protocol-compliant tools for AI assistant integration
- **AI-Powered Scoring**: Azure OpenAI and LangChain for pitch analysis
- **Multi-tenant Architecture**: Event-based isolation with Redis storage
- **Audio Processing**: Gladia STT integration with MinIO storage
- **Domain-Driven Design**: Clean architecture with separated concerns

## Development

See [docs/WARP.md](./docs/WARP.md) for detailed development guidelines and commands.

## License

MIT
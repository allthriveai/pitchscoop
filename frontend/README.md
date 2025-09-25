# PitchScoop Frontend - Chat with Transcripts

A Next.js TypeScript application providing a RAG-powered chat interface for pitch analysis and transcript exploration.

## Features

- **RAG-Powered Chat**: Chat with pitch transcripts using advanced AI and source attribution
- **Multi-Conversation Support**: Create and manage multiple conversation types (general chat, pitch analysis, scoring review, etc.)
- **Source References**: Every AI response includes clear references to source documents (transcripts, rubrics, scoring data)
- **Real-time Interface**: Interactive chat with loading states and error handling
- **Session Integration**: Direct integration with pitch sessions for focused analysis

## Quick Start

### Development

```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:3000)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Backend Integration

The frontend connects to the PitchScoop backend API running on port 8000. Ensure the backend is running:

```bash
# In the project root
docker compose up --build
```

## Usage

### 1. Dashboard (/)

- View recent sessions and pitch data
- Navigate to chat interface
- See available sessions with transcripts

### 2. Chat Interface (/chat)

#### Creating Conversations

- **New Chat**: General conversation about all available data
- **Analyze Session**: Focus on a specific pitch session
- **URL Parameters**: Direct links like `/chat?session=session-123&event=event-456`

#### Conversation Types

- `general_chat` - Open-ended conversation about event data
- `pitch_analysis` - Focused analysis of specific pitch sessions
- `scoring_review` - Discussion about scoring and evaluation
- `rubric_discussion` - Conversation about evaluation criteria
- `comparative_analysis` - Comparison between multiple pitches

#### Chat Features

- **Source Attribution**: AI responses show which documents were referenced
- **Message History**: Full conversation persistence and retrieval
- **Multi-Session Context**: Include multiple sessions in conversation context
- **Focus Areas**: Specify focus criteria (idea, technical, tools, presentation)
- **Real-time Responses**: Streaming responses with loading indicators

## API Integration

The frontend uses the MCP (Model Context Protocol) tools from the backend:

### Chat Tools Used
- `chat.start_conversation` - Create new conversations with context
- `chat.send_message` - Send messages and get AI responses
- `chat.get_conversation_history` - Retrieve message history
- `chat.search_documents` - Search indexed documents
- `chat.ask_about_pitch` - Session-specific Q&A
- `chat.compare_sessions` - Multi-session comparison

### Session Tools Used
- `pitches.get_session` - Get session details
- `events.list_events` - List available events

## Architecture

### Tech Stack
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom chat animations
- **State Management**: React hooks and local state
- **API Client**: Custom MCP tool execution client

### Project Structure
```
src/
├── app/
│   ├── layout.tsx          # Root layout with navigation
│   ├── page.tsx            # Dashboard homepage
│   ├── chat/
│   │   └── page.tsx        # Main chat interface
│   └── globals.css         # Global styles with chat animations
├── components/             # Reusable React components (future)
├── lib/
│   └── api.ts             # API client and MCP tool execution
└── types/
    └── chat.ts            # TypeScript interfaces for chat domain
```

### Key Components

- **ChatPageContent**: Main chat interface with conversation management
- **MessageBubble**: Individual message display with source references
- **SourceReference**: Source attribution display for AI responses

## Configuration

### Environment Variables
```bash
NODE_ENV=development|production
```

### Backend Connection
The frontend proxies API requests to the backend through Next.js rewrites:
- `/api/*` → `http://localhost:8000/*`
- `/mcp/*` → `http://localhost:8000/mcp/*`

## Multi-Tenant Support

The application supports multi-tenant architecture through:
- **Event ID**: All conversations scoped to specific events
- **User ID**: User context for conversation attribution
- **URL Parameters**: Direct event/session linking

## Example Usage

### Direct Session Analysis
```
http://localhost:3000/chat?session=session-abc-123&event=demo-event&user=judge-001
```

### General Chat
```
http://localhost:3000/chat
```

## Development Notes

- Uses React 18+ with Suspense for loading states
- Implements proper TypeScript typing throughout
- Follows Next.js 15 App Router patterns
- Responsive design with Tailwind CSS
- Error boundary handling and user feedback
- Optimized build output with static generation where possible

## Troubleshooting

### Build Issues
- Ensure Node.js 18+ is installed
- Check TypeScript configuration in `tsconfig.json`
- Verify Tailwind CSS setup in `tailwind.config.js`

### API Connection Issues
- Verify backend is running on port 8000
- Check Next.js proxy configuration in `next.config.js`
- Review browser network tab for API call failures

### Chat Not Working
- Ensure backend has indexed documents for RAG
- Check that sessions have completed transcripts
- Verify event IDs match between frontend and backend
# 🖥️ Frontend Integration Guide

## 🎯 **MCP Tools → Frontend Integration**

Your PitchScoop backend is now ready for frontend integration. Here's how to connect your UI to the automated scoring and leaderboard system.

## 🏆 **Leaderboard Integration**

### **Real-Time Leaderboard Display**
```typescript
// TypeScript interface for leaderboard data
interface LeaderboardEntry {
  rank: number;
  team_name: string;
  total_score: number;
  pitch_title: string;
  category_scores: {
    idea_score: number;
    technical_score: number;
    tool_use_score: number;
    presentation_score: number;
  };
  scoring_timestamp: string;
}

interface LeaderboardResponse {
  success: boolean;
  event_id: string;
  leaderboard: LeaderboardEntry[];
  total_teams: number;
  generated_at: string;
}
```

### **API Endpoint Examples**
```bash
# Get top 10 teams for an event
GET /api/leaderboard/{event_id}/rankings?limit=10

# Get individual team rank
GET /api/leaderboard/{event_id}/team/{session_id}/rank

# Get competition statistics
GET /api/leaderboard/{event_id}/stats
```

### **Frontend Components Needed**

#### **1. Live Leaderboard Component**
```jsx
function LiveLeaderboard({ eventId }) {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Auto-refresh every 30 seconds
  useEffect(() => {
    const fetchLeaderboard = async () => {
      const response = await fetch(`/api/leaderboard/${eventId}/rankings`);
      const data = await response.json();
      if (data.success) {
        setLeaderboard(data.leaderboard);
      }
      setLoading(false);
    };
    
    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 30000);
    return () => clearInterval(interval);
  }, [eventId]);

  return (
    <div className="leaderboard">
      <h2>🏆 Live Rankings</h2>
      {leaderboard.map((team, index) => (
        <div key={team.team_name} className="leaderboard-entry">
          <span className="rank">#{team.rank}</span>
          <span className="team">{team.team_name}</span>
          <span className="score">{team.total_score.toFixed(1)} pts</span>
        </div>
      ))}
    </div>
  );
}
```

#### **2. Team Rank Lookup Component**
```jsx
function TeamRankLookup({ eventId, sessionId }) {
  const [teamRank, setTeamRank] = useState(null);
  
  useEffect(() => {
    const fetchRank = async () => {
      const response = await fetch(`/api/leaderboard/${eventId}/team/${sessionId}/rank`);
      const data = await response.json();
      if (data.success) {
        setTeamRank(data);
      }
    };
    
    fetchRank();
  }, [eventId, sessionId]);

  if (!teamRank) return <div>Loading your rank...</div>;

  return (
    <div className="team-rank-card">
      <h3>Your Competition Results</h3>
      <div className="rank-display">
        <span className="big-rank">#{teamRank.rank}</span>
        <span className="total-teams">out of {teamRank.total_teams} teams</span>
      </div>
      <div className="score-breakdown">
        <div>Total Score: {teamRank.total_score.toFixed(1)}</div>
        <div>Idea: {teamRank.category_scores.idea_score.toFixed(1)}</div>
        <div>Technical: {teamRank.category_scores.technical_score.toFixed(1)}</div>
        <div>Tools: {teamRank.category_scores.tool_use_score.toFixed(1)}</div>
        <div>Presentation: {teamRank.category_scores.presentation_score.toFixed(1)}</div>
      </div>
    </div>
  );
}
```

## 📊 **Recording Status Integration**

### **Recording Progress Component**
```jsx
function RecordingStatus({ sessionId }) {
  const [session, setSession] = useState(null);
  const [isScoring, setIsScoring] = useState(false);

  useEffect(() => {
    const checkStatus = async () => {
      const response = await fetch(`/api/recordings/session/${sessionId}`);
      const data = await response.json();
      
      if (data.status === 'completed' && data.transcript) {
        setIsScoring(true);
        // Start checking for scoring completion
        setTimeout(checkScoringStatus, 5000);
      }
      
      setSession(data);
    };
    
    const checkScoringStatus = async () => {
      const response = await fetch(`/api/scoring/${sessionId}/status`);
      const data = await response.json();
      
      if (data.success) {
        setIsScoring(false);
        // Redirect to results page
        window.location.href = `/results/${sessionId}`;
      } else {
        // Keep checking
        setTimeout(checkScoringStatus, 5000);
      }
    };

    checkStatus();
  }, [sessionId]);

  return (
    <div className="recording-status">
      {session?.status === 'recording' && (
        <div>🔴 Recording in progress...</div>
      )}
      
      {session?.status === 'completed' && !isScoring && (
        <div>✅ Recording complete! Processing transcript...</div>
      )}
      
      {isScoring && (
        <div>🧠 AI is scoring your pitch... This may take 10-15 seconds.</div>
      )}
    </div>
  );
}
```

## 🎮 **MCP Tool Calling from Frontend**

### **Direct MCP Integration**
```typescript
// MCP tool calling service
class MCPService {
  private async callMCPTool(toolName: string, args: any) {
    const response = await fetch('/api/mcp/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tool_name: toolName,
        arguments: args
      })
    });
    return await response.json();
  }
  
  async getLeaderboard(eventId: string, limit: number = 10) {
    return await this.callMCPTool('leaderboard.get_rankings', {
      event_id: eventId,
      limit: limit
    });
  }
  
  async getTeamRank(eventId: string, sessionId: string) {
    return await this.callMCPTool('leaderboard.get_team_rank', {
      event_id: eventId,
      session_id: sessionId
    });
  }
  
  async scoreSession(sessionId: string, eventId: string) {
    return await this.callMCPTool('analysis.score_pitch', {
      session_id: sessionId,
      event_id: eventId
    });
  }
}
```

## 📱 **UI/UX Recommendations**

### **1. Competition Dashboard**
- **Live Leaderboard**: Auto-refreshing top 10
- **Team Counter**: "X teams have pitched"
- **Progress Bar**: "Y out of Z teams completed"
- **Next Up**: Queue of upcoming teams

### **2. Team Results Page**
- **Overall Rank**: Big, prominent display
- **Score Breakdown**: Category-by-category analysis
- **Feedback Display**: AI-generated insights
- **Audio Playback**: Link to recorded pitch

### **3. Real-time Updates**
- **WebSocket Integration**: Live score updates
- **Push Notifications**: "New team finished!"
- **Animated Transitions**: Smooth rank changes

## 🔄 **Event Flow Integration**

### **Competition Lifecycle**
```
1. Event Created → Show registration
2. Teams Join → Update participant count  
3. Recording Starts → Show "Live" indicator
4. Recording Ends → "Processing..." status
5. Scoring Complete → Update leaderboard
6. All Done → Final rankings display
```

### **Error State Handling**
```jsx
function ErrorBoundary({ error, eventId }) {
  if (error.type === 'scoring_failed') {
    return (
      <div className="error-state">
        <p>Scoring is taking longer than usual...</p>
        <button onClick={() => retryScoring(eventId)}>
          Try Again
        </button>
      </div>
    );
  }
  
  if (error.type === 'session_not_found') {
    return (
      <div className="error-state">
        <p>Session not found. Please check your link.</p>
      </div>
    );
  }
  
  return <div>Something went wrong. Please try again.</div>;
}
```

## 🚀 **Performance Optimizations**

### **Caching Strategy**
- **Leaderboard**: Cache for 30 seconds
- **Individual Ranks**: Cache for 5 minutes after scoring
- **Competition Stats**: Cache for 1 minute

### **Loading States**
- **Skeleton Loaders**: For leaderboard entries
- **Progress Indicators**: For scoring process
- **Real-time Feedback**: During recording

## 📊 **Analytics Integration**

Track key events:
- `recording_started`
- `recording_completed` 
- `scoring_completed`
- `leaderboard_viewed`
- `rank_checked`

---

## 🎯 **Next Frontend Steps**

1. **Create API endpoints** that call MCP tools
2. **Build leaderboard components** with real-time updates
3. **Add team results pages** with detailed breakdowns
4. **Implement WebSocket** for live updates
5. **Add error boundaries** for graceful failures

Your backend is ready - now connect the frontend for a complete experience! 🚀
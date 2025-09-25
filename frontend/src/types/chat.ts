// Chat domain types based on backend implementation

export interface SourceReference {
  document_type: string;
  document_id: string;
  session_id?: string;
  content_snippet?: string;
  relevance_score?: number;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  message_id: string;
  conversation_id: string;
  event_id: string;
  content: string;
  message_type: 'user_query' | 'ai_response' | 'system_message';
  timestamp: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  error_message?: string;
  processing_duration_ms?: number;
  sources?: SourceReference[];
  model_used?: string;
  tokens_used?: number;
  user_id?: string;
  session_context?: Record<string, any>;
}

export interface Conversation {
  conversation_id: string;
  event_id: string;
  title?: string;
  conversation_type: 'general_chat' | 'pitch_analysis' | 'scoring_review' | 'rubric_discussion' | 'comparative_analysis';
  status: 'active' | 'paused' | 'archived' | 'error';
  created_at: string;
  last_message_at?: string;
  context: ConversationContext;
  user_id?: string;
  message_count: number;
}

export interface ConversationContext {
  session_ids?: string[];
  rubric_ids?: string[];
  focus_areas?: string[];
  judge_id?: string;
  metadata?: Record<string, any>;
}

export interface StartConversationRequest {
  event_id: string;
  conversation_type?: string;
  title?: string;
  session_ids?: string[];
  rubric_ids?: string[];
  focus_areas?: string[];
  user_id?: string;
}

export interface StartConversationResponse {
  conversation_id: string;
  event_id: string;
  title?: string;
  conversation_type: string;
  status: string;
  created_at: string;
  context: ConversationContext;
  context_status: {
    has_context: boolean;
    available_document_types: string[];
    session_context_available: boolean;
    rubric_context_available: boolean;
  };
  user_id?: string;
  success: boolean;
  error?: string;
}

export interface SendMessageRequest {
  conversation_id: string;
  event_id: string;
  message: string;
  include_sources?: boolean;
  max_sources?: number;
  user_id?: string;
}

export interface SendMessageResponse {
  conversation_id: string;
  event_id: string;
  user_message: ChatMessage;
  ai_response: ChatMessage;
  processing_duration_ms: number;
  success: boolean;
  error?: string;
}

export interface ConversationHistoryRequest {
  conversation_id: string;
  event_id: string;
  include_sources?: boolean;
  message_limit?: number;
  message_offset?: number;
  message_types?: string[];
}

export interface ConversationHistoryResponse {
  conversation_id: string;
  event_id: string;
  conversation: Conversation;
  messages: ChatMessage[];
  pagination: {
    total_messages: number;
    returned_count: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
  success: boolean;
  error?: string;
}

export interface SearchDocumentsRequest {
  event_id: string;
  query: string;
  document_types?: string[];
  session_ids?: string[];
  max_results?: number;
  min_relevance_score?: number;
}

export interface SearchDocumentsResponse {
  event_id: string;
  query: string;
  results: Array<{
    document_type: string;
    content: string;
    relevance_score: number;
    metadata: Record<string, any>;
    session_id?: string;
  }>;
  total_results: number;
  search_parameters: {
    document_types?: string[];
    session_ids?: string[];
    max_results: number;
    min_relevance_score: number;
  };
  success: boolean;
  error?: string;
}

// UI state types
export interface ChatUIState {
  currentConversation: Conversation | null;
  conversations: Conversation[];
  isLoading: boolean;
  error: string | null;
  eventId: string;
  userId?: string;
}

export interface MessageUIState {
  isTyping: boolean;
  currentMessage: string;
  showSources: boolean;
  isLoadingHistory: boolean;
}

// MCP tool execution types
export interface MCPToolRequest {
  tool: string;
  arguments: Record<string, any>;
}

export interface MCPToolResponse {
  success?: boolean;
  error?: string;
  [key: string]: any;
}
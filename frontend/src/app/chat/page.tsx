'use client';

import { useEffect, useState, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiClient, formatTimestamp, formatDuration, getConversationTypeLabel, getDocumentTypeLabel, getMessageStatusColor } from '@/lib/api';
import type { ChatMessage, Conversation, SourceReference, StartConversationRequest, SendMessageRequest } from '@/types/chat';

// Wrapper component to handle Suspense for useSearchParams
function ChatPageContent() {
  const searchParams = useSearchParams();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSources, setShowSources] = useState(true);
  const [availableSessions, setAvailableSessions] = useState<any[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // URL parameters
  const sessionId = searchParams.get('session');
  const eventId = searchParams.get('event') || 'demo-event';
  const userId = searchParams.get('user') || 'demo-user';

  const loadAvailableSessions = async () => {
    try {
      const response = await apiClient.getSessions();
      setAvailableSessions(response.sessions || []);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const createConversation = useCallback(async (request: StartConversationRequest) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.startConversation(request);
      
      if (response.success) {
        const newConversation: Conversation = {
          conversation_id: response.conversation_id,
          event_id: response.event_id,
          title: response.title,
          conversation_type: response.conversation_type as any,
          status: response.status as any,
          created_at: response.created_at,
          context: response.context,
          user_id: response.user_id,
          message_count: 0
        };
        
        setCurrentConversation(newConversation);
        setConversations(prev => [newConversation, ...prev]);
        setMessages([]);
        
        // Load conversation history if it exists
        if (newConversation.message_count > 0) {
          loadConversationHistory(newConversation.conversation_id);
        }
      } else {
        setError(response.error || 'Failed to create conversation');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create conversation');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createPitchAnalysisConversation = useCallback((sessionId: string) => {
    createConversation({
      event_id: eventId,
      conversation_type: 'pitch_analysis',
      title: `Analysis of session ${sessionId.substring(0, 8)}`,
      session_ids: [sessionId],
      user_id: userId,
    });
  }, [eventId, userId, createConversation]);

  useEffect(() => {
    // Auto-focus input
    inputRef.current?.focus();
    
    // Load available sessions
    loadAvailableSessions();

    // Auto-create conversation if session specified in URL
    if (sessionId && !currentConversation) {
      createPitchAnalysisConversation(sessionId);
    }
  }, [sessionId, currentConversation, createPitchAnalysisConversation]);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversationHistory = async (conversationId: string) => {
    try {
      setIsLoadingHistory(true);
      const response = await apiClient.getConversationHistory({
        conversation_id: conversationId,
        event_id: eventId,
        include_sources: showSources,
        message_limit: 50,
      });
      
      if (response.success) {
        setMessages(response.messages);
      } else {
        setError(response.error || 'Failed to load conversation history');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const sendMessage = async () => {
    if (!currentConversation || !currentMessage.trim() || isLoading) return;

    const messageToSend = currentMessage.trim();
    setCurrentMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const request: SendMessageRequest = {
        conversation_id: currentConversation.conversation_id,
        event_id: eventId,
        message: messageToSend,
        include_sources: showSources,
        max_sources: 5,
        user_id: userId,
      };

      const response = await apiClient.sendMessage(request);
      
      if (response.success) {
        setMessages(prev => [...prev, response.user_message, response.ai_response]);
        
        // Update conversation message count
        setCurrentConversation(prev => prev ? {
          ...prev,
          message_count: prev.message_count + 2,
          last_message_at: response.ai_response.timestamp
        } : null);
      } else {
        setError(response.error || 'Failed to send message');
        // Re-add message to input if failed
        setCurrentMessage(messageToSend);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setCurrentMessage(messageToSend);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const selectConversation = (conversation: Conversation) => {
    setCurrentConversation(conversation);
    setMessages([]);
    loadConversationHistory(conversation.conversation_id);
  };

  return (
    <div className="h-full max-h-screen flex bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Sidebar */}
      <div className="w-1/3 border-r border-gray-200 flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <div className="mt-2 flex space-x-2">
            <button
              onClick={() => createConversation({
                event_id: eventId,
                conversation_type: 'general_chat',
                title: 'General Chat',
                user_id: userId,
              })}
              className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700"
              disabled={isLoading}
            >
              New Chat
            </button>
            <select 
              onChange={(e) => {
                const sessionId = e.target.value;
                if (sessionId) {
                  createPitchAnalysisConversation(sessionId);
                }
              }}
              className="text-sm border border-gray-300 rounded px-2 py-1"
              disabled={isLoading}
            >
              <option value="">Analyze Session...</option>
              {availableSessions.filter(s => s.has_transcript).map(session => (
                <option key={session.session_id} value={session.session_id}>
                  {session.team_name} - {session.pitch_title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="p-4 text-gray-500 text-sm">
              No conversations yet. Start a new chat or analyze a session.
            </div>
          ) : (
            conversations.map(conversation => (
              <div
                key={conversation.conversation_id}
                onClick={() => selectConversation(conversation)}
                className={`conversation-item p-4 border-b border-gray-100 cursor-pointer ${
                  currentConversation?.conversation_id === conversation.conversation_id
                    ? 'bg-indigo-50 border-indigo-200'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 text-sm">
                      {conversation.title}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {getConversationTypeLabel(conversation.conversation_type)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatTimestamp(conversation.created_at)}
                    </p>
                  </div>
                  <div className="text-xs text-gray-400">
                    {conversation.message_count} messages
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Settings */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={showSources}
              onChange={(e) => setShowSources(e.target.checked)}
              className="mr-2"
            />
            Show source references
          </label>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentConversation ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h1 className="text-xl font-semibold text-gray-900">
                {currentConversation.title}
              </h1>
              <div className="text-sm text-gray-500 mt-1">
                {getConversationTypeLabel(currentConversation.conversation_type)}
                {currentConversation.context.session_ids && currentConversation.context.session_ids.length > 0 && (
                  <span className="ml-2">
                    • Sessions: {currentConversation.context.session_ids.length}
                  </span>
                )}
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 messages-container">
              {isLoadingHistory ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600 text-sm">Loading conversation...</p>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>Start a conversation by asking a question!</p>
                  <div className="mt-4 text-sm">
                    <p className="font-medium">Try asking:</p>
                    <ul className="mt-2 text-left inline-block">
                      <li>• &quot;What was this pitch about?&quot;</li>
                      <li>• &quot;How did the team explain their technical approach?&quot;</li>
                      <li>• &quot;What tools did they mention?&quot;</li>
                      <li>• &quot;Compare this with other sessions&quot;</li>
                    </ul>
                  </div>
                </div>
              ) : (
                messages.map(message => (
                  <MessageBubble 
                    key={message.message_id} 
                    message={message} 
                    showSources={showSources} 
                  />
                ))
              )}
              
              {/* Loading indicator */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-xs">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      <span className="text-sm text-gray-600 loading-dots">AI is thinking</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Error Display */}
            {error && (
              <div className="px-4 py-2 bg-red-50 border-t border-red-200">
                <p className="text-red-700 text-sm">{error}</p>
                <button 
                  onClick={() => setError(null)}
                  className="text-red-600 hover:text-red-800 text-xs mt-1"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Message Input */}
            <div className="p-4 border-t border-gray-200">
              <div className="flex space-x-2">
                <textarea
                  ref={inputRef}
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about the transcripts..."
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  rows={2}
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={!currentMessage.trim() || isLoading}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    'Send'
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
          </>
        ) : (
          // No conversation selected
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <h2 className="text-xl font-medium mb-2">Welcome to PitchScoop Chat</h2>
              <p className="mb-4">Start a conversation to chat with transcripts using AI</p>
              <div className="space-y-2">
                <button
                  onClick={() => createConversation({
                    event_id: eventId,
                    conversation_type: 'general_chat',
                    title: 'General Chat',
                    user_id: userId,
                  })}
                  className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 block mx-auto"
                  disabled={isLoading}
                >
                  Start General Chat
                </button>
                {sessionId && (
                  <button
                    onClick={() => createPitchAnalysisConversation(sessionId)}
                    className="border border-indigo-600 text-indigo-600 px-6 py-2 rounded-lg hover:bg-indigo-50 block mx-auto"
                    disabled={isLoading}
                  >
                    Analyze Session {sessionId.substring(0, 8)}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Message bubble component
function MessageBubble({ message, showSources }: { message: ChatMessage; showSources: boolean }) {
  const isUser = message.message_type === 'user_query';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 message-bubble`}>
      <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
        isUser 
          ? 'bg-indigo-600 text-white' 
          : 'bg-gray-100 text-gray-900'
      }`}>
        {/* Message content */}
        <div className="whitespace-pre-wrap">{message.content}</div>
        
        {/* Message metadata */}
        <div className={`text-xs mt-2 ${isUser ? 'text-indigo-100' : 'text-gray-500'}`}>
          <span className={getMessageStatusColor(message.status)}>
            {message.status === 'processing' ? 'Processing...' : formatTimestamp(message.timestamp)}
          </span>
          {message.processing_duration_ms && (
            <span className="ml-2">
              • {formatDuration(message.processing_duration_ms)}
            </span>
          )}
        </div>
        
        {/* Source references */}
        {!isUser && showSources && message.sources && message.sources.length > 0 && (
          <div className="mt-3 space-y-2">
            <div className="text-xs font-medium text-gray-600">Sources:</div>
            {message.sources.map((source, index) => (
              <SourceReference key={index} source={source} />
            ))}
          </div>
        )}
        
        {/* Error message */}
        {message.status === 'error' && message.error_message && (
          <div className="mt-2 text-red-600 text-sm">
            Error: {message.error_message}
          </div>
        )}
      </div>
    </div>
  );
}

// Source reference component
function SourceReference({ source }: { source: SourceReference }) {
  return (
    <div className="source-reference bg-white border border-gray-200 rounded p-2 text-xs">
      <div className="flex justify-between items-center">
        <span className="font-medium text-gray-700">
          {getDocumentTypeLabel(source.document_type)}
        </span>
        {source.relevance_score && (
          <span className="text-gray-500">
            {Math.round(source.relevance_score * 100)}% relevant
          </span>
        )}
      </div>
      {source.session_id && (
        <div className="text-gray-500 mt-1">
          Session: {source.session_id.substring(0, 8)}
        </div>
      )}
      {source.content_snippet && (
        <div className="text-gray-600 mt-1 italic">
          &quot;{source.content_snippet.length > 100 
            ? source.content_snippet.substring(0, 100) + '...' 
            : source.content_snippet}&quot;
        </div>
      )}
    </div>
  );
}

// Main export with Suspense wrapper
export default function ChatPage() {
  return (
    <div className="chat-container">
      <Suspense fallback={
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-2">Loading chat interface...</span>
        </div>
      }>
        <ChatPageContent />
      </Suspense>
    </div>
  );
}
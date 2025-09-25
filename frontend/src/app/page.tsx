'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient, formatTimestamp } from '@/lib/api';

interface Session {
  session_id: string;
  event_id: string;
  team_name: string;
  pitch_title: string;
  status: string;
  created_at: string;
  has_audio: boolean;
  has_transcript: boolean;
}

export default function HomePage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.getSessions();
        setSessions(response.sessions || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load sessions');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, []);

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome to PitchScoop
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            AI-powered pitch analysis and transcript exploration platform
          </p>
          <div className="flex justify-center space-x-4">
            <Link
              href="/chat"
              className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
            >
              Start Chatting with Transcripts
            </Link>
            <button className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition-colors">
              View Documentation
            </button>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="text-indigo-600 mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">RAG-Powered Chat</h3>
          <p className="text-gray-600">
            Chat with pitch transcripts using advanced RAG technology for context-aware responses.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="text-indigo-600 mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Analysis</h3>
          <p className="text-gray-600">
            Get detailed insights and scoring for pitch presentations with AI-powered analysis.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="text-indigo-600 mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Source Attribution</h3>
          <p className="text-gray-600">
            Every AI response includes clear references to the source documents and transcripts.
          </p>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Sessions</h2>
        
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading sessions...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-600">
            <p>Error loading sessions: {error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-2 text-indigo-600 hover:text-indigo-800"
            >
              Try again
            </button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No sessions found. Start recording to see sessions here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Team & Pitch
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sessions.slice(0, 5).map((session) => (
                  <tr key={session.session_id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {session.team_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {session.pitch_title}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        session.status === 'completed' 
                          ? 'bg-green-100 text-green-800'
                          : session.status === 'processing'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {session.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatTimestamp(session.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {session.has_transcript && (
                        <Link
                          href={`/chat?session=${session.session_id}&event=${session.event_id}`}
                          className="text-indigo-600 hover:text-indigo-900 mr-4"
                        >
                          Chat with Transcript
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {sessions.length > 5 && (
          <div className="text-center mt-4">
            <button className="text-indigo-600 hover:text-indigo-800 font-medium">
              View all sessions →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
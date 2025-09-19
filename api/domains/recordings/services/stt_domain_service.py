import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities.stt_session import STTSession, SessionStatus
from ..value_objects.session_id import SessionId
from ..value_objects.audio_configuration import AudioConfiguration
from ..value_objects.transcript import TranscriptSegment
from ..repositories.stt_session_repository import STTSessionRepository
from ..repositories.gladia_api_repository import GladiaAPIRepository, GladiaWebSocketConnection


class STTDomainService:
    """Domain service for Speech-to-Text operations."""
    
    def __init__(
        self,
        session_repository: STTSessionRepository,
        gladia_api_repository: GladiaAPIRepository
    ):
        self.session_repository = session_repository
        self.gladia_api_repository = gladia_api_repository
        self._websocket_connections: Dict[str, GladiaWebSocketConnection] = {}
        self._message_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_session(
        self,
        audio_config: AudioConfiguration,
        session_name: Optional[str] = None
    ) -> STTSession:
        """Create a new STT session."""
        # Create domain session
        session = STTSession.create_new(audio_config, session_name)
        
        # Save to repository
        await self.session_repository.save(session)
        
        return session
    
    async def start_session(self, session_id: SessionId) -> bool:
        """Start an STT session by connecting to Gladia."""
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status != SessionStatus.INITIALIZING:
            raise ValueError(f"Session {session_id} is not in initializing state")
        
        try:
            # Create Gladia session
            gladia_response = await self.gladia_api_repository.create_session(session.audio_config)
            
            # Update session with Gladia details
            session.set_gladia_connection(
                gladia_response['id'],
                gladia_response['url']
            )
            
            # Connect to WebSocket
            ws_connection = await self.gladia_api_repository.connect_websocket(
                session.gladia_websocket_url
            )
            self._websocket_connections[str(session_id)] = ws_connection
            
            # Start message handling
            self._message_tasks[str(session_id)] = asyncio.create_task(
                self._handle_websocket_messages(session, ws_connection)
            )
            
            # Update session status
            session.change_status(SessionStatus.CONNECTED)
            await self.session_repository.save(session)
            
            return True
            
        except Exception as e:
            session.set_error(f"Failed to start session: {str(e)}")
            await self.session_repository.save(session)
            raise
    
    async def send_audio(self, session_id: SessionId, audio_data: bytes) -> None:
        """Send audio data to a session."""
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.can_receive_audio:
            raise ValueError(f"Session {session_id} cannot receive audio in state {session.status}")
        
        # Get WebSocket connection
        ws_connection = self._websocket_connections.get(str(session_id))
        if not ws_connection or not ws_connection.is_connected():
            raise ValueError(f"No active WebSocket connection for session {session_id}")
        
        # Start recording if connected
        if session.status == SessionStatus.CONNECTED:
            session.start_recording()
            await self.session_repository.save(session)
        
        # Send audio data
        await ws_connection.send_audio(audio_data)
    
    async def stop_session(self, session_id: SessionId) -> None:
        """Stop an STT session."""
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.is_active:
            return  # Already stopped
        
        try:
            # Stop recording
            session.stop_recording()
            await self.session_repository.save(session)
            
            # Send stop message to Gladia
            ws_connection = self._websocket_connections.get(str(session_id))
            if ws_connection and ws_connection.is_connected():
                await ws_connection.send_stop_recording()
            
            # Clean up resources
            await self._cleanup_session_resources(session_id)
            
        except Exception as e:
            session.set_error(f"Error stopping session: {str(e)}")
            await self.session_repository.save(session)
            raise
    
    async def get_session_results(self, session_id: SessionId) -> Optional[Dict[str, Any]]:
        """Get final results for a completed session."""
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            return None
        
        if session.status != SessionStatus.STOPPED:
            return None
        
        if not session.gladia_session_id:
            return None
        
        return await self.gladia_api_repository.get_session_results(session.gladia_session_id)
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_sessions = await self.session_repository.get_sessions_created_before(cutoff_time)
        
        cleanup_count = 0
        for session in old_sessions:
            try:
                if session.is_active:
                    await self.stop_session(session.session_id)
                
                await self.session_repository.delete(session.session_id)
                cleanup_count += 1
                
            except Exception as e:
                # Log error but continue with other sessions
                print(f"Error cleaning up session {session.session_id}: {e}")
        
        return cleanup_count
    
    async def stop_all_active_sessions(self) -> int:
        """Stop all active sessions."""
        active_sessions = await self.session_repository.get_all_active()
        
        stop_count = 0
        for session in active_sessions:
            try:
                await self.stop_session(session.session_id)
                stop_count += 1
            except Exception as e:
                print(f"Error stopping session {session.session_id}: {e}")
        
        return stop_count
    
    async def _handle_websocket_messages(
        self,
        session: STTSession,
        ws_connection: GladiaWebSocketConnection
    ) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for message in ws_connection.receive_messages():
                await self._process_gladia_message(session, message)
                
        except Exception as e:
            session.set_error(f"WebSocket error: {str(e)}")
            await self.session_repository.save(session)
        finally:
            # Clean up when message handling ends
            await self._cleanup_session_resources(session.session_id)
    
    async def _process_gladia_message(self, session: STTSession, message: Dict[str, Any]) -> None:
        """Process a message from Gladia WebSocket."""
        message_type = message.get('type')
        
        if message_type == 'transcript':
            # Parse transcript segment
            transcript_segment = TranscriptSegment.from_gladia_message(message)
            if transcript_segment:
                session.add_transcript(transcript_segment)
                await self.session_repository.save(session)
                
        elif message_type == 'error':
            error_msg = message.get('data', {}).get('message', 'Unknown Gladia error')
            session.set_error(error_msg)
            await self.session_repository.save(session)
            
        elif message_type == 'session_ends':
            session.mark_as_stopped()
            await self.session_repository.save(session)
    
    async def _cleanup_session_resources(self, session_id: SessionId) -> None:
        """Clean up WebSocket connections and tasks for a session."""
        session_id_str = str(session_id)
        
        # Cancel message handling task
        if session_id_str in self._message_tasks:
            task = self._message_tasks.pop(session_id_str)
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close WebSocket connection
        if session_id_str in self._websocket_connections:
            ws_connection = self._websocket_connections.pop(session_id_str)
            await ws_connection.close()
    
    async def get_session_count(self) -> int:
        """Get count of active sessions."""
        return await self.session_repository.count_active_sessions()
    
    async def get_all_session_statuses(self) -> Dict[str, str]:
        """Get status of all sessions."""
        return await self.session_repository.get_session_statuses()
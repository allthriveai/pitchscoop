"""
MinIO client for audio file storage and retrieval.
"""
import os
import asyncio
from typing import Optional, BinaryIO
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error


class MinIOAudioStorage:
    """MinIO client for storing and retrieving audio files."""
    
    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket_name: str = None,
        secure: bool = False
    ):
        """Initialize MinIO client with configuration."""
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "pitchscoop")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "pitchscoop123")
        self.bucket_name = bucket_name or os.getenv("MINIO_BUCKET_NAME", "pitchscoop")
        
        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    async def upload_audio(
        self, 
        session_id: str, 
        audio_data: bytes, 
        file_format: str = "wav"
    ) -> str:
        """
        Upload audio data to MinIO.
        
        Args:
            session_id: Unique session identifier
            audio_data: Raw audio bytes
            file_format: Audio format (wav, mp3, etc.)
            
        Returns:
            MinIO object key for the uploaded file
        """
        try:
            # Create object key
            object_key = f"sessions/{session_id}/recording.{file_format}"
            
            # Convert bytes to BytesIO stream
            audio_stream = BytesIO(audio_data)
            
            # Upload to MinIO
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.put_object,
                self.bucket_name,
                object_key,
                audio_stream,
                len(audio_data),
                f"audio/{file_format}"
            )
            
            print(f"Uploaded audio to MinIO: {object_key} ({len(audio_data)} bytes)")
            return object_key
            
        except S3Error as e:
            print(f"Error uploading audio to MinIO: {e}")
            raise
    
    async def get_playback_url(
        self, 
        session_id: str, 
        file_format: str = "wav",
        expires: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """
        Generate presigned URL for audio playback.
        
        Args:
            session_id: Session identifier
            file_format: Audio format
            expires: URL expiration time
            
        Returns:
            Presigned URL for audio playback or None if file doesn't exist
        """
        try:
            object_key = f"sessions/{session_id}/recording.{file_format}"
            
            # Check if object exists
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.client.stat_object,
                    self.bucket_name,
                    object_key
                )
            except S3Error as e:
                if e.code == "NoSuchKey":
                    return None
                raise
            
            # Generate presigned URL
            playback_url = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.presigned_get_object,
                self.bucket_name,
                object_key,
                expires
            )
            
            return playback_url
            
        except S3Error as e:
            print(f"Error generating playback URL: {e}")
            return None
    
    async def get_direct_url(self, session_id: str, file_format: str = "wav") -> str:
        """
        Get direct URL for audio file (for internal use).
        
        Args:
            session_id: Session identifier
            file_format: Audio format
            
        Returns:
            Direct MinIO URL
        """
        object_key = f"sessions/{session_id}/recording.{file_format}"
        return f"http://{self.endpoint}/{self.bucket_name}/{object_key}"
    
    async def delete_audio(self, session_id: str, file_format: str = "wav") -> bool:
        """
        Delete audio file from MinIO.
        
        Args:
            session_id: Session identifier
            file_format: Audio format
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            object_key = f"sessions/{session_id}/recording.{file_format}"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.remove_object,
                self.bucket_name,
                object_key
            )
            
            print(f"Deleted audio from MinIO: {object_key}")
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return True  # Already deleted
            print(f"Error deleting audio from MinIO: {e}")
            return False
    
    async def get_audio_info(self, session_id: str, file_format: str = "wav") -> Optional[dict]:
        """
        Get audio file information.
        
        Args:
            session_id: Session identifier
            file_format: Audio format
            
        Returns:
            Dictionary with file info or None if file doesn't exist
        """
        try:
            object_key = f"sessions/{session_id}/recording.{file_format}"
            
            stat = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.stat_object,
                self.bucket_name,
                object_key
            )
            
            return {
                "object_key": object_key,
                "size": stat.size,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "content_type": stat.content_type,
                "etag": stat.etag
            }
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            print(f"Error getting audio info: {e}")
            return None
    
    async def list_session_audio_files(self, session_id: str) -> list:
        """
        List all audio files for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of object keys for the session
        """
        try:
            prefix = f"sessions/{session_id}/"
            
            objects = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self.client.list_objects(self.bucket_name, prefix=prefix))
            )
            
            return [obj.object_name for obj in objects]
            
        except S3Error as e:
            print(f"Error listing audio files: {e}")
            return []
    
    async def upload_compressed_audio(
        self, 
        session_id: str, 
        compressed_data: bytes,
        original_format: str = "wav"
    ) -> str:
        """
        Upload compressed version of audio for web playback.
        
        Args:
            session_id: Session identifier
            compressed_data: Compressed audio bytes (e.g., MP3)
            original_format: Original format for reference
            
        Returns:
            MinIO object key for compressed file
        """
        try:
            # Store compressed version alongside original
            object_key = f"sessions/{session_id}/compressed.mp3"
            
            audio_stream = BytesIO(compressed_data)
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.put_object,
                self.bucket_name,
                object_key,
                audio_stream,
                len(compressed_data),
                "audio/mp3"
            )
            
            print(f"Uploaded compressed audio: {object_key}")
            return object_key
            
        except S3Error as e:
            print(f"Error uploading compressed audio: {e}")
            raise


# Global instance for dependency injection
minio_audio_storage = MinIOAudioStorage()
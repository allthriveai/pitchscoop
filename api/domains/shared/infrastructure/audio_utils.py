import base64
import json
from typing import List, Dict, Any, Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for processing audio data for Gladia STT."""
    
    @staticmethod
    def interleave_audio(channels_data: List[bytes], bit_depth: int = 16) -> bytes:
        """
        Merge multiple audio tracks into a single multi-channel stream.
        
        Args:
            channels_data: List of audio buffers, one per channel
            bit_depth: Bit depth of the audio (8, 16, 24, or 32)
            
        Returns:
            Interleaved multi-channel audio buffer
        """
        if not channels_data:
            raise ValueError("No audio channels provided")
            
        nb_channels = len(channels_data)
        if nb_channels == 1:
            return channels_data[0]
        
        bytes_per_sample = bit_depth // 8
        samples_per_channel = len(channels_data[0]) // bytes_per_sample
        
        # Verify all channels have the same length
        for i, channel in enumerate(channels_data):
            if len(channel) // bytes_per_sample != samples_per_channel:
                raise ValueError(f"Channel {i} has different length than channel 0")
        
        # Create interleaved audio buffer
        audio = bytearray(nb_channels * samples_per_channel * bytes_per_sample)
        
        for i in range(samples_per_channel):
            for j in range(nb_channels):
                sample_start = i * bytes_per_sample
                sample_end = (i + 1) * bytes_per_sample
                sample = channels_data[j][sample_start:sample_end]
                
                dest_start = (i * nb_channels + j) * bytes_per_sample
                dest_end = dest_start + bytes_per_sample
                audio[dest_start:dest_end] = sample
        
        return bytes(audio)
    
    @staticmethod
    def create_audio_chunk_message(audio_data: bytes, as_base64: bool = True) -> str:
        """
        Create a JSON message containing audio chunk data.
        
        Args:
            audio_data: Raw audio bytes
            as_base64: Whether to encode as base64 (True) or send as binary (False)
            
        Returns:
            JSON string message for sending to Gladia
        """
        if as_base64:
            encoded_data = base64.b64encode(audio_data).decode('utf-8')
            message = {
                "type": "audio_chunk",
                "data": {
                    "chunk": encoded_data
                }
            }
            return json.dumps(message)
        else:
            # For binary transmission, return the raw bytes
            return audio_data
    
    @staticmethod
    def create_stop_recording_message() -> str:
        """Create a stop recording message for Gladia."""
        message = {
            "type": "stop_recording"
        }
        return json.dumps(message)
    
    @staticmethod
    def validate_audio_config(config: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate audio configuration parameters.
        
        Args:
            config: Audio configuration dictionary
            
        Returns:
            Validated configuration with error messages if any
        """
        errors = {}
        
        # Validate encoding
        valid_encodings = ['wav/pcm', 'mp3', 'flac', 'ogg', 'webm']
        if 'encoding' in config and config['encoding'] not in valid_encodings:
            errors['encoding'] = f"Invalid encoding. Must be one of: {valid_encodings}"
        
        # Validate sample rate
        valid_sample_rates = [8000, 16000, 22050, 44100, 48000]
        if 'sample_rate' in config and config['sample_rate'] not in valid_sample_rates:
            errors['sample_rate'] = f"Invalid sample rate. Must be one of: {valid_sample_rates}"
        
        # Validate bit depth
        valid_bit_depths = [8, 16, 24, 32]
        if 'bit_depth' in config and config['bit_depth'] not in valid_bit_depths:
            errors['bit_depth'] = f"Invalid bit depth. Must be one of: {valid_bit_depths}"
        
        # Validate channels
        if 'channels' in config and (config['channels'] < 1 or config['channels'] > 8):
            errors['channels'] = "Channels must be between 1 and 8"
        
        return errors
    
    @staticmethod
    def calculate_audio_duration(audio_size: int, sample_rate: int, bit_depth: int, channels: int) -> float:
        """
        Calculate audio duration from size and parameters.
        
        Args:
            audio_size: Size of audio data in bytes
            sample_rate: Sample rate in Hz
            bit_depth: Bit depth (8, 16, 24, 32)
            channels: Number of audio channels
            
        Returns:
            Duration in seconds
        """
        bytes_per_sample = bit_depth // 8
        total_samples = audio_size // (bytes_per_sample * channels)
        return total_samples / sample_rate
    
    @staticmethod
    def chunk_audio_data(audio_data: bytes, chunk_size: int = 8192) -> List[bytes]:
        """
        Split audio data into chunks for streaming.
        
        Args:
            audio_data: Complete audio data
            chunk_size: Size of each chunk in bytes
            
        Returns:
            List of audio chunks
        """
        chunks = []
        for i in range(0, len(audio_data), chunk_size):
            chunks.append(audio_data[i:i + chunk_size])
        return chunks


def parse_gladia_message(message_data: str) -> Optional[Dict[str, Any]]:
    """
    Parse a message received from Gladia WebSocket.
    
    Args:
        message_data: Raw message data from WebSocket
        
    Returns:
        Parsed message dictionary or None if parsing fails
    """
    try:
        message = json.loads(message_data)
        return message
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gladia message: {e}")
        return None


def extract_transcript_text(message: Dict[str, Any]) -> Optional[str]:
    """
    Extract transcript text from a Gladia message.
    
    Args:
        message: Parsed Gladia message
        
    Returns:
        Transcript text if available, None otherwise
    """
    try:
        if (message.get('type') == 'transcript' and 
            message.get('data', {}).get('is_final') and
            'utterance' in message.get('data', {})):
            return message['data']['utterance']['text']
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to extract transcript text: {e}")
    
    return None


def get_speaker_channel(message: Dict[str, Any]) -> Optional[int]:
    """
    Get speaker channel from a Gladia message.
    
    Args:
        message: Parsed Gladia message
        
    Returns:
        Channel number if available, None otherwise
    """
    try:
        if (message.get('type') == 'transcript' and
            'utterance' in message.get('data', {})):
            return message['data']['utterance'].get('channel')
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to extract speaker channel: {e}")
    
    return None
from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class AudioEncoding(Enum):
    """Supported audio encodings."""
    WAV_PCM = "wav/pcm"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    WEBM = "webm"


class SampleRate(Enum):
    """Supported sample rates."""
    RATE_8000 = 8000
    RATE_16000 = 16000
    RATE_22050 = 22050
    RATE_44100 = 44100
    RATE_48000 = 48000


class BitDepth(Enum):
    """Supported bit depths."""
    DEPTH_8 = 8
    DEPTH_16 = 16
    DEPTH_24 = 24
    DEPTH_32 = 32


@dataclass(frozen=True)
class AudioConfiguration:
    """Value object representing audio configuration for STT with Audio Intelligence features."""
    
    encoding: AudioEncoding
    sample_rate: SampleRate
    bit_depth: BitDepth
    channels: int
    
    # Gladia Audio Intelligence Features
    sentiment_analysis: bool = False
    emotion_analysis: bool = False
    speaker_identification: bool = False
    summarization: bool = False
    named_entity_recognition: bool = False
    chapterization: bool = False
    translation: bool = False
    target_language: str = None
    
    def __post_init__(self):
        """Validate audio configuration."""
        if self.channels < 1 or self.channels > 8:
            raise ValueError("Channels must be between 1 and 8")
    
    @property
    def bytes_per_sample(self) -> int:
        """Calculate bytes per sample."""
        return self.bit_depth.value // 8
    
    @property
    def is_multichannel(self) -> bool:
        """Check if configuration is multichannel."""
        return self.channels > 1
    
    def to_gladia_config(self, include_ai_features: bool = False) -> Dict[str, Any]:
        """Convert to Gladia API configuration format.
        
        Args:
            include_ai_features: Whether to include Audio Intelligence features.
                                Set to True for batch API, False for live streaming API.
        """
        config = {
            "encoding": self.encoding.value,
            "sample_rate": self.sample_rate.value,
            "bit_depth": self.bit_depth.value,
            "channels": self.channels
        }
        
        # Only add Audio Intelligence features if explicitly requested (batch API)
        if include_ai_features:
            if self.sentiment_analysis:
                config["sentiment_analysis"] = True
                
            if self.emotion_analysis:
                config["emotion_analysis"] = True
                
            if self.speaker_identification:
                config["speaker_identification"] = True
                
            if self.summarization:
                config["summarization"] = True
                
            if self.named_entity_recognition:
                config["named_entity_recognition"] = True
                
            if self.chapterization:
                config["chapterization"] = True
                
            if self.translation and self.target_language:
                config["translation"] = True
                config["target_language"] = self.target_language
        
        return config
    
    def calculate_duration(self, audio_size_bytes: int) -> float:
        """Calculate audio duration from byte size."""
        total_samples = audio_size_bytes // (self.bytes_per_sample * self.channels)
        return total_samples / self.sample_rate.value
    
    @classmethod
    def create_default(cls) -> 'AudioConfiguration':
        """Create default audio configuration."""
        return cls(
            encoding=AudioEncoding.WAV_PCM,
            sample_rate=SampleRate.RATE_16000,
            bit_depth=BitDepth.DEPTH_16,
            channels=1
        )
    
    @classmethod
    def create_pitch_analysis(cls) -> 'AudioConfiguration':
        """Create configuration optimized for pitch analysis with Audio Intelligence."""
        return cls(
            encoding=AudioEncoding.WAV_PCM,
            sample_rate=SampleRate.RATE_16000,
            bit_depth=BitDepth.DEPTH_16,
            channels=1,
            sentiment_analysis=True,
            emotion_analysis=True,
            summarization=True,
            named_entity_recognition=True,
            chapterization=True
        )
    
    @classmethod
    def create_full_intelligence(cls) -> 'AudioConfiguration':
        """Create configuration with all Audio Intelligence features enabled."""
        return cls(
            encoding=AudioEncoding.WAV_PCM,
            sample_rate=SampleRate.RATE_16000,
            bit_depth=BitDepth.DEPTH_16,
            channels=1,
            sentiment_analysis=True,
            emotion_analysis=True,
            speaker_identification=True,
            summarization=True,
            named_entity_recognition=True,
            chapterization=True
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioConfiguration':
        """Create from dictionary with Audio Intelligence features."""
        return cls(
            encoding=AudioEncoding(data.get('encoding', 'wav/pcm')),
            sample_rate=SampleRate(data.get('sample_rate', 16000)),
            bit_depth=BitDepth(data.get('bit_depth', 16)),
            channels=data.get('channels', 1),
            sentiment_analysis=data.get('sentiment_analysis', False),
            emotion_analysis=data.get('emotion_analysis', False),
            speaker_identification=data.get('speaker_identification', False),
            summarization=data.get('summarization', False),
            named_entity_recognition=data.get('named_entity_recognition', False),
            chapterization=data.get('chapterization', False),
            translation=data.get('translation', False),
            target_language=data.get('target_language', None)
        )

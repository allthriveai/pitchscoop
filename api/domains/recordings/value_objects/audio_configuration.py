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
    """Value object representing audio configuration for STT."""
    
    encoding: AudioEncoding
    sample_rate: SampleRate
    bit_depth: BitDepth
    channels: int
    
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
    
    def to_gladia_config(self) -> Dict[str, Any]:
        """Convert to Gladia API configuration format."""
        return {
            "encoding": self.encoding.value,
            "sample_rate": self.sample_rate.value,
            "bit_depth": self.bit_depth.value,
            "channels": self.channels
        }
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioConfiguration':
        """Create from dictionary."""
        return cls(
            encoding=AudioEncoding(data.get('encoding', 'wav/pcm')),
            sample_rate=SampleRate(data.get('sample_rate', 16000)),
            bit_depth=BitDepth(data.get('bit_depth', 16)),
            channels=data.get('channels', 1)
        )
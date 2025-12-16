"""Audio file loading using soundfile with streaming support."""

from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf


@dataclass(frozen=True, slots=True)
class AudioChunk:
    """A chunk of audio data with metadata."""
    samples: np.ndarray
    sample_rate: int
    channels: int
    is_last: bool


@dataclass(frozen=True, slots=True)
class AudioInfo:
    """Audio file metadata."""
    sample_rate: int
    channels: int
    frames: int
    duration: float


def audio_info(filepath: str | Path) -> AudioInfo:
    """
    Audio file metadata without loading the entire file.
    
    Args:
        filepath: Path to the audio file.
        
    Returns:
        AudioInfo with sample_rate, channels, frames, and duration.
    """
    with sf.SoundFile(filepath) as f:
        return AudioInfo(
            sample_rate=f.samplerate,
            channels=f.channels,
            frames=f.frames,
            duration=f.frames / f.samplerate,
        )


def stream_audio(
    filepath: str | Path,
    chunk_size: int = 4096,
) -> Generator[AudioChunk, None, None]:
    """
    Stream audio file in chunks for memory-efficient processing.
    
    Args:
        filepath: Path to the audio file.
        chunk_size: Number of frames per chunk (default: 4096).
        
    Yields:
        AudioChunk containing samples, sample_rate, channels, and is_last flag.
        For stereo files, samples shape is (chunk_size, channels).
    """
    with sf.SoundFile(filepath) as f:
        sample_rate = f.samplerate
        channels = f.channels
        
        while True:
            chunk = f.read(chunk_size, dtype='float64')
            
            if len(chunk) == 0:
                break
            
            is_last = len(chunk) < chunk_size or f.tell() >= f.frames
            
            yield AudioChunk(
                samples=chunk,
                sample_rate=sample_rate,
                channels=channels,
                is_last=is_last,
            )

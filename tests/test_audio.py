"""Tests for audio loading."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audioviz.audio import AudioChunk, AudioInfo, audio_info, stream_audio


@pytest.fixture
def sample_wav_file(
    tmp_path: Path,
    sample_rate: int,
    duration_sec: float,
    frequency_hz: int,
) -> Path:
    """Create a simple test WAV file."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
    samples = np.sin(2 * np.pi * frequency_hz * t)
    
    filepath = tmp_path / "test.wav"
    sf.write(filepath, samples, sample_rate)
    return filepath


@pytest.fixture
def stereo_wav_file(
    tmp_path: Path,
    sample_rate: int,
    duration_sec: float,
    frequency_hz: int,
) -> Path:
    """Create a stereo test WAV file."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
    left = np.sin(2 * np.pi * frequency_hz * t)
    right = np.sin(2 * np.pi * frequency_hz * 2 * t)  # Octave higher
    stereo = np.column_stack([left, right])
    
    filepath = tmp_path / "stereo.wav"
    sf.write(filepath, stereo, sample_rate)
    return filepath


def test_audio_info(
    sample_wav_file: Path,
    sample_rate: int,
    duration_sec: float,
) -> None:
    """Test that audio_info returns correct metadata."""
    info = audio_info(sample_wav_file)
    expected_frames = int(sample_rate * duration_sec)
    
    assert isinstance(info, AudioInfo)
    assert info.sample_rate == sample_rate
    assert info.channels == 1
    assert info.frames == expected_frames
    assert abs(info.duration - duration_sec) < 0.001


def test_stream_audio_yields_chunks(
    sample_wav_file: Path,
    chunk_size: int,
) -> None:
    """Test that stream_audio yields AudioChunk objects."""
    chunks = list(stream_audio(sample_wav_file, chunk_size=chunk_size))
    
    assert len(chunks) > 0
    assert all(isinstance(c, AudioChunk) for c in chunks)
    assert chunks[-1].is_last is True


def test_stream_audio_chunk_sizes(
    sample_wav_file: Path,
    chunk_size: int,
) -> None:
    """Test that chunks have correct sizes."""
    chunks = list(stream_audio(sample_wav_file, chunk_size=chunk_size))
    
    # All chunks except last should be full size
    for chunk in chunks[:-1]:
        assert len(chunk.samples) == chunk_size
    
    # Last chunk can be smaller
    assert len(chunks[-1].samples) <= chunk_size


def test_stream_audio_stereo_preserves_channels(
    stereo_wav_file: Path,
    stereo_channels: int,
) -> None:
    """Test that stereo files preserve both channels when streaming."""
    chunks = list(stream_audio(stereo_wav_file))
    
    for chunk in chunks:
        assert chunk.samples.ndim == stereo_channels
        assert chunk.samples.shape[1] == stereo_channels
        assert chunk.channels == stereo_channels

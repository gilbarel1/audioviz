"""Tests for audio loading."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audioviz.audio import AudioChunk, AudioInfo, audio_info, stream_audio

# Test parameters
SAMPLE_RATE = 44100
DURATION_SEC = 0.5
FREQUENCY_HZ = 440
CHUNK_SIZE = 4096


@pytest.fixture
def sample_wav_file(tmp_path: Path) -> Path:
    """Create a simple test WAV file."""
    t = np.linspace(0, DURATION_SEC, int(SAMPLE_RATE * DURATION_SEC))
    samples = np.sin(2 * np.pi * FREQUENCY_HZ * t)
    
    filepath = tmp_path / "test.wav"
    sf.write(filepath, samples, SAMPLE_RATE)
    return filepath


@pytest.fixture
def stereo_wav_file(tmp_path: Path) -> Path:
    """Create a stereo test WAV file."""
    t = np.linspace(0, DURATION_SEC, int(SAMPLE_RATE * DURATION_SEC))
    left = np.sin(2 * np.pi * FREQUENCY_HZ * t)
    right = np.sin(2 * np.pi * FREQUENCY_HZ * 2 * t)  # Octave higher
    stereo = np.column_stack([left, right])
    
    filepath = tmp_path / "stereo.wav"
    sf.write(filepath, stereo, SAMPLE_RATE)
    return filepath


def test_audio_info(sample_wav_file: Path) -> None:
    """Test that audio_info returns correct metadata."""
    info = audio_info(sample_wav_file)
    expected_frames = int(SAMPLE_RATE * DURATION_SEC)
    
    assert isinstance(info, AudioInfo)
    assert info.sample_rate == SAMPLE_RATE
    assert info.channels == 1
    assert info.frames == expected_frames
    assert abs(info.duration - DURATION_SEC) < 0.001


def test_stream_audio_yields_chunks(sample_wav_file: Path) -> None:
    """Test that stream_audio yields AudioChunk objects."""
    chunks = list(stream_audio(sample_wav_file, chunk_size=CHUNK_SIZE))
    
    assert len(chunks) > 0
    assert all(isinstance(c, AudioChunk) for c in chunks)
    assert chunks[-1].is_last is True


def test_stream_audio_chunk_sizes(sample_wav_file: Path) -> None:
    """Test that chunks have correct sizes."""
    chunks = list(stream_audio(sample_wav_file, chunk_size=CHUNK_SIZE))
    
    # All chunks except last should be full size
    for chunk in chunks[:-1]:
        assert len(chunk.samples) == CHUNK_SIZE
    
    # Last chunk can be smaller
    assert len(chunks[-1].samples) <= CHUNK_SIZE

def test_stream_audio_stereo_preserves_channels(stereo_wav_file: Path) -> None:
    """Test that stereo files preserve both channels when streaming."""
    chunks = list(stream_audio(stereo_wav_file))
    
    for chunk in chunks:
        assert chunk.samples.ndim == 2
        assert chunk.samples.shape[1] == 2
        assert chunk.channels == 2

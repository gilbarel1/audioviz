"""Tests for audio loading."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audioviz.audio import AudioChunk, AudioInfo, audio_info, load_audio, stream_audio


@pytest.fixture
def sample_wav_file(tmp_path: Path) -> Path:
    """Create a simple test WAV file."""
    sample_rate = 44100
    duration = 0.5  # seconds
    frequency = 440  # Hz (A4 note)
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    samples = np.sin(2 * np.pi * frequency * t)
    
    filepath = tmp_path / "test.wav"
    sf.write(filepath, samples, sample_rate)
    return filepath


@pytest.fixture
def stereo_wav_file(tmp_path: Path) -> Path:
    """Create a stereo test WAV file."""
    sample_rate = 44100
    duration = 0.5
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    left = np.sin(2 * np.pi * frequency * t)
    right = np.sin(2 * np.pi * frequency * 2 * t)  # Octave higher
    stereo = np.column_stack([left, right])
    
    filepath = tmp_path / "stereo.wav"
    sf.write(filepath, stereo, sample_rate)
    return filepath


def test_load_audio_returns_samples_and_rate(sample_wav_file: Path) -> None:
    """Test that load_audio returns samples and sample rate."""
    samples, sample_rate = load_audio(sample_wav_file)
    
    assert isinstance(samples, np.ndarray)
    assert isinstance(sample_rate, int)
    assert sample_rate == 44100


def test_load_audio_mono_output(sample_wav_file: Path) -> None:
    """Test that load_audio returns correct shape for mono file."""
    samples, _ = load_audio(sample_wav_file)
    
    assert samples.ndim == 1


def test_load_audio_stereo_output(stereo_wav_file: Path) -> None:
    """Test that load_audio preserves stereo channels."""
    samples, _ = load_audio(stereo_wav_file)
    
    assert samples.ndim == 2
    assert samples.shape[1] == 2


def test_load_audio_nonexistent_file() -> None:
    """Test that load_audio raises error for missing file."""
    with pytest.raises(Exception):
        load_audio("nonexistent.wav")


# --- Streaming tests ---

def test_audio_info(sample_wav_file: Path) -> None:
    """Test that audio_info returns correct metadata."""
    info = audio_info(sample_wav_file)
    
    assert isinstance(info, AudioInfo)
    assert info.sample_rate == 44100
    assert info.channels == 1
    assert info.frames == 22050  # 0.5s * 44100
    assert abs(info.duration - 0.5) < 0.001


def test_stream_audio_yields_chunks(sample_wav_file: Path) -> None:
    """Test that stream_audio yields AudioChunk objects."""
    chunks = list(stream_audio(sample_wav_file, chunk_size=4096))
    
    assert len(chunks) > 0
    assert all(isinstance(c, AudioChunk) for c in chunks)
    assert chunks[-1].is_last is True


def test_stream_audio_chunk_sizes(sample_wav_file: Path) -> None:
    """Test that chunks have correct sizes."""
    chunk_size = 4096
    chunks = list(stream_audio(sample_wav_file, chunk_size=chunk_size))
    
    # All chunks except last should be full size
    for chunk in chunks[:-1]:
        assert len(chunk.samples) == chunk_size
    
    # Last chunk can be smaller
    assert len(chunks[-1].samples) <= chunk_size


def test_stream_audio_total_samples(sample_wav_file: Path) -> None:
    """Test that streaming produces same total samples as load_audio."""
    full_samples, _ = load_audio(sample_wav_file)
    
    streamed_samples = np.concatenate([c.samples for c in stream_audio(sample_wav_file)])
    
    assert len(streamed_samples) == len(full_samples)
    np.testing.assert_array_almost_equal(streamed_samples, full_samples)


def test_stream_audio_stereo_preserves_channels(stereo_wav_file: Path) -> None:
    """Test that stereo files preserve both channels when streaming."""
    chunks = list(stream_audio(stereo_wav_file))
    
    for chunk in chunks:
        assert chunk.samples.ndim == 2
        assert chunk.samples.shape[1] == 2
        assert chunk.channels == 2

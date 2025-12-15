"""Tests for audio loading."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audioviz.audio import load_audio


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


def test_load_audio_returns_samples_and_rate(sample_wav_file: Path) -> None:
    """Test that load_audio returns samples and sample rate."""
    samples, sample_rate = load_audio(sample_wav_file)
    
    assert isinstance(samples, np.ndarray)
    assert isinstance(sample_rate, int)
    assert sample_rate == 44100


def test_load_audio_mono_output(sample_wav_file: Path) -> None:
    """Test that load_audio returns mono (1D) array."""
    samples, _ = load_audio(sample_wav_file)
    
    assert samples.ndim == 1


def test_load_audio_nonexistent_file() -> None:
    """Test that load_audio raises error for missing file."""
    with pytest.raises(Exception):
        load_audio("nonexistent.wav")

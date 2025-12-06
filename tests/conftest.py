"""
Shared pytest fixtures for all tests.
"""

import pytest
import numpy as np


@pytest.fixture
def sample_audio_mono():
    """Generate sample mono audio data (1 second at 44.1kHz)."""
    sample_rate = 44100
    duration = 1.0
    frequency = 440.0  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    return audio, sample_rate


@pytest.fixture
def sample_audio_stereo():
    """Generate sample stereo audio data."""
    sample_rate = 44100
    duration = 1.0
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    left = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    right = np.sin(2 * np.pi * 880 * t).astype(np.float32)
    
    audio = np.column_stack((left, right))
    
    return audio, sample_rate


@pytest.fixture
def sample_fft_bins():
    """Generate sample FFT magnitude bins."""
    # Simulate realistic FFT output with decreasing energy at higher frequencies
    bins = np.random.rand(512).astype(np.float32)
    bins *= np.exp(-np.linspace(0, 3, 512))  # Exponential decay
    bins /= np.max(bins)  # Normalize to [0, 1]
    
    return bins

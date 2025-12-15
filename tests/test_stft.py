"""Tests for STFT computation."""

import numpy as np
import pytest

from audioviz.stft import compute_stft


def test_compute_stft_returns_correct_shapes() -> None:
    """Test that compute_stft returns arrays with expected shapes."""
    sample_rate = 44100
    duration = 1.0
    samples = np.sin(np.linspace(0, 2 * np.pi * 440 * duration, int(sample_rate * duration)))
    
    frequencies, times, magnitudes = compute_stft(samples, sample_rate, nperseg=1024)
    
    assert frequencies.ndim == 1
    assert times.ndim == 1
    assert magnitudes.ndim == 2
    assert magnitudes.shape[0] == len(frequencies)
    assert magnitudes.shape[1] == len(times)


def test_compute_stft_magnitudes_nonnegative() -> None:
    """Test that magnitudes are non-negative."""
    sample_rate = 44100
    samples = np.random.randn(44100)
    
    _, _, magnitudes = compute_stft(samples, sample_rate)
    
    assert np.all(magnitudes >= 0)


def test_compute_stft_detects_frequency() -> None:
    """Test that STFT correctly detects a known frequency."""
    sample_rate = 44100
    frequency = 1000
    duration = 1.0
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    samples = np.sin(2 * np.pi * frequency * t)
    
    frequencies, _, magnitudes = compute_stft(samples, sample_rate, nperseg=2048)
    
    # Find the dominant frequency in the middle frame
    mid_frame = magnitudes.shape[1] // 2
    peak_idx = np.argmax(magnitudes[:, mid_frame])
    peak_freq = frequencies[peak_idx]
    
    # Should be close to 1000 Hz (within one bin)
    assert abs(peak_freq - frequency) < sample_rate / 2048

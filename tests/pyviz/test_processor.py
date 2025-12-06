"""
Unit tests for signal processing module.
"""

import pytest
import numpy as np
from pyviz.processor import SignalProcessor


def test_signal_processor_initialization():
    """Test SignalProcessor initializes correctly."""
    processor = SignalProcessor(fft_size=1024, window='hann')
    
    assert processor.fft_size == 1024
    assert processor.window_name == 'hann'
    assert len(processor.window) == 1024


def test_window_functions():
    """Test different window functions are created correctly."""
    windows = ['hann', 'hamming', 'blackman']
    
    for window_type in windows:
        processor = SignalProcessor(fft_size=512, window=window_type)
        assert len(processor.window) == 512
        assert np.all(processor.window >= 0)
        assert np.all(processor.window <= 1)


def test_process_chunk_correct_size():
    """Test processing chunk of correct size."""
    processor = SignalProcessor(fft_size=1024)
    
    # Generate test signal (sine wave)
    t = np.linspace(0, 1, 1024)
    signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    
    magnitude, phase = processor.process_chunk(signal, return_phase=True)
    
    # rfft returns (N/2 + 1) bins
    assert len(magnitude) == 513
    assert len(phase) == 513
    assert np.all(magnitude >= 0)
    assert np.all(magnitude <= 1)


def test_process_chunk_normalization():
    """Test that magnitude is normalized to [0, 1]."""
    processor = SignalProcessor(fft_size=512)
    
    # Create strong signal
    signal = np.ones(512)
    magnitude, _ = processor.process_chunk(signal)
    
    assert np.max(magnitude) <= 1.0
    assert np.min(magnitude) >= 0.0


def test_process_chunk_padding():
    """Test processing chunk smaller than FFT size."""
    processor = SignalProcessor(fft_size=1024)
    
    # Smaller chunk
    signal = np.random.randn(512)
    magnitude, _ = processor.process_chunk(signal)
    
    assert len(magnitude) == 513  # Still returns full FFT bins


def test_process_chunk_truncation():
    """Test processing chunk larger than FFT size."""
    processor = SignalProcessor(fft_size=512)
    
    # Larger chunk
    signal = np.random.randn(1024)
    magnitude, _ = processor.process_chunk(signal)
    
    assert len(magnitude) == 257  # (512/2 + 1)


def test_get_frequency_bins():
    """Test frequency bin calculation."""
    processor = SignalProcessor(fft_size=1024)
    
    freqs = processor.get_frequency_bins(sample_rate=44100)
    
    assert len(freqs) == 513
    assert freqs[0] == 0  # DC component
    assert freqs[-1] == pytest.approx(22050, rel=1)  # Nyquist frequency


def test_apply_smoothing():
    """Test exponential smoothing."""
    processor = SignalProcessor()
    
    current = np.ones(100)
    previous = np.zeros(100)
    
    smoothed = processor.apply_smoothing(current, previous, alpha=0.5)
    
    assert len(smoothed) == 100
    assert np.all(smoothed == 0.5)  # Perfect average


def test_frequency_peak_detection():
    """Test that FFT correctly identifies frequency peak."""
    processor = SignalProcessor(fft_size=1024)
    sample_rate = 44100
    
    # Create pure tone at 440 Hz
    t = np.linspace(0, 1024/sample_rate, 1024)
    signal = np.sin(2 * np.pi * 440 * t)
    
    magnitude, _ = processor.process_chunk(signal)
    freqs = processor.get_frequency_bins(sample_rate)
    
    # Find peak
    peak_idx = np.argmax(magnitude)
    peak_freq = freqs[peak_idx]
    
    # Should be close to 440 Hz (within one bin)
    bin_width = sample_rate / 1024
    assert abs(peak_freq - 440) < bin_width

"""
Unit tests for audio loading module.
"""

import pytest
import numpy as np
from pathlib import Path
from pyviz.audio import AudioLoader


def test_audio_loader_initialization():
    """Test AudioLoader initializes with correct sample rate."""
    loader = AudioLoader(sample_rate=44100)
    assert loader.sample_rate == 44100
    assert loader._backend in ['librosa', 'soundfile', 'pydub']


def test_stream_chunks_no_overlap():
    """Test streaming chunks without overlap."""
    loader = AudioLoader()
    samples = np.arange(1000, dtype=np.float32)
    
    chunks = list(loader.stream_chunks(samples, chunk_size=100, hop_size=100))
    
    assert len(chunks) == 10
    assert all(len(chunk) == 100 for chunk in chunks)
    
    # Verify data integrity
    reconstructed = np.concatenate(chunks)
    np.testing.assert_array_equal(reconstructed, samples)


def test_stream_chunks_with_overlap():
    """Test streaming chunks with 50% overlap."""
    loader = AudioLoader()
    samples = np.arange(1000, dtype=np.float32)
    
    chunks = list(loader.stream_chunks(samples, chunk_size=200, hop_size=100))
    
    # With 50% overlap: (1000 - 200) / 100 + 1 = 9 chunks
    assert len(chunks) == 9
    assert all(len(chunk) == 200 for chunk in chunks)


def test_stream_chunks_padding():
    """Test that last chunk is zero-padded if needed."""
    loader = AudioLoader()
    samples = np.arange(950, dtype=np.float32)
    
    chunks = list(loader.stream_chunks(samples, chunk_size=100, hop_size=100))
    
    # Should have 10 chunks, last one padded
    assert len(chunks) == 10
    assert len(chunks[-1]) == 100
    
    # Check padding
    assert np.all(chunks[-1][50:] == 0)


def test_simple_resample():
    """Test simple resampling function."""
    loader = AudioLoader()
    
    # Create test signal
    original = np.sin(np.linspace(0, 2*np.pi, 1000))
    
    # Resample to different rate
    resampled = loader._simple_resample(original, 1000, 500)
    
    assert len(resampled) == 500
    assert resampled.dtype == original.dtype

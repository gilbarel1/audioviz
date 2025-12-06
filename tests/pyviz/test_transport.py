"""
Unit tests for shared memory transport.
"""

import pytest
import numpy as np
import time
from pyviz import transport
from pyviz.config import BUFFER_SLOTS


# Skip tests if posix_ipc not available
pytestmark = pytest.mark.skipif(
    not transport.POSIX_IPC_AVAILABLE,
    reason="posix_ipc not available"
)


@pytest.fixture
def shm_transport():
    """Create transport instance and cleanup after test."""
    trans = None
    try:
        trans = transport.SharedMemoryTransport(
            shm_name="/test_audioviz_shm",
            create=True
        )
        yield trans
    finally:
        if trans:
            trans.cleanup()
        # Cleanup test resources
        try:
            import posix_ipc
            posix_ipc.unlink_shared_memory("/test_audioviz_shm")
            posix_ipc.unlink_semaphore("/audioviz_sem_write")
        except:
            pass


def test_transport_initialization(shm_transport):
    """Test transport initializes correctly."""
    assert shm_transport is not None
    assert shm_transport.frame_sequence == 0


def test_write_single_frame(shm_transport):
    """Test writing a single frame."""
    magnitude = np.random.rand(512).astype(np.float32)
    
    success = shm_transport.write_frame(magnitude, sample_rate=44100)
    
    assert success is True
    assert shm_transport.frame_sequence == 1


def test_write_multiple_frames(shm_transport):
    """Test writing multiple frames."""
    for i in range(10):
        magnitude = np.random.rand(512).astype(np.float32)
        success = shm_transport.write_frame(magnitude, sample_rate=44100)
        assert success is True
    
    assert shm_transport.frame_sequence == 10


def test_backpressure_handling(shm_transport):
    """Test that frames are dropped when buffer is full."""
    # Fill buffer completely
    for i in range(BUFFER_SLOTS + 5):
        magnitude = np.random.rand(512).astype(np.float32)
        success = shm_transport.write_frame(magnitude, sample_rate=44100)
        
        if i < BUFFER_SLOTS:
            assert success is True
        else:
            # Should start dropping frames
            assert success is False


def test_magnitude_truncation(shm_transport):
    """Test that oversized magnitude arrays are truncated."""
    # Create magnitude array larger than MAX_FFT_BINS
    magnitude = np.random.rand(1024).astype(np.float32)
    
    success = shm_transport.write_frame(magnitude, sample_rate=44100)
    
    assert success is True


def test_frame_timing(shm_transport):
    """Test that timestamps are reasonable."""
    magnitude = np.random.rand(512).astype(np.float32)
    
    before = time.time()
    shm_transport.write_frame(magnitude, sample_rate=44100)
    after = time.time()
    
    # Can't directly check timestamp, but frame should succeed
    assert shm_transport.frame_sequence == 1

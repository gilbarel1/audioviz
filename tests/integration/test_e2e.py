"""
Integration test: End-to-end pipeline.
"""

import pytest
import numpy as np
import time
from pyviz.audio import AudioLoader
from pyviz.processor import SignalProcessor
from pyviz import transport

# Skip if no IPC support
pytestmark = pytest.mark.skipif(
    not transport.POSIX_IPC_AVAILABLE,
    reason="posix_ipc not available"
)


def test_full_pipeline(sample_audio_mono):
    """Test complete audio processing pipeline."""
    audio, sample_rate = sample_audio_mono
    
    # Initialize components
    loader = AudioLoader(sample_rate=sample_rate)
    processor = SignalProcessor(fft_size=1024)
    trans = None
    
    try:
        trans = transport.SharedMemoryTransport(
            shm_name="/test_pipeline_shm",
            create=True
        )
        
        # Process audio
        frame_count = 0
        for chunk in loader.stream_chunks(audio, chunk_size=1024, hop_size=512):
            magnitude, _ = processor.process_chunk(chunk)
            success = trans.write_frame(magnitude, sample_rate)
            
            if success:
                frame_count += 1
        
        assert frame_count > 0
        assert trans.frame_sequence == frame_count
        
    finally:
        if trans:
            trans.cleanup()
        # Cleanup
        try:
            import posix_ipc
            posix_ipc.unlink_shared_memory("/test_pipeline_shm")
            posix_ipc.unlink_semaphore("/audioviz_sem_write")
        except:
            pass


def test_pipeline_timing(sample_audio_mono):
    """Test that pipeline meets latency targets."""
    audio, sample_rate = sample_audio_mono
    
    processor = SignalProcessor(fft_size=1024)
    
    # Take small sample
    chunk = audio[:1024]
    
    # Measure processing time
    start = time.time()
    magnitude, _ = processor.process_chunk(chunk)
    elapsed = time.time() - start
    
    # Should be well under 5ms target
    assert elapsed < 0.005

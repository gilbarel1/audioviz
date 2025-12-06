"""
Transport layer for inter-process communication with C renderer.

Uses POSIX shared memory and semaphores for low-latency data transfer.
"""

import struct
import time
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# Platform-specific imports with fallback
try:
    import posix_ipc
    POSIX_IPC_AVAILABLE = True
except ImportError:
    POSIX_IPC_AVAILABLE = False
    logger.warning("posix_ipc not available, shared memory transport disabled")

try:
    import mmap
    MMAP_AVAILABLE = True
except ImportError:
    MMAP_AVAILABLE = False


from .config import (
    SHM_NAME, SEM_WRITE_NAME, SEM_READ_NAME,
    BUFFER_SLOTS, SLOT_SIZE, HEADER_SIZE,
    MAGIC_NUMBER, ENDIANNESS, MAX_FFT_BINS
)


class SharedMemoryTransport:
    """
    Manages shared memory circular buffer for FFT data transfer.
    
    Protocol:
        - Circular buffer with BUFFER_SLOTS slots
        - Each slot contains: [Header (64 bytes)][Data (remaining)]
        - Producer (Python) writes to slot (frame_seq % BUFFER_SLOTS)
        - Consumer (C) reads oldest unread slot
        - Semaphores coordinate access
    """
    
    def __init__(
        self, 
        shm_name: str = SHM_NAME,
        create: bool = True
    ):
        """
        Initialize shared memory transport.
        
        Args:
            shm_name: Shared memory segment name
            create: If True, create new segment; if False, attach to existing
        """
        if not POSIX_IPC_AVAILABLE:
            raise RuntimeError(
                "posix_ipc not available. Install with: pip install posix_ipc"
            )
        
        self.shm_name = shm_name
        self.frame_sequence = 0
        self.total_size = BUFFER_SLOTS * SLOT_SIZE
        
        # Create or attach to shared memory
        try:
            if create:
                # Unlink existing segment if present
                try:
                    posix_ipc.unlink_shared_memory(shm_name)
                except posix_ipc.ExistentialError:
                    pass
                
                self.shm = posix_ipc.SharedMemory(
                    shm_name, 
                    flags=posix_ipc.O_CREX,
                    size=self.total_size
                )
                logger.info(f"Created shared memory: {shm_name} ({self.total_size} bytes)")
            else:
                self.shm = posix_ipc.SharedMemory(shm_name)
                logger.info(f"Attached to shared memory: {shm_name}")
            
            # Memory map the segment
            self.mapfile = mmap.mmap(self.shm.fd, self.total_size)
            
        except Exception as e:
            logger.error(f"Failed to initialize shared memory: {e}")
            raise
        
        # Create or attach to semaphores
        try:
            if create:
                try:
                    posix_ipc.unlink_semaphore(SEM_WRITE_NAME)
                except posix_ipc.ExistentialError:
                    pass
                
                self.sem_write = posix_ipc.Semaphore(
                    SEM_WRITE_NAME,
                    flags=posix_ipc.O_CREX,
                    initial_value=0
                )
                logger.info(f"Created semaphore: {SEM_WRITE_NAME}")
            else:
                self.sem_write = posix_ipc.Semaphore(SEM_WRITE_NAME)
                logger.info(f"Attached to semaphore: {SEM_WRITE_NAME}")
                
        except Exception as e:
            logger.error(f"Failed to initialize semaphores: {e}")
            self.cleanup()
            raise
    
    def write_frame(
        self,
        magnitude: np.ndarray,
        sample_rate: int,
        phase: Optional[np.ndarray] = None
    ) -> bool:
        """
        Write FFT frame to shared memory.
        
        Args:
            magnitude: FFT magnitude bins (float32 array)
            sample_rate: Audio sample rate
            phase: Optional phase data
            
        Returns:
            True if written successfully, False if dropped (backpressure)
        """
        # Check backpressure
        if self.sem_write.value >= BUFFER_SLOTS:
            logger.warning(f"Buffer full, dropping frame {self.frame_sequence}")
            return False
        
        # Validate bin count
        bin_count = len(magnitude)
        if bin_count > MAX_FFT_BINS:
            logger.warning(f"Truncating {bin_count} bins to {MAX_FFT_BINS}")
            magnitude = magnitude[:MAX_FFT_BINS]
            if phase is not None:
                phase = phase[:MAX_FFT_BINS]
            bin_count = MAX_FFT_BINS
        
        # Determine slot index
        slot_idx = self.frame_sequence % BUFFER_SLOTS
        slot_offset = slot_idx * SLOT_SIZE
        
        # Build header
        timestamp_us = int(time.time() * 1_000_000)
        header = struct.pack(
            f"<IQQIIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # Little-endian, 36 bytes reserved
            MAGIC_NUMBER,       # 4 bytes
            self.frame_sequence, # 8 bytes
            timestamp_us,        # 8 bytes
            sample_rate,         # 4 bytes
            bin_count            # 4 bytes
        )
        
        assert len(header) == HEADER_SIZE, f"Header size mismatch: {len(header)}"
        
        # Serialize magnitude data
        magnitude_bytes = magnitude.astype(np.float32).tobytes()
        
        # Serialize phase if present
        phase_bytes = b""
        if phase is not None:
            phase_bytes = phase.astype(np.float32).tobytes()
        
        # Write to shared memory slot
        data = header + magnitude_bytes + phase_bytes
        if len(data) > SLOT_SIZE:
            logger.error(f"Data size {len(data)} exceeds slot size {SLOT_SIZE}")
            return False
        
        # Pad to slot size
        data = data.ljust(SLOT_SIZE, b'\x00')
        
        # Write atomically
        self.mapfile.seek(slot_offset)
        self.mapfile.write(data)
        self.mapfile.flush()
        
        # Signal consumer
        self.sem_write.release()
        
        self.frame_sequence += 1
        
        if self.frame_sequence % 100 == 0:
            logger.debug(f"Wrote frame {self.frame_sequence} to slot {slot_idx}")
        
        return True
    
    def cleanup(self):
        """Release shared memory and semaphore resources."""
        try:
            if hasattr(self, 'mapfile'):
                self.mapfile.close()
            if hasattr(self, 'shm'):
                self.shm.close_fd()
            if hasattr(self, 'sem_write'):
                self.sem_write.close()
            logger.info("Transport cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def __del__(self):
        self.cleanup()


def unlink_resources():
    """Unlink shared memory and semaphores (cleanup utility)."""
    if not POSIX_IPC_AVAILABLE:
        return
    
    try:
        posix_ipc.unlink_shared_memory(SHM_NAME)
        logger.info(f"Unlinked shared memory: {SHM_NAME}")
    except posix_ipc.ExistentialError:
        pass
    
    try:
        posix_ipc.unlink_semaphore(SEM_WRITE_NAME)
        logger.info(f"Unlinked semaphore: {SEM_WRITE_NAME}")
    except posix_ipc.ExistentialError:
        pass

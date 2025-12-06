"""
Signal processing module for FFT computation.

Handles windowing, FFT computation via SciPy, and magnitude extraction.
"""

import numpy as np
from scipy import fft
from typing import Optional
import logging

from .config import DEFAULT_WINDOW, DEFAULT_FFT_SIZE

logger = logging.getLogger(__name__)


class SignalProcessor:
    """
    Processes audio chunks with windowing and FFT.
    """
    
    def __init__(
        self, 
        fft_size: int = DEFAULT_FFT_SIZE,
        window: str = DEFAULT_WINDOW
    ):
        """
        Initialize signal processor.
        
        Args:
            fft_size: FFT size (number of samples)
            window: Window function name ('hann', 'hamming', 'blackman')
        """
        self.fft_size = fft_size
        self.window_name = window
        self.window = self._create_window(window, fft_size)
        
        logger.info(f"Initialized SignalProcessor: FFT={fft_size}, window={window}")
    
    def _create_window(self, window_type: str, size: int) -> np.ndarray:
        """Create window function."""
        if window_type == "hann":
            return np.hanning(size)
        elif window_type == "hamming":
            return np.hamming(size)
        elif window_type == "blackman":
            return np.blackman(size)
        else:
            logger.warning(f"Unknown window type '{window_type}', using rectangular")
            return np.ones(size)
    
    def process_chunk(
        self, 
        chunk: np.ndarray,
        return_phase: bool = False
    ) -> tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Process audio chunk: apply window, compute FFT, extract magnitude.
        
        Args:
            chunk: Audio samples (should be fft_size length)
            return_phase: If True, also return phase information
            
        Returns:
            Tuple of (magnitude, phase)
            - magnitude: FFT magnitude bins, normalized to [0, 1]
            - phase: Phase in radians (or None if return_phase=False)
        """
        if len(chunk) != self.fft_size:
            logger.warning(
                f"Chunk size {len(chunk)} != FFT size {self.fft_size}, "
                f"zero-padding or truncating"
            )
            if len(chunk) < self.fft_size:
                padded = np.zeros(self.fft_size)
                padded[:len(chunk)] = chunk
                chunk = padded
            else:
                chunk = chunk[:self.fft_size]
        
        # Apply window
        windowed = chunk * self.window
        
        # Compute FFT (real FFT for efficiency)
        fft_result = fft.rfft(windowed)
        
        # Extract magnitude and normalize
        magnitude = np.abs(fft_result)
        magnitude = magnitude / (self.fft_size / 2)  # Normalize by FFT size
        
        # Clip to [0, 1] range
        magnitude = np.clip(magnitude, 0, 1)
        
        # Extract phase if requested
        phase = None
        if return_phase:
            phase = np.angle(fft_result)
        
        return magnitude, phase
    
    def get_frequency_bins(self, sample_rate: int) -> np.ndarray:
        """
        Get frequency values for each FFT bin.
        
        Args:
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Array of frequency values in Hz
        """
        return fft.rfftfreq(self.fft_size, 1.0 / sample_rate)
    
    def apply_smoothing(
        self, 
        current: np.ndarray, 
        previous: np.ndarray,
        alpha: float = 0.3
    ) -> np.ndarray:
        """
        Apply exponential smoothing between frames.
        
        Args:
            current: Current magnitude spectrum
            previous: Previous magnitude spectrum
            alpha: Smoothing factor [0, 1] (higher = more responsive)
            
        Returns:
            Smoothed magnitude spectrum
        """
        return alpha * current + (1 - alpha) * previous

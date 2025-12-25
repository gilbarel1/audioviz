"""STFT (Short-Time Fourier Transform) processing using SciPy."""

import numpy as np
from scipy import signal


def compute_stft(
    samples: np.ndarray,
    sample_rate: int,
    nperseg: int = 1024,
    noverlap: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the Short-Time Fourier Transform of audio samples.
    
    Args:
        samples: Audio samples as numpy array.
        sample_rate: Sample rate in Hz.
        nperseg: Length of each segment (FFT window size).
        noverlap: Number of points to overlap between segments.
                  Defaults to nperseg // 2 (50% overlap).
    
    Returns:
        Tuple of (frequencies, times, magnitudes).
        frequencies: Array of sample frequencies.
        times: Array of segment times.
        magnitudes: STFT magnitude (absolute value), shape (n_frequencies, n_times).
    """
    if noverlap is None:
        noverlap = nperseg // 2
    
    frequencies, times, stft_result = signal.stft(
        samples,
        fs=sample_rate,
        nperseg=nperseg,
        noverlap=noverlap,
    )
    
    # Get magnitude (absolute value of complex STFT)
    magnitudes = np.abs(stft_result)
    
    return frequencies, times, magnitudes

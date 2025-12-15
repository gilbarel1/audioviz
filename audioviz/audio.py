"""Audio file loading using soundfile."""

from pathlib import Path

import numpy as np
import soundfile as sf


def load_audio(filepath: str | Path) -> tuple[np.ndarray, int]:
    """
    Load an audio file and return samples and sample rate.
    
    Args:
        filepath: Path to the audio file.
        
    Returns:
        Tuple of (samples, sample_rate).
        samples: Audio data as float64 numpy array.
                 If stereo, converted to mono by averaging channels.
    """
    samples, sample_rate = sf.read(filepath, dtype='float64')
    
    # Convert stereo to mono by averaging channels
    if samples.ndim > 1:
        samples = np.mean(samples, axis=1)
    
    return samples, sample_rate

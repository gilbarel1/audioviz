"""
Audio file ingestion and decoding module.

Supports multiple audio libraries with fallback mechanism:
- librosa (primary)
- soundfile (fallback)
- pydub (fallback)
"""

import numpy as np
from typing import Generator, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AudioLoader:
    """
    Loads and decodes audio files to PCM samples.
    """
    
    def __init__(self, sample_rate: int = 44100):
        """
        Initialize audio loader.
        
        Args:
            sample_rate: Target sample rate for resampling
        """
        self.sample_rate = sample_rate
        self._backend = self._detect_backend()
        
    def _detect_backend(self) -> str:
        """Detect available audio backend."""
        try:
            import librosa
            return "librosa"
        except ImportError:
            pass
            
        try:
            import soundfile
            return "soundfile"
        except ImportError:
            pass
            
        try:
            import pydub
            return "pydub"
        except ImportError:
            raise RuntimeError(
                "No audio backend available. Install one of: "
                "librosa, soundfile, pydub"
            )
    
    def load(self, filepath: str) -> Tuple[np.ndarray, int]:
        """
        Load entire audio file.
        
        Args:
            filepath: Path to audio file
            
        Returns:
            Tuple of (samples, sample_rate)
            samples: mono float32 array in range [-1, 1]
        """
        if self._backend == "librosa":
            return self._load_librosa(filepath)
        elif self._backend == "soundfile":
            return self._load_soundfile(filepath)
        elif self._backend == "pydub":
            return self._load_pydub(filepath)
        else:
            raise RuntimeError(f"Unknown backend: {self._backend}")
    
    def _load_librosa(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load using librosa."""
        import librosa
        samples, sr = librosa.load(filepath, sr=self.sample_rate, mono=True)
        logger.info(f"Loaded {filepath} using librosa: {len(samples)} samples @ {sr} Hz")
        return samples, sr
    
    def _load_soundfile(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load using soundfile."""
        import soundfile as sf
        samples, sr = sf.read(filepath, dtype='float32')
        
        # Convert to mono if stereo
        if len(samples.shape) > 1:
            samples = np.mean(samples, axis=1)
        
        # Resample if needed (basic interpolation)
        if sr != self.sample_rate:
            logger.warning(f"Resampling from {sr} to {self.sample_rate} Hz (basic method)")
            samples = self._simple_resample(samples, sr, self.sample_rate)
            sr = self.sample_rate
            
        logger.info(f"Loaded {filepath} using soundfile: {len(samples)} samples @ {sr} Hz")
        return samples, sr
    
    def _load_pydub(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load using pydub."""
        from pydub import AudioSegment
        audio = AudioSegment.from_file(filepath)
        
        # Convert to mono and resample
        audio = audio.set_channels(1).set_frame_rate(self.sample_rate)
        
        # Convert to numpy array
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        samples = samples / (2**15)  # Normalize to [-1, 1]
        
        logger.info(f"Loaded {filepath} using pydub: {len(samples)} samples @ {self.sample_rate} Hz")
        return samples, self.sample_rate
    
    def _simple_resample(self, samples: np.ndarray, old_sr: int, new_sr: int) -> np.ndarray:
        """Simple linear interpolation resampling."""
        duration = len(samples) / old_sr
        new_length = int(duration * new_sr)
        old_indices = np.linspace(0, len(samples) - 1, new_length)
        return np.interp(old_indices, np.arange(len(samples)), samples)
    
    def stream_chunks(
        self, 
        samples: np.ndarray, 
        chunk_size: int,
        hop_size: Optional[int] = None
    ) -> Generator[np.ndarray, None, None]:
        """
        Stream audio samples in chunks with optional overlap.
        
        Args:
            samples: Audio samples array
            chunk_size: Number of samples per chunk
            hop_size: Step size between chunks (default: chunk_size, no overlap)
            
        Yields:
            Audio chunks as numpy arrays
        """
        if hop_size is None:
            hop_size = chunk_size
            
        num_chunks = (len(samples) - chunk_size) // hop_size + 1
        
        for i in range(num_chunks):
            start = i * hop_size
            end = start + chunk_size
            
            if end > len(samples):
                # Pad last chunk with zeros
                chunk = np.zeros(chunk_size, dtype=samples.dtype)
                chunk[:len(samples) - start] = samples[start:]
            else:
                chunk = samples[start:end]
                
            yield chunk

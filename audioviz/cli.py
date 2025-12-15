"""Command-line interface for AudioViz."""

import argparse
import sys

from .audio import load_audio
from .stft import compute_stft


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AudioViz - Compute and display frequency amplitudes from audio files'
    )
    parser.add_argument(
        'audio_file',
        type=str,
        help='Path to audio file (WAV, FLAC, etc.)',
    )
    parser.add_argument(
        '--nperseg',
        type=int,
        default=1024,
        help='FFT window size (default: 1024)',
    )
    
    args = parser.parse_args()
    
    try:
        # Load audio
        print(f"Loading: {args.audio_file}")
        samples, sample_rate = load_audio(args.audio_file)
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Duration: {len(samples) / sample_rate:.2f} seconds")
        print(f"  Samples: {len(samples)}")
        
        # Compute STFT
        print(f"\nComputing STFT (window size: {args.nperseg})...")
        frequencies, times, magnitudes = compute_stft(
            samples, sample_rate, nperseg=args.nperseg
        )
        print(f"  Frequency bins: {len(frequencies)}")
        print(f"  Time frames: {len(times)}")
        
        # Print amplitude summary for each time frame
        print(f"\nFrequency amplitudes (first 80 frames):")
        print("-" * 60)
        
        for i, t in enumerate(times[:80]):
            frame_magnitudes = magnitudes[:, i]
            max_idx = np.argmax(frame_magnitudes)
            max_freq = frequencies[max_idx]
            max_amp = frame_magnitudes[max_idx]
            mean_amp = np.mean(frame_magnitudes)
            
            print(f"  t={t:.3f}s: max={max_amp:.4f} @ {max_freq:.1f}Hz, mean={mean_amp:.6f}")
        
        if len(times) > 10:
            print(f"  ... ({len(times) - 10} more frames)")
        
        return 0
        
    except FileNotFoundError:
        print(f"Error: File not found: {args.audio_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# Required for numpy in print
import numpy as np

if __name__ == '__main__':
    sys.exit(main())

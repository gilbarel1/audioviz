"""Command-line interface for AudioViz."""

import argparse
import signal
import scipy.signal
import sys
import numpy as np
from .audioviz.audio import audio_info, stream_audio
import libaudioviz
import time
##from .audioviz.stft import compute_stft


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AudioViz - Real-time Audio Visualization'
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
        # load audio info
        print(f"Loading: {args.audio_file}")
        info = audio_info(args.audio_file)
        print(f"  Sample rate: {info.sample_rate} Hz")
        print(f"  Duration: {info.duration:.2f} seconds")
        print(f"  Channels: {info.channels}")
        print(f"  Frames: {info.frames}")
        
        # Stream and concatenate samples for STFT
        samples = np.concatenate([chunk.samples for chunk in stream_audio(args.audio_file)])
        
        # For stereo, use first channel for now
        if samples.ndim > 1:
            samples = samples[:, 0]
        
        # Compute STFT
        print(f"\nComputing STFT (window size: {args.nperseg})...")

        # Use scipy.signal.stft
        f, t, Zxx = scipy.signal.stft(
            samples, 
            fs=info.sample_rate, 
            nperseg=args.nperseg, 
            noverlap=args.nperseg // 2
        )
        
        # Transpose to iterate over time frames (Time x Frequency)
        # Zxx is (Freqs, Times), we need (Times, Freqs)
        stft_frames = Zxx.T
        
        print(f"  Total frames to render: {len(t)}")

        # 4. Initialize C++ Renderer
        renderer = libaudioviz.Renderer(800, 600)
        renderer.initialize_window() 
        
        print("Starting playback... (Press Ctrl+C to stop)")

        # 5. Render Loop
        for i, frame_data in enumerate(stft_frames):
            # Pass the complex frequency data to C++
            renderer.render_frame(frame_data.astype(np.complex64))
             #TODO: play audio
            #  TODO : Sync playback speed with audio time
           
                
        return 0
        
    except FileNotFoundError:
        print(f"Error: File not found: {args.audio_file}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopping...")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

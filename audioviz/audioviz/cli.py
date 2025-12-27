"""Command-line interface for AudioViz."""

import argparse
import scipy.signal
import sys
import numpy as np
import time
import sounddevice as sd
from .audio import audio_info, stream_audio
import libaudioviz


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
    parser.add_argument(
        '--blocksize',
        type=int,
        default=8192,
        help='Audio playback buffer size (default: 8192)',
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
        
        audio_samples = samples
        
        # Compute STFT for all channels
        print(f"\nComputing STFT (window size: {args.nperseg})...")
        
        if samples.ndim == 1:
            samples = samples[:, np.newaxis]
        
        num_channels = samples.shape[1]
        
        # Compute STFT for each channel
        stft_per_channel = []
        for ch in range(num_channels):
            f, t, Zxx = scipy.signal.stft(
                samples[:, ch], 
                fs=info.sample_rate, 
                nperseg=args.nperseg, 
                noverlap=args.nperseg // 2
            )
            stft_per_channel.append(Zxx.T)
        
        # Stack all channels: (Times, Channels, Freqs)
        stft_channels = np.stack(stft_per_channel, axis=1)
        
        time_per_frame = info.duration / len(stft_channels)
        # Initialize C++ Renderer
        renderer = libaudioviz.Renderer(800, 600)
        renderer.initialize_window() 
        
        print("Starting playback... (Press Ctrl+C to stop)")

        # Start non-blocking audio playback
        sd.play(audio_samples, info.sample_rate, blocksize=args.blocksize)

        # Render Loop
        for frame_channels in stft_channels:
            start_time = time.time()

            # For now, visualize first channel only
            magnitudes = np.abs(frame_channels[0]).astype(np.float32)
            renderer.render_frame(magnitudes)
            
            processing_time = time.time() - start_time
            sleep_time = max(0, time_per_frame - processing_time)
            time.sleep(sleep_time)           
           
        sd.stop()
        print("\nPlayback finished.")
        input("Press Enter to close window...") 
        return 0       
        
        
    except FileNotFoundError:
        print(f"Error: File not found: {args.audio_file}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        sd.stop()
        print("\nStopping...")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

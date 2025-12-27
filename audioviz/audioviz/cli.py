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
        
        # For stereo, use first channel for visualization
        if samples.ndim > 1:
            samples = samples[:, 0]
        
        # Compute STFT
        print(f"\nComputing STFT (window size: {args.nperseg})...")

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

        #calculate frame time
        time_per_frame = info.duration / len(stft_frames)

        # 4. Initialize C++ Renderer
        renderer = libaudioviz.Renderer(800, 600)
        renderer.initialize_window() 
        
        print("Starting playback... (Press Ctrl+C to stop)")

        # Start non-blocking audio playback
        sd.play(audio_samples, info.sample_rate, blocksize=8192)

        # 5. Render Loop
        for i, frame_data in enumerate(stft_frames):
            start_time = time.time()

            magnitudes = np.abs(frame_data).astype(np.float32)
            # Pass the complex frequency data to C++
            renderer.render_frame(magnitudes)

            #sleep after each render so i will be able to see something
            #TODO - maybe need to change sleep time for sync
            processing_time = time.time() - start_time
            sleep_time = max(0, time_per_frame - processing_time)
            time.sleep(sleep_time)           
            #TODO: Sync playback speed with audio time
           

        #so the window not close too fast 
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

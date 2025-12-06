"""
Command-line interface for PyViz audio processor.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from .config import (
    DEFAULT_SAMPLE_RATE, DEFAULT_FFT_SIZE, 
    DEFAULT_HOP_SIZE, DEFAULT_WINDOW
)
from .audio import AudioLoader
from .processor import SignalProcessor
from .transport import SharedMemoryTransport, unlink_resources


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PyViz - Audio Processing for Music Visualizer'
    )
    parser.add_argument(
        'audio_file',
        type=str,
        help='Path to audio file'
    )
    parser.add_argument(
        '--sample-rate',
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help=f'Target sample rate (default: {DEFAULT_SAMPLE_RATE})'
    )
    parser.add_argument(
        '--fft-size',
        type=int,
        default=DEFAULT_FFT_SIZE,
        help=f'FFT size in samples (default: {DEFAULT_FFT_SIZE})'
    )
    parser.add_argument(
        '--hop-size',
        type=int,
        default=DEFAULT_HOP_SIZE,
        help=f'Hop size in samples (default: {DEFAULT_HOP_SIZE})'
    )
    parser.add_argument(
        '--window',
        type=str,
        default=DEFAULT_WINDOW,
        choices=['hann', 'hamming', 'blackman'],
        help=f'Window function (default: {DEFAULT_WINDOW})'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up shared memory and exit'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Cleanup mode
    if args.cleanup:
        logger.info("Cleaning up IPC resources...")
        unlink_resources()
        return 0
    
    # Validate audio file
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        return 1
    
    try:
        # Initialize components
        logger.info("Initializing audio processor...")
        loader = AudioLoader(sample_rate=args.sample_rate)
        processor = SignalProcessor(fft_size=args.fft_size, window=args.window)
        transport = SharedMemoryTransport(create=True)
        
        # Load audio file
        logger.info(f"Loading audio: {audio_path}")
        samples, sample_rate = loader.load(str(audio_path))
        logger.info(f"Loaded {len(samples)} samples @ {sample_rate} Hz ({len(samples)/sample_rate:.2f} seconds)")
        
        # Process and stream
        logger.info(f"Starting audio processing (FFT size: {args.fft_size}, hop: {args.hop_size})...")
        frame_count = 0
        dropped_count = 0
        start_time = time.time()
        
        for chunk in loader.stream_chunks(samples, args.fft_size, args.hop_size):
            # Compute FFT
            magnitude, _ = processor.process_chunk(chunk, return_phase=False)
            
            # Send to renderer
            success = transport.write_frame(magnitude, sample_rate)
            
            if success:
                frame_count += 1
            else:
                dropped_count += 1
            
            # Throttle to real-time playback
            expected_time = frame_count * args.hop_size / sample_rate
            elapsed_time = time.time() - start_time
            sleep_time = expected_time - elapsed_time
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Summary
        total_time = time.time() - start_time
        logger.info(f"Processing complete:")
        logger.info(f"  Frames sent: {frame_count}")
        logger.info(f"  Frames dropped: {dropped_count}")
        logger.info(f"  Duration: {total_time:.2f} seconds")
        logger.info(f"  Average FPS: {frame_count / total_time:.1f}")
        
        # Cleanup
        transport.cleanup()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

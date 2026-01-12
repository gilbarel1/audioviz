"""Command-line interface for AudioViz."""

import argparse
import scipy.signal
import sys
import numpy as np
import time
import sounddevice as sd

from .audio import audio_info, stream_audio
from .state_manager import StateManager, StateManagerConfig
from .visualizers import get_visualizer
from .config import FrameCommands, DrawBatch, APP, AUDIO, UI
from .ui import create_button_panel



import libaudioviz


def render_frame(renderer: libaudioviz.Renderer, commands: FrameCommands, 
                 labels: list[tuple[str, int, int]] = None) -> None:
    """
    Send draw commands to the C++ renderer.
    
    Args:
        renderer: The C++ renderer instance
        commands: Frame commands containing background color and draw batches
        labels: Optional list of (text, x, y) for text rendering
    """
    # Clear with background color
    bg = commands.background
    renderer.clear(bg.r, bg.g, bg.b, bg.a)
    
    # Draw each batch
    for batch in commands.batches:
        r, g, b, a = batch.color.as_tuple()
        
        if batch.rectangles:
            # Convert Python Rect objects to C++ Rect objects
            cpp_rects = [
                libaudioviz.Rect(rect.x, rect.y, rect.width, rect.height) 
                for rect in batch.rectangles
            ]
            renderer.draw_rectangles(cpp_rects, r, g, b, a)
        
        if batch.lines:
            # Convert Python Line objects to C++ Line objects
            cpp_lines = [
                libaudioviz.Line(line.x1, line.y1, line.x2, line.y2) 
                for line in batch.lines
            ]
            renderer.draw_lines(cpp_lines, r, g, b, a)
    
    # Draw text labels
    if labels:
        r, g, b, a = UI.text_color.as_tuple()
        for text, x, y in labels:
            renderer.draw_text(text, x, y, r, g, b, a)

    
    # Present to screen
    renderer.present()


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
        default=AUDIO.nperseg,
        help=f'FFT window size (default: {AUDIO.nperseg})',

    )
    parser.add_argument(
        '--blocksize',
        type=int,
        default=AUDIO.blocksize,
        help=f'Audio playback buffer size (default: {AUDIO.blocksize})',

    )
    parser.add_argument(
        '--mode',
        type=str,
        default=APP.default_mode,
        choices=APP.modes,
        help=f'Initial visualization mode (default: {APP.default_mode})',

    )
    parser.add_argument(
        '--no-auto-switch',
        action='store_true',
        help='Disable automatic mode switching',
    )
    
    args = parser.parse_args()
    
    try:
        # Load audio info
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
        width, height = APP.window_width, APP.window_height

        renderer = libaudioviz.Renderer(width, height)
        
        # Load font from configured path
        try:
            renderer.initialize_window(APP.font_path)
        except Exception as e:
            print(f"Warning: Renderer initialization issue: {e}", file=sys.stderr)
            raise
        
        # Initialize state manager
        auto_switch = None if args.no_auto_switch else 5.0
        config = StateManagerConfig(
            initial_mode=args.mode,
            width=width,
            height=height,
            auto_switch_interval=auto_switch,
        )
        state_manager = StateManager(config)
        
        print("Starting playback... (Click buttons to switch modes, Esc to quit)")
        
        # Start non-blocking audio playback
        sd.play(audio_samples, info.sample_rate, blocksize=args.blocksize)
        playback_start = time.time()
        
        # Main render loop
        while True:
            elapsed = time.time() - playback_start
            frame_idx = int(elapsed / time_per_frame)
            if frame_idx >= len(stft_channels):
                break
            
            # Poll events and update state
            events = renderer.poll_events()
            state = state_manager.update(events)
            
            # Check if we should quit
            if not state.is_running or renderer.should_quit():
                break
            
            # Get current magnitudes
            magnitudes = np.abs(stft_channels[frame_idx][0]).astype(np.float32)
            
            # Get visualizer and compute draw commands
            visualizer = get_visualizer(state.mode)
            viz_commands = visualizer(magnitudes, state.width, state.height)
            
            # Helper for default background if needed
            from .config import Color, BLACK
            
            if viz_commands:
                viz_batches = viz_commands.batches
                bg_color = viz_commands.background
            else:
                viz_batches = ()
                bg_color = BLACK
            
            # Render button panel on top
            button_batches = state.button_panel.render(state.mode)
            
            # Combine visualization and UI batches
            all_batches = viz_batches + tuple(button_batches)
            commands = FrameCommands(batches=all_batches, background=bg_color)
            
            # Get button labels for text rendering
            labels = state.button_panel.get_labels()
            
            # Render the frame with text
            render_frame(renderer, commands, labels)
        
        sd.stop()
        print("\nPlayback finished.")
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

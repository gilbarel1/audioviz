"""Command-line interface for AudioViz."""

import argparse
import scipy.signal
import sys
import numpy as np
import time
import sounddevice as sd

from .audio import audio_info, stream_audio
from .state_manager import StateManager, StateManagerConfig
from .visualizers import get_visualizer, get_default_viz_configs, get_mode_names
from .config import FrameCommands, DrawBatch, AppConfig, AudioConfig, UIConfig, ButtonType
from .ui import create_button_panel, render_button_panel, calculate_label_positions, render_timeline, get_timeline_labels
from .config import Color, BLACK


import libaudioviz


def render_frame(renderer: libaudioviz.Renderer, commands: FrameCommands, 
                 labels: list[tuple[str, int, int]] = None, ui_config: UIConfig = None) -> None:
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
    
    # Draw text labels (white text)
    if labels:
        r, g, b, a = ui_config.text_color.as_tuple()
        for text, x, y in labels:
            renderer.draw_text(text, x, y, r, g, b, a)

    
    # Present to screen
    renderer.present()


def main() -> int:
    """Main entry point."""
    # Create config instances (no more globals!)
    app_config = AppConfig()
    audio_config = AudioConfig()
    ui_config = UIConfig()
    
    # Visualizer configs (initialized with defaults from registry)
    viz_configs = get_default_viz_configs()
    
    # Derive available modes from button_specs (single source of truth)
    available_modes = [spec[0] for spec in app_config.button_specs if spec[1] == ButtonType.MODE]
    
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
        default=audio_config.nperseg,
        help=f'FFT window size (default: {audio_config.nperseg})',

    )
    parser.add_argument(
        '--blocksize',
        type=int,
        default=audio_config.blocksize,
        help=f'Audio playback buffer size (default: {audio_config.blocksize})',

    )
    parser.add_argument(
        '--mode',
        type=str,
        default=app_config.default_mode,
        choices=available_modes,
        help=f'Initial visualization mode (default: {app_config.default_mode})',
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
        width, height = app_config.window_width, app_config.window_height

        renderer = libaudioviz.Renderer(width, height)
        
        # Load font from configured path
        try:
            renderer.initialize_window(app_config.font_path)
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
            button_specs=app_config.button_specs,
            mode_order=tuple(available_modes),
            app_config=app_config,
            ui_config=ui_config,
            total_duration=info.duration,  # Pass total duration
        )
        state_manager = StateManager(config)
        
        print("Starting playback... (Click buttons to switch modes, Esc to quit)")
        
        # Start non-blocking audio playback
        # We need to keep track of where we are in the file to support seeking
        current_sample_idx = 0
        sd.play(audio_samples, info.sample_rate, blocksize=args.blocksize)
        playback_start = time.time()
        playback_offset = 0.0  # Time offset from seeks
        
        # Main render loop
        while True:
            # Calculate current playback time
            now = time.time()
            elapsed_play = now - playback_start
            current_time = playback_offset + elapsed_play
            
            # Clamp to duration
            if current_time > info.duration:
                 current_time = info.duration
                 
            # Sync time to state manager (for UI to know where knob is)
            # We don't change mode here, just update time info
            # Note: updating state here is slightly inefficient if nothing changed, 
            # but we need smooth progress bar.
            # Only update if not dragging (or update dragging time separate? NO, state manager handles drag overrides)
            if not state_manager.state.is_dragging:
                 state_manager._state = state_manager.state.with_time(current_time)

            frame_idx = int(current_time / time_per_frame)
            if frame_idx >= len(stft_channels):
                # Loop or stop? Let's stop for now as per original behavior
                break
            
            # Poll events and update state
            events = renderer.poll_events()
            state = state_manager.update(events)
            
            # Check for seek request
            if state.seek_request is not None:
                seek_time = state.seek_request
                
                # Stop current playback
                sd.stop()
                
                # Calculate new sample index
                new_sample_idx = int(seek_time * info.sample_rate)
                new_sample_idx = max(0, min(new_sample_idx, len(audio_samples) - 1))
                
                # Restart playback from new position
                remaining_samples = audio_samples[new_sample_idx:]
                if len(remaining_samples) > 0:
                    sd.play(remaining_samples, info.sample_rate, blocksize=args.blocksize)
                
                # Update time tracking
                playback_start = time.time()
                playback_offset = seek_time
                current_time = seek_time
                
                # Clear seek request from state
                state_manager._state = state.with_time(current_time, is_dragging=state.is_dragging, seek_req=None)
                state = state_manager.state # Refresh local var
            
            # Check if we should quit
            
            # Check if we should quit
            if not state.is_running or renderer.should_quit():
                break
            
            # Get current magnitudes (safe check for bounds)
            safe_frame_idx = min(frame_idx, len(stft_channels) - 1)
            magnitudes = np.abs(stft_channels[safe_frame_idx][0]).astype(np.float32)
            
            # Get visualizer and compute draw commands
            visualizer = get_visualizer(state.mode, viz_configs)
            viz_commands = visualizer(magnitudes, state.width, state.height)
            
            
            if viz_commands:
                viz_batches = viz_commands.batches
                bg_color = viz_commands.background
            else:
                viz_batches = ()
                bg_color = BLACK
            
            # Render button panel using standalone function
            button_batches = render_button_panel(state.button_panel, state.mode, ui_config)
            
            # Render timeline
            timeline_batches = render_timeline(state.timeline, state.current_time, ui_config)

            # Combine visualization and UI batches
            all_batches = viz_batches + tuple(button_batches) + tuple(timeline_batches)
            commands = FrameCommands(batches=all_batches, background=bg_color)
            
            # Calculate button label positions from config
            labels = calculate_label_positions(state_manager.button_specs, state.width, ui_config)
            
            # Add time labels
            time_labels = get_timeline_labels(state.timeline, state.current_time, ui_config)
            labels.extend(time_labels)
            
            # Render the frame with text
            render_frame(renderer, commands, labels, ui_config)
        
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

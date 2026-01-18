"""Application Controller.

This module contains the AppController which handles application logic,
events, and state transitions, separating decision-making from state storage.
"""

import time
from .state_manager import StateStore, VisualizationState
from .config import AppConfig

import ctypes
from ctypes import c_int, byref
from .ui import ButtonPanel

# Helper to load SDL for robust mouse polling
try:
    _sdl = ctypes.CDLL("/lib/x86_64-linux-gnu/libSDL2-2.0.so.0")
    # signature: UINT32 SDL_GetMouseState(int *x, int *y)
    _sdl.SDL_GetMouseState.argtypes = [ctypes.POINTER(c_int), ctypes.POINTER(c_int)]
    _sdl.SDL_GetMouseState.restype = ctypes.c_uint32
    _HAS_SDL = True
except Exception as e:
    print(f"Warning: Could not load SDL2 for mouse polling: {e}")
    _HAS_SDL = False

class AppController:
    """
    Manages application logic and updates the StateStore.
    """

    def __init__(self, state_store: StateStore, config: AppConfig):
        """
        Initialize the App Controller.

        Args:
            state_store: The state storage instance
            config: Application configuration
        """
        self._store = state_store
        self._config = config
        self._mode_order = [spec[0] for spec in config.button_specs]
        self._last_switch_time = time.time()

    def update(self, events: list[tuple[str, tuple[int, ...]]]) -> None:
        """
        Process events and time, updating the state in the store.

        Args:
            events: List of event tuples from renderer.poll_events()
        """
        current_state = self._store.state
        new_state = self._process_events(current_state, events)
        
        # Poll mouse directly for robust dragging
        if _HAS_SDL:
            new_state = self._poll_mouse(new_state)

        # Apply time-driven transitions if still running
        if new_state.is_running and new_state.auto_switch_interval is not None:
            current_time = time.time()
            if current_time - self._last_switch_time >= new_state.auto_switch_interval:
                new_state = self._switch_mode(new_state)

        # Update the store if state changed
        if new_state != current_state:
            self._store.state = new_state

    def _poll_mouse(self, state: VisualizationState) -> VisualizationState:
        """Poll SDL mouse state directly to handle dragging."""
        x = c_int(0)
        y = c_int(0)
        mask = _sdl.SDL_GetMouseState(byref(x), byref(y))
        
        # Left button is bit 0 (value 1)
        is_left_down = (mask & 1) != 0
        mx, my = x.value, y.value
        
        new_state = state
        
        if is_left_down:
            # Check if we clicked inside timeline (start drag) or are already dragging
            if state.timeline.hit_test(mx, my) or state.is_dragging:
                # Calculate progress
                progress = state.timeline.get_progress_at_x(mx)
                seek_time = progress * state.total_duration
                # Update state: dragging=True, request seek
                # This ensures the knob follows mouse and audio seeks continuously
                new_state = new_state.with_time(seek_time, is_dragging=True, seek_req=seek_time)
        else:
            # Mouse released
            if state.is_dragging:
                # Stop dragging
                 new_state = new_state.with_time(state.current_time, is_dragging=False, seek_req=None)
        
        return new_state

    def _process_events(self, state: VisualizationState, events: list[tuple[str, tuple[int, ...]]]) -> VisualizationState:
        """Calculate next state based on events."""
        new_state = state
        for event_type, params in events:
            match event_type:
                case "quit":
                    return new_state.stopped()
                
                case "resize":
                    if len(params) >= 2:
                        width, height = params[0], params[1]
                        # We need to recreate button panel on resize
                        labels = [spec[0] for spec in self._config.button_specs]
                        # Fix: Pass ui_config to with_size
                        new_state = new_state.with_size(width, height, labels, self._config.ui_config)
                
                case "keydown":
                    if len(params) >= 1:
                        key = params[0]
                        # Space bar to switch modes manually
                        if key == 32:  # SDLK_SPACE
                            new_state = self._switch_mode(new_state)
                        elif key == 27:  # SDLK_ESCAPE
                            return new_state.stopped()
                
                case "mousedown":
                    if len(params) >= 2:
                        x, y = params[0], params[1]
                        # Note: Timeline is now handled exclusively by _poll_mouse
                        # We only check buttons here
                        if not state.timeline.hit_test(x, y):
                            clicked_mode = state.button_panel.hit_test(x, y)
                            if clicked_mode:
                                clicked_mode = clicked_mode.lower()
                                if clicked_mode != state.mode:
                                    # Update last switch time when manually switching
                                    self._last_switch_time = time.time()
                                    print(f"Switched to mode: {clicked_mode}")
                                    new_state = new_state.with_mode(clicked_mode)
        return new_state

    def _switch_mode(self, state: VisualizationState) -> VisualizationState:
        """Switch to the next visualization mode."""
        new_mode = self._get_next_mode(state.mode)
        self._last_switch_time = time.time()
        print(f"Switched to mode: {new_mode}")
        return state.with_mode(new_mode)

    def _get_next_mode(self, current: str) -> str:
        """Calculate next mode using configured mode order."""
        modes = self._mode_order
        if not modes:
            return current
            
        try:
            # Check if current mode is in the list (it might be an alias or invalid)
            # If we want to support aliases here, we should resolve them first.
            # But based on previous refactor, we just cycle the list.
            idx = modes.index(current)
            return modes[(idx + 1) % len(modes)]
        except ValueError:
            return modes[0] if modes else "bars"

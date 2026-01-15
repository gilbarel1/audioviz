"""State management for the visualization application.

The state manager handles mode transitions, timing, and event processing.
It provides an immutable state object that drives the render loop.
"""

from dataclasses import dataclass
import time
from typing import Optional, TYPE_CHECKING
from .ui import ButtonPanel, create_button_panel
from .config import ButtonType, AppConfig, UIConfig




@dataclass(frozen=True, slots=True)
class StateManagerConfig:
    """Configuration for the StateManager."""
    initial_mode: str = "bars"
    width: int = 800
    height: int = 600
    auto_switch_interval: Optional[float] = 5.0
    button_specs: tuple[tuple[str, ButtonType], ...] = ()
    mode_order: tuple[str, ...] = ()  # Dynamic cycle order
    app_config: "AppConfig" = None
    ui_config: "UIConfig" = None 


@dataclass(frozen=True, slots=True)
class VisualizationState:
    """Immutable representation of the current visualization state."""
    mode: str
    width: int
    height: int
    button_panel: "ButtonPanel"
    auto_switch_interval: Optional[float] = 5.0
    is_running: bool = True
    
    def with_mode(self, new_mode: str) -> "VisualizationState":
        """Return a new state with the mode changed."""
        return VisualizationState(
            mode=new_mode,
            width=self.width,
            height=self.height,
            button_panel=self.button_panel,
            auto_switch_interval=self.auto_switch_interval,
            is_running=self.is_running
        )
    
    def with_size(self, width: int, height: int, labels: list[str]) -> "VisualizationState":
        """Return a new state with the size changed."""
        return VisualizationState(
            mode=self.mode,
            width=width,
            height=height,
            button_panel=create_button_panel(width, list(labels), self._ui_config),
            auto_switch_interval=self.auto_switch_interval,
            is_running=self.is_running
        )
    
    def stopped(self) -> "VisualizationState":
        """Return a new state that signals the app should stop."""
        return VisualizationState(
            mode=self.mode,
            width=self.width,
            height=self.height,
            button_panel=self.button_panel,
            auto_switch_interval=self.auto_switch_interval,
            is_running=False
        )


class StateManager:
    """
    Manages state transitions based on events and time.
    """
    
    def __init__(self, config: StateManagerConfig):
        """
        Initialize the State Manager.
        
        Args:
            config: Configuration object
        """
        self._state = VisualizationState(
            mode=config.initial_mode,
            width=config.width,
            height=config.height,
            button_panel=create_button_panel(config.width, list(config.button_specs), config.ui_config),
            auto_switch_interval=config.auto_switch_interval,
        )
        self._button_specs = list(config.button_specs)
        self._mode_order = config.mode_order
        self._app_config = config.app_config
        self._ui_config = config.ui_config
        self._last_switch_time = time.time()
    
    @property
    def state(self) -> VisualizationState:
        """Get the current state."""
        return self._state
    
    @property
    def button_specs(self) -> list[tuple[str, ButtonType]]:
        """Get the button specifications."""
        return self._button_specs
    
    def update(self, events: list[tuple[str, tuple[int, ...]]]) -> VisualizationState:
        """
        Process events and time, returning the new state.
        
        Args:
            events: List of event tuples from renderer.poll_events()
                   Each tuple: (event_type, params_tuple)
        
        Returns:
            The updated visualization state
        """
        # First, apply event-driven transitions
        self._state = self._process_events(self._state, events)
        
        # Then, apply time-driven transitions (if still running)
        if self._state.is_running and self._state.auto_switch_interval is not None:
            current_time = time.time()
            if current_time - self._last_switch_time >= self._state.auto_switch_interval:
                self._switch_mode()
        
        return self._state

    def _process_events(self, state: VisualizationState, events: list[tuple[str, tuple[int, ...]]]) -> VisualizationState:
        """Pure-ish function to calculate next state based on events.
        
        Args:
            events: List of (event_type, params) tuples
        """
        new_state = state
        for event_type, params in events:
            match event_type:
                case "quit":
                    return new_state.stopped()
                
                case "resize":
                    if len(params) >= 2:
                        width, height = params[0], params[1]
                        new_state = new_state.with_size(width, height, self._button_specs)
                
                case "keydown":
                    if len(params) >= 1:
                        key = params[0]
                        # Space bar to switch modes manually
                        if key == 32:  # SDLK_SPACE
                            self._switch_mode()
                            new_state = new_state.with_mode(self._state.mode)
                        elif key == 27:  # SDLK_ESCAPE
                            return new_state.stopped()
                
                case "mousedown":
                    if len(params) >= 2:
                        x, y = params[0], params[1]
                        clicked_mode = state.button_panel.hit_test(x, y)
                        if clicked_mode:
                            clicked_mode = clicked_mode.lower()
                            if clicked_mode != self._state.mode:
                                self._state = self._state.with_mode(clicked_mode)
                                self._last_switch_time = time.time()
                                print(f"Switched to mode: {clicked_mode}")
                                new_state = new_state.with_mode(clicked_mode)
        return new_state
    
    def _switch_mode(self) -> None:
        """Switch to the next visualization mode."""
        new_mode = self._get_next_mode(self._state.mode)
        self._state = self._state.with_mode(new_mode)
        self._last_switch_time = time.time()
        print(f"Switched to mode: {new_mode}")

    def _get_next_mode(self, current: str) -> str:
        """Calculate next mode using configured mode order."""
        modes = self._mode_order
        if not modes:
            return current
            
        try:
            # Handle aliases if necessary
            if current == "spectrum" and "multiband" in modes:
                 current = "multiband"
            elif current == "multiband" and "spectrum" in modes:
                 current = "spectrum"

            idx = modes.index(current)
            return modes[(idx + 1) % len(modes)]
        except ValueError:
            return modes[0] if modes else "bars"


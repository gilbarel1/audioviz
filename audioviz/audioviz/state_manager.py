"""State management for the visualization application.

The state manager handles mode transitions, timing, and event processing.
It provides an immutable state object that drives the render loop.
"""

from dataclasses import dataclass
import time
from typing import Optional, TYPE_CHECKING

from .visualizers import next_mode

if TYPE_CHECKING:
    from .ui import ButtonPanel


@dataclass(frozen=True, slots=True)
class StateManagerConfig:
    """Configuration for the StateManager."""
    initial_mode: str = "bars"
    width: int = 800
    height: int = 600
    auto_switch_interval: Optional[float] = 5.0


@dataclass(frozen=True, slots=True)
class VisualizationState:
    """Immutable representation of the current visualization state."""
    mode: str
    width: int
    height: int
    is_running: bool = True
    
    def with_mode(self, new_mode: str) -> "VisualizationState":
        """Return a new state with the mode changed."""
        return VisualizationState(
            mode=new_mode,
            width=self.width,
            height=self.height,
            is_running=self.is_running
        )
    
    def with_size(self, width: int, height: int) -> "VisualizationState":
        """Return a new state with the size changed."""
        return VisualizationState(
            mode=self.mode,
            width=width,
            height=height,
            is_running=self.is_running
        )
    
    def stopped(self) -> "VisualizationState":
        """Return a new state that signals the app should stop."""
        return VisualizationState(
            mode=self.mode,
            width=self.width,
            height=self.height,
            is_running=False
        )


class StateManager:
    """
    Manages state transitions based on events and time.
    """
    
    def __init__(self, config: StateManagerConfig = StateManagerConfig()):
        """
        Initialize the State Manager.
        
        Args:
            config: Configuration object
        """
        self._state = VisualizationState(
            mode=config.initial_mode,
            width=config.width,
            height=config.height,
        )
        self.auto_switch_interval = config.auto_switch_interval
        self._last_switch_time = time.time()
        self._button_panel: Optional["ButtonPanel"] = None
    
    def set_button_panel(self, panel: "ButtonPanel") -> None:
        """Set the button panel for click handling."""
        self._button_panel = panel
    
    @property
    def state(self) -> VisualizationState:
        """Get the current state."""
        return self._state
    
    def update(self, events: list[tuple[str, int, int]]) -> VisualizationState:
        """
        Process events and time, returning the new state.
        
        Args:
            events: List of (event_type, data1, data2) from renderer.poll_events()
        
        Returns:
            The updated visualization state
        """
        # First, apply event-driven transitions
        self._state = self._process_events(self._state, events)
        
        # Then, apply time-driven transitions (if still running)
        if self._state.is_running and self.auto_switch_interval is not None:
            current_time = time.time()
            if current_time - self._last_switch_time >= self.auto_switch_interval:
                self._switch_mode()
        
        return self._state

    def _process_events(self, state: VisualizationState, events: list[tuple[str, int, int]]) -> VisualizationState:
        """Pure-ish function to calculate next state based on events."""
        new_state = state
        for event_type, data1, data2 in events:
            if event_type == "quit":
                return new_state.stopped()
            
            elif event_type == "resize":
                new_state = new_state.with_size(data1, data2)
            
            elif event_type == "keydown":
                # Space bar to switch modes manually
                if data1 == 32:  # SDLK_SPACE
                    self._switch_mode()
                    new_state = new_state.with_mode(self._state.mode)
                elif data1 == 27:  # SDLK_ESCAPE
                    return new_state.stopped()
            elif event_type == "mousedown":
                # data1 = x, data2 = y
                if self._button_panel:
                    clicked_mode = self._button_panel.hit_test(data1, data2)
                    if clicked_mode and clicked_mode != self._state.mode:
                        self._state = self._state.with_mode(clicked_mode)
                        self._last_switch_time = time.time()
                        print(f"Switched to mode: {clicked_mode}")
                        new_state = new_state.with_mode(clicked_mode)
        return new_state
    
    def _switch_mode(self) -> None:
        """Switch to the next visualization mode."""
        new_mode = next_mode(self._state.mode)
        self._state = self._state.with_mode(new_mode)
        self._last_switch_time = time.time()
        print(f"Switched to mode: {new_mode}")

"""State management for the visualization application.

The state manager handles mode transitions, timing, and event processing.
It provides an immutable state object that drives the render loop.
"""

from dataclasses import dataclass
import time
from typing import Optional

from .visualizers import MODE_ORDER, next_mode


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
    
    def __init__(
        self, 
        initial_mode: str = "bars",
        width: int = 800,
        height: int = 600,
        auto_switch_interval: Optional[float] = 5.0,
    ):
        """
        Initialize the State Manager.
        
        Args:
            initial_mode: Starting visualization mode
            width: Initial window width
            height: Initial window height
            auto_switch_interval: Time in seconds between auto mode switches.
                                  Set to None to disable auto-switching.
        """
        self._state = VisualizationState(
            mode=initial_mode,
            width=width,
            height=height,
        )
        self.auto_switch_interval = auto_switch_interval
        self._last_switch_time = time.time()
    
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
        for event_type, data1, data2 in events:
            if event_type == "quit":
                self._state = self._state.stopped()
                return self._state
            
            elif event_type == "resize":
                self._state = self._state.with_size(data1, data2)
            
            elif event_type == "keydown":
                # Space bar to switch modes manually
                if data1 == 32:  # SDLK_SPACE
                    self._switch_mode()
                # Escape to quit
                elif data1 == 27:  # SDLK_ESCAPE
                    self._state = self._state.stopped()
                    return self._state
        
        # Auto-switch modes if enabled
        if self.auto_switch_interval is not None:
            current_time = time.time()
            if current_time - self._last_switch_time >= self.auto_switch_interval:
                self._switch_mode()
        
        return self._state
    
    def _switch_mode(self) -> None:
        """Switch to the next visualization mode."""
        new_mode = next_mode(self._state.mode)
        self._state = self._state.with_mode(new_mode)
        self._last_switch_time = time.time()
        print(f"Switched to mode: {new_mode}")

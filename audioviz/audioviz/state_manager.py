from enum import Enum
import time
from dataclasses import dataclass

class VisualMode(Enum):
    BARS = 0
    CIRCLE = 1
    SPIRAL = 2
    RAIN = 3

@dataclass(frozen=True)
class VisualizationState:
    """Immutable representation of the current visualization state."""
    mode: VisualMode
    
    @property
    def mode_id(self) -> int:
        return self.mode.value
        
    @property
    def name(self) -> str:
        return self.mode.name

class StateManager:
    """
    Manages the transitions and current state of the visualization.
    """
    
    def __init__(self, switch_interval: float = 5.0):
        """
        Initialize the State Manager.
        
        Args:
            switch_interval: Time in seconds between state switches.
        """
        self._current_mode = VisualMode.BARS
        self.switch_interval = switch_interval
        self.last_switch_time = time.time()
        
    @property
    def current_state(self) -> VisualizationState:
        """
        Returns the current visualization state, evolving it if the interval has passed.
        """
        current_time = time.time()
        if current_time - self.last_switch_time >= self.switch_interval:
            self._evolve()
            self.last_switch_time = current_time
            
        return VisualizationState(mode=self._current_mode)
        
    def _evolve(self):
        """Internal logic to cycle through available modes."""
        modes = list(VisualMode)
        current_index = modes.index(self._current_mode)
        next_index = (current_index + 1) % len(modes)
        self._current_mode = modes[next_index]
        print(f"Switched to state: {self._current_mode.name}")


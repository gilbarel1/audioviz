from enum import Enum, auto
import time

class VisualState(Enum):
    BARS = 0
    CIRCLE = 1
    SPIRAL = 2
    RAIN = 3

class StateManager:
    """
    Manages the state of the visualization.
    """
    
    def __init__(self, switch_interval: float = 5.0):
        """
        Initialize the State Manager.
        
        Args:
            switch_interval: Time in seconds between state switches.
        """
        self.current_state = VisualState.BARS
        self.switch_interval = switch_interval
        self.last_switch_time = time.time()
        
    def update(self) -> bool:
        """
        Update the state based on elapsed time.
        
        Returns:
            True if the state changed, False otherwise.
        """
        current_time = time.time()
        if current_time - self.last_switch_time >= self.switch_interval:
            self._next_state()
            self.last_switch_time = current_time
            return True
        return False
        
    def _next_state(self):
        """Switch to the next available state."""
        # Get all enum members as a list
        members = list(VisualState)
        # Find current index
        try:
            current_index = members.index(self.current_state)
        except ValueError:
             current_index = 0
             self.current_state = members[0]

        # Cycle to next logic
        next_index = (current_index + 1) % len(members)
        self.current_state = members[next_index]
        print(f"Switched to state: {self.current_state.name}")
        
    def get_current_state(self) -> int:
        """Get the current state ID (integer for C++ compatibility)."""
        # Return 0-based index corresponding to the Enum member
        return list(VisualState).index(self.current_state)
        
    def get_state_name(self, state_id: int) -> str:
        """Get human-readable name for a state ID."""
        try:
            return list(VisualState)[state_id].name
        except IndexError:
            return "UNKNOWN"

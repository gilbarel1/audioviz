"""State Manager for controlling visualization modes."""

import time

class StateManager:
    """
    Manages the state of the visualization.
    
    States:
        0: BARS (Default)
        1: CIRCLE
    """
    
    BARS = 0
    CIRCLE = 1
    
    def __init__(self, switch_interval: float = 5.0):
        """
        Initialize the State Manager.
        
        Args:
            switch_interval: Time in seconds between state switches.
        """
        self.current_state = self.BARS
        self.switch_interval = switch_interval
        self.last_switch_time = time.time()
        self.num_states = 2
        
    def update(self) -> bool:
        """
        Update the state based on elapsed time.
        
        Returns:
            True if the state changed, False otherwise.
        """
        current_time = time.time()
        if current_time - self.last_switch_time >= self.switch_interval:
            self.next_state()
            self.last_switch_time = current_time
            return True
        return False
        
    def next_state(self):
        """Switch to the next available state."""
        self.current_state = (self.current_state + 1) % self.num_states
        print(f"Switched to state: {self.get_state_name(self.current_state)}")
        
    def get_current_state(self) -> int:
        """Get the current state ID."""
        return self.current_state
        
    def get_state_name(self, state_id: int) -> str:
        """Get human-readable name for a state."""
        if state_id == self.BARS:
            return "BARS"
        elif state_id == self.CIRCLE:
            return "CIRCLE"
        return "UNKNOWN"

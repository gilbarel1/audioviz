"""State management for the visualization application.

This module provides the StateStore which holds the current state,
and the immutable VisualizationState data structure.
"""

from dataclasses import dataclass
from typing import Optional
from .ui import ButtonPanel, create_button_panel, Timeline, create_timeline
from .config import ButtonType, AppConfig, UIConfig


@dataclass(frozen=True, slots=True)
class StateStoreConfig:
    """Configuration for the StateStore."""
    initial_mode: str = "bars"
    width: int = 800
    height: int = 600
    total_duration: float = 0.0
    auto_switch_interval: Optional[float] = 5.0
    button_specs: tuple[tuple[str, ButtonType], ...] = ()
    mode_order: tuple[str, ...] = ()
    app_config: "AppConfig" = None
    ui_config: "UIConfig" = None 


@dataclass(frozen=True, slots=True)
class VisualizationState:
    """Immutable representation of the current visualization state."""
    mode: str
    width: int
    height: int
    button_panel: "ButtonPanel"
    timeline: "Timeline"
    current_time: float = 0.0
    total_duration: float = 0.0
    seek_request: Optional[float] = None
    is_dragging: bool = False
    auto_switch_interval: Optional[float] = 5.0
    is_running: bool = True
    
    def with_mode(self, new_mode: str) -> "VisualizationState":
        """Return a new state with the mode changed."""
        return VisualizationState(
            mode=new_mode,
            width=self.width,
            height=self.height,
            button_panel=self.button_panel,
            timeline=self.timeline,
            current_time=self.current_time,
            total_duration=self.total_duration,
            seek_request=self.seek_request,
            is_dragging=self.is_dragging,
            auto_switch_interval=self.auto_switch_interval,
            is_running=self.is_running
        )
    
    def with_size(self, width: int, height: int, button_specs: list[tuple[str, ButtonType]], ui_config: UIConfig) -> "VisualizationState":
        """Return a new state with the size changed."""
        # Cleanly recreate timeline and button panel on resize
        return VisualizationState(
            mode=self.mode,
            width=width,
            height=height,
            button_panel=create_button_panel(width, button_specs, ui_config),
            timeline=create_timeline(width, height, self.total_duration, ui_config),
            current_time=self.current_time,
            total_duration=self.total_duration,
            seek_request=self.seek_request,
            is_dragging=self.is_dragging,
            auto_switch_interval=self.auto_switch_interval,
            is_running=self.is_running
        )
    
    def with_time(self, time: float, is_dragging: bool = False, seek_req: Optional[float] = None) -> "VisualizationState":
        """Return a new state with updated time."""
        return VisualizationState(
            mode=self.mode,
            width=self.width,
            height=self.height,
            button_panel=self.button_panel,
            timeline=self.timeline,
            current_time=time,
            total_duration=self.total_duration,
            seek_request=seek_req,
            is_dragging=is_dragging, 
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
            timeline=self.timeline,
            current_time=self.current_time,
            total_duration=self.total_duration,
            seek_request=None,
            is_dragging=False,
            auto_switch_interval=self.auto_switch_interval,
            is_running=False
        )


class StateStore:
    """
    Holds the current state of the visualization.
    Only stores state; does not contain business logic.
    """
    
    def __init__(self, config: StateStoreConfig):
        """
        Initialize the State Store.
        
        Args:
            config: Configuration object
        """
        self._state = VisualizationState(
            mode=config.initial_mode,
            width=config.width,
            height=config.height,
            button_panel=create_button_panel(config.width, list(config.button_specs), config.ui_config),
            timeline=create_timeline(config.width, config.height, config.total_duration, config.ui_config),
            total_duration=config.total_duration,
            auto_switch_interval=config.auto_switch_interval,
        )
    
    @property
    def state(self) -> VisualizationState:
        """Get the current state."""
        return self._state
    
    @state.setter
    def state(self, new_state: VisualizationState) -> None:
        """Set the current state."""
        self._state = new_state

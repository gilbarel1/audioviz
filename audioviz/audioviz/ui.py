"""UI components for the visualization overlay.

This module provides button panel functionality for mode selection.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from .config import Rect, DrawBatch, FrameCommands, Color, WHITE, BLACK, Line, ButtonType, UIConfig



@dataclass(frozen=True, slots=True)
class Button:
    """A clickable button with bounds and label."""
    label: str
    x: int
    y: int
    width: int
    height: int
    type: ButtonType  # Button type must be explicitly specified
    
    def contains(self, px: int, py: int) -> bool:
        """Check if point (px, py) is inside this button."""
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)


class ButtonPanel:
    """A horizontal panel of buttons."""
    
    def __init__(self, buttons: list[Button]):
        """
        Create a button panel with pre-laid-out buttons.
        
        Args:
            buttons: List of Button objects with positions already calculated
        """
        self.buttons = buttons
    
    def hit_test(self, x: int, y: int) -> Optional[str]:
        """
        Test if a click at (x, y) hit any button.
        
        Returns:
            Mode name if a button was clicked, None otherwise
        """
        for button in self.buttons:
            if button.contains(x, y):
                return button.label
        return None
    



def render_button_panel(panel: ButtonPanel, current_mode: str, ui_config: UIConfig) -> list[DrawBatch]:
    """
    Render the button panel to draw batches.
    
    Args:
        panel: The ButtonPanel to render
        current_mode: The currently active mode (will be highlighted)
        
    Returns:
        List of DrawBatches to render
    """
    batches: list[DrawBatch] = []
    
    # Draw each button
    for button in panel.buttons:
        # Choose color based on whether this is the active mode
        if button.label.lower() == current_mode.lower():
            bg_color = ui_config.mode_button_active_color
        else:
            bg_color = ui_config.mode_button_bg_color

        
        # Button background
        rect = Rect(button.x, button.y, button.width, button.height)
        batches.append(DrawBatch.from_rects([rect], bg_color))
        
        
        border_lines = [
            # Top
            Line(button.x, button.y, button.x + button.width, button.y),
            # Bottom
            Line(button.x, button.y + button.height, 
                 button.x + button.width, button.y + button.height),
            # Left
            Line(button.x, button.y, button.x, button.y + button.height),
            # Right
            Line(button.x + button.width, button.y,
                 button.x + button.width, button.y + button.height),
        ]
        batches.append(DrawBatch.from_lines(border_lines, ui_config.mode_button_border_color))

    
    return batches


def calculate_label_positions(button_specs: list[tuple[str, ButtonType]], screen_width: int, ui_config: UIConfig) -> list[tuple[str, int, int]]:
    """Calculate text label positions for buttons without creating Button objects.
    
    Args:
        button_specs: List of (label, button_type) tuples
        screen_width: Width of the screen for centering
        
    Returns:
        List of (label, x, y) tuples for text rendering
    """
    labels = []
    
    # Calculate layout (same as _layout_buttons)
    num_buttons = len(button_specs)
    total_width = num_buttons * ui_config.mode_button_width + (num_buttons - 1) * ui_config.mode_button_padding
    start_x = (screen_width - total_width) // 2
    
    # Calculate text positions for each button
    for i, (label, button_type) in enumerate(button_specs):
        button_x = start_x + i * (ui_config.mode_button_width + ui_config.mode_button_padding)
        text_x = button_x + ui_config.mode_text_padding_x
        text_y = ui_config.mode_button_y_offset + (ui_config.mode_button_height - ui_config.mode_text_vertical_correction) // 2
        labels.append((label.capitalize(), text_x, text_y))
    
    return labels


def _layout_buttons(button_specs: list[tuple[str, ButtonType]], screen_width: int, ui_config: UIConfig) -> list[Button]:
    """Calculate button positions for horizontal layout.
    
    Args:
        button_specs: List of (label, button_type) tuples
        screen_width: Width of the screen for centering
        
    Returns:
        List of Button objects with calculated positions
    """
    buttons = []
    
    # Calculate layout
    num_buttons = len(button_specs)
    total_width = num_buttons * ui_config.mode_button_width + (num_buttons - 1) * ui_config.mode_button_padding
    start_x = (screen_width - total_width) // 2
    
    # Create positioned buttons
    for i, (label, button_type) in enumerate(button_specs):
        x = start_x + i * (ui_config.mode_button_width + ui_config.mode_button_padding)
        buttons.append(Button(
            label=label.capitalize(),
            x=x,
            y=ui_config.mode_button_y_offset,
            width=ui_config.mode_button_width,
            height=ui_config.mode_button_height,
            type=button_type
        ))
    
    return buttons


def create_button_panel(screen_width: int, button_specs: list[tuple[str, ButtonType]], ui_config: UIConfig) -> ButtonPanel:
    """Factory function to create a button panel.
    
    Args:
        screen_width: Width of the screen for centering buttons
        button_specs: List of (label, button_type) tuples
        
    Returns:
        ButtonPanel with buttons laid out horizontally
    """
    buttons = _layout_buttons(button_specs, screen_width, ui_config)
    return ButtonPanel(buttons)

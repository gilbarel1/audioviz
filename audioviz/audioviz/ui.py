"""UI components for the visualization overlay.

This module provides button panel functionality for mode selection.
"""

from dataclasses import dataclass
from typing import Optional

from .config import Rect, DrawBatch, FrameCommands, Color, WHITE, BLACK, Line
from .config import UI


@dataclass(frozen=True, slots=True)
class Button:
    """A clickable button with bounds and label."""
    label: str
    x: int
    y: int
    width: int
    height: int
    
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
    
    def render(self, current_mode: str) -> list[DrawBatch]:
        """
        Render the button panel.
        
        Args:
            current_mode: The currently active mode (will be highlighted)
            
        Returns:
            List of DrawBatches to render
        """
        batches: list[DrawBatch] = []
        
        # Draw each button
        for button in self.buttons:
            # Choose color based on whether this is the active mode
            if button.label.lower() == current_mode.lower():
                bg_color = UI.button_active_color
            else:
                bg_color = UI.button_bg_color

            
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
            batches.append(DrawBatch.from_lines(border_lines, UI.button_border_color))

        
        return batches
    
    def get_labels(self) -> list[tuple[str, int, int]]:
        """
        Get button labels with their positions for text rendering.
        
        Returns:
            List of (label, x, y) tuples for text centering
        """
        labels = []
        for button in self.buttons:
            # Center text in button
            text_x = button.x + UI.text_padding_x
            text_y = button.y + (button.height - UI.text_vertical_correction) // 2

            labels.append((button.label, text_x, text_y))
        return labels


def _layout_buttons(button_labels: list[str], screen_width: int) -> list[Button]:
    """Calculate button positions for horizontal layout.
    
    Args:
        button_labels: List of button label strings
        screen_width: Width of the screen for centering
        
    Returns:
        List of Button objects with calculated positions
    """
    buttons = []
    
    # Calculate layout
    num_buttons = len(button_labels)
    total_width = num_buttons * UI.button_width + (num_buttons - 1) * UI.button_padding
    start_x = (screen_width - total_width) // 2
    
    # Create positioned buttons
    for i, label in enumerate(button_labels):
        x = start_x + i * (UI.button_width + UI.button_padding)
        buttons.append(Button(
            label=label.capitalize(),
            x=x,
            y=UI.button_y_offset,
            width=UI.button_width,
            height=UI.button_height
        ))
    
    return buttons


def create_button_panel(screen_width: int) -> ButtonPanel:
    """Factory function to create a button panel with configured labels.
    
    Args:
        screen_width: Width of the screen for centering buttons
        
    Returns:
        ButtonPanel with buttons laid out horizontally
    """
    buttons = _layout_buttons(list(UI.button_labels), screen_width)
    return ButtonPanel(buttons)

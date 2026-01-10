"""UI components for the visualization overlay.

This module provides button panel functionality for mode selection.
"""

from dataclasses import dataclass
from typing import Optional

from .primitives import Rect, DrawBatch, FrameCommands, Color, WHITE, BLACK
from .visualizers import MODE_ORDER


# Button styling
BUTTON_HEIGHT = 45
BUTTON_PADDING = 8
BUTTON_BG = Color(40, 40, 40, 220)
BUTTON_HOVER = Color(60, 60, 60, 220)
BUTTON_ACTIVE = Color(80, 120, 200, 220)
BUTTON_BORDER = Color(100, 100, 100, 255)


@dataclass(frozen=True, slots=True)
class Button:
    """A clickable button with bounds and associated mode."""
    label: str
    mode: str
    x: int
    y: int
    width: int
    height: int
    
    def contains(self, px: int, py: int) -> bool:
        """Check if point (px, py) is inside this button."""
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)


class ButtonPanel:
    """A horizontal panel of mode selection buttons."""
    
    def __init__(self, modes: list[str], screen_width: int, y_offset: int = 10):
        """
        Create a button panel for the given modes.
        
        Args:
            modes: List of mode names to create buttons for
            screen_width: Width of the screen for layout
            y_offset: Distance from top of screen
        """
        self.modes = modes
        self.y_offset = y_offset
        self.buttons: list[Button] = []
        self._layout(screen_width)
    
    def _layout(self, screen_width: int) -> None:
        """Calculate button positions."""
        self.buttons = []
        
        # Calculate button width based on mode name length
        button_width = 110
        total_width = len(self.modes) * button_width + (len(self.modes) - 1) * BUTTON_PADDING
        start_x = (screen_width - total_width) // 2
        
        for i, mode in enumerate(self.modes):
            x = start_x + i * (button_width + BUTTON_PADDING)
            self.buttons.append(Button(
                label=mode.capitalize(),
                mode=mode,
                x=x,
                y=self.y_offset,
                width=button_width,
                height=BUTTON_HEIGHT
            ))
    
    def update_layout(self, screen_width: int) -> None:
        """Recalculate layout when screen size changes."""
        self._layout(screen_width)
    
    def hit_test(self, x: int, y: int) -> Optional[str]:
        """
        Test if a click at (x, y) hit any button.
        
        Returns:
            Mode name if a button was clicked, None otherwise
        """
        for button in self.buttons:
            if button.contains(x, y):
                return button.mode
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
            if button.mode == current_mode:
                bg_color = BUTTON_ACTIVE
            else:
                bg_color = BUTTON_BG
            
            # Button background
            rect = Rect(button.x, button.y, button.width, button.height)
            batches.append(DrawBatch.from_rects([rect], bg_color))
            
            # Button border (draw as 4 lines)
            from .primitives import Line
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
            batches.append(DrawBatch.from_lines(border_lines, BUTTON_BORDER))
        
        return batches
    
    def get_labels(self) -> list[tuple[str, int, int]]:
        """
        Get button labels with their positions for text rendering.
        
        Returns:
            List of (label, x, y) tuples for text centering
        """
        labels = []
        for button in self.buttons:
            # Center text in button (approximate - actual centering depends on font metrics)
            text_x = button.x + 10  # Left padding
            text_y = button.y + (button.height - 16) // 2  # Vertical center (font size ~16)
            labels.append((button.label, text_x, text_y))
        return labels


def create_button_panel(screen_width: int) -> ButtonPanel:
    """Factory function to create a button panel with all modes."""
    return ButtonPanel(MODE_ORDER, screen_width)

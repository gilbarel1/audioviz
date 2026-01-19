"""UI components for the visualization overlay.

This module provides button panel functionality for mode selection.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol,Optional
import math

from .config import Rect, DrawBatch, FrameCommands, Color, WHITE, BLACK, Line, ButtonType, UIConfig

class UIController(Protocol):
    def hit_test(self, x: int, y: int) -> Optional[str]:
        """Test if a click at (x, y) hit any button."""
        ...

@dataclass(frozen=True, slots=True)
class Timeline:
    """Audio playback timeline/scroller."""
    x: int
    y: int
    width: int
    height: int
    total_duration: float
    
    def hit_test(self, px: int, py: int) -> bool:
        """Check if point is within the timeline interaction area."""
        return (self.x <= px < self.x + self.width and 
                self.y <= py < self.y + self.height)

    def get_progress_at_x(self, px: int) -> float:
        """Calculate progress (0.0-1.0) for a given X coordinate."""
        if self.width <= 0:
            return 0.0
        relative_x = px - self.x
        return max(0.0, min(1.0, relative_x / self.width))

@dataclass(frozen=True, slots=True)
class Button:
    """A clickable button with bounds and label."""
    label: str
    x: int
    y: int
    width: int
    height: int
    type: ButtonType  # Button type must be explicitly specified
    
    def hit_test(self, px: int, py: int) -> Optional[str]:
        """Check if point (px, py) is inside this button."""
        if self.x <= px < self.x + self.width and self.y <= py < self.y + self.height:
                return self.label
        return None


class ButtonPanel:
    """A horizontal panel of buttons."""
    
    def __init__(self, buttons: list[UIController]):
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
            if result := button.hit_test(x, y):
                return result
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


def create_playback_ui(screen_width: int, screen_height: int, duration: float, is_paused: bool, ui_config: UIConfig) -> tuple[Button, Timeline]:
    """Create the playback controls (Play/Pause button + Timeline)."""
    
    # Button positioned at bottom left
    btn_height = ui_config.timeline_height
    btn_y = screen_height - btn_height - ui_config.timeline_padding_bottom
    btn_x = ui_config.timeline_padding_x
    
    play_button = Button(
        label="Play" if is_paused else "Pause",
        x=btn_x,
        y=btn_y,
        width=ui_config.play_button_width,
        height=btn_height,
        type=ButtonType.ACTION
    )
    
    # Timeline positioned after button
    timeline_x = btn_x + ui_config.play_button_width + 10
    timeline_width = screen_width - timeline_x - ui_config.timeline_padding_x
    
    timeline = Timeline(
        x=timeline_x,
        y=btn_y,
        width=timeline_width,
        height=btn_height,
        total_duration=duration
    )
    
    return play_button, timeline


def create_timeline(screen_width: int, screen_height: int, duration: float, ui_config: UIConfig) -> Timeline:
    """Factory function to create a timeline positioned at the bottom."""
    width = screen_width - (2 * ui_config.timeline_padding_x)
    height = ui_config.timeline_height
    x = ui_config.timeline_padding_x
    y = screen_height - height - ui_config.timeline_padding_bottom
    
    return Timeline(x, y, width, height, duration)


def render_timeline(timeline: Timeline, current_time: float, ui_config: UIConfig) -> list[DrawBatch]:
    """Render the timeline, progress bar, and knob."""
    batches: list[DrawBatch] = []
    
    # Calculate progress
    progress = 0.0
    if timeline.total_duration > 0:
        progress = max(0.0, min(1.0, current_time / timeline.total_duration))
    
    # Background bar
    bar_height = 4
    bar_y = timeline.y + (timeline.height - bar_height) // 2
    
    bg_rect = Rect(timeline.x, bar_y, timeline.width, bar_height)
    batches.append(DrawBatch.from_rects([bg_rect], ui_config.timeline_bar_color))
    
    # Progress bar
    progress_width = int(timeline.width * progress)
    if progress_width > 0:
        prog_rect = Rect(timeline.x, bar_y, progress_width, bar_height)
        batches.append(DrawBatch.from_rects([prog_rect], ui_config.timeline_progress_color))
    
    # Knob
    knob_x = timeline.x + progress_width
    knob_y = bar_y + bar_height // 2
    
    # Draw simple square knob
    r = ui_config.timeline_knob_radius
    knob_rect = Rect(knob_x - r, knob_y - r, r * 2, r * 2)
    batches.append(DrawBatch.from_rects([knob_rect], ui_config.timeline_knob_color))
    
    return batches

def get_timeline_labels(timeline: Timeline, current_time: float, ui_config: UIConfig) -> list[tuple[str, int, int]]:
    """Get text labels for current time and total duration."""
    def format_time(seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
        
    labels = []
    y = timeline.y + timeline.height  # Below the bar
    
    # Current time (left aligned)
    labels.append((format_time(current_time), timeline.x, y))
    
    # Total duration (right aligned - approx width of text subtracted)
    # Since we can't measure text width easily here, we'll shift left by constant
    total_str = format_time(timeline.total_duration)
    labels.append((total_str, timeline.x + timeline.width - 50, y))
    
    return labels
    return labels


def _draw_circle_filled(x: int, y: int, radius: int, color: Color) -> DrawBatch:
    """Draw a filled circle using horizontal lines (Rectangle primitives)."""
    rects = []
    # Simple rasterization
    for dy in range(-radius, radius + 1):
        dx = int(math.sqrt(radius*radius - dy*dy))
        if dx > 0:
            rects.append(Rect(x - dx, y + dy, dx * 2, 1))
    return DrawBatch.from_rects(rects, color)

def _draw_play_icon(x: int, y: int, size: int, color: Color) -> DrawBatch:
    """Draw a play triangle using lines."""
    # Vertices of triangle
    x1, y1 = x - size // 2, y - size // 2
    x2, y2 = x - size // 2, y + size // 2
    x3, y3 = x + size // 2, y

    rects = []
    # Scanline fill triangle
    width = 0
    start_y = y - size // 2
    end_y = y + size // 2

    
    # Fill Triangle:
    half_size = size // 2
    for i in range(size + 1):
        curr_y = y - half_size + i
        ny = (i - half_size) / half_size
        
        
        # Let's do simple scanlines
        if curr_y < y:
             pass

    lines = []
    
    # Draw outline
    lines.append(Line(x1, y1, x2, y2)) 
    lines.append(Line(x2, y2, x3, y3)) 
    lines.append(Line(x3, y3, x1, y1)) 
    
    # Fill with horizontal lines
    for i in range(1, size // 2):
        offset = i 
        pass

    rects = []
    h = size
    w = size

    left_x = x - w // 4  
    apex_x = x + w // 2 - w // 4
    
    
    for r in range(h):
        dy = r - h // 2
        pass
        
    x_min = x - size // 3
    x_max = x + size // 2
    y_center = y
    half_h = size // 2
    
    rect_lines = []
    for cx in range(x_min, x_max):
        progress = (cx - x_min) / (x_max - x_min)
        
        curr_half_h = int(half_h * (1 - progress))
        if curr_half_h > 0:
            rect_lines.append(Rect(cx, y - curr_half_h, 1, curr_half_h * 2))
            
    return DrawBatch.from_rects(rect_lines, color)


def _draw_pause_icon(x: int, y: int, size: int, color: Color) -> DrawBatch:
    """Draw pause bars."""
    bar_width = max(3, size // 3)
    bar_height = size
    gap = max(2, size // 3)
    
    # Left bar
    r1 = Rect(x - gap//2 - bar_width, y - bar_height//2, bar_width, bar_height)
    # Right bar
    r2 = Rect(x + gap//2, y - bar_height//2, bar_width, bar_height)
    
    return DrawBatch.from_rects([r1, r2], color)


def render_play_button(button: Button, is_paused: bool, ui_config: UIConfig) -> list[DrawBatch]:
    """Render the play/pause button."""
    batches: list[DrawBatch] = []
    
    # Center coordinates
    cx = button.x + button.width // 2
    cy = button.y + button.height // 2
    radius = min(button.width, button.height) // 2

    bg_color = ui_config.mode_button_bg_color
    circle_batch = _draw_circle_filled(cx, cy, radius, bg_color)
    batches.append(circle_batch)
    
    icon_size = int(radius * 0.9)
    icon_color = WHITE
    
    if is_paused:

        batches.append(_draw_play_icon(cx, cy, icon_size, icon_color))
    else:
        batches.append(_draw_pause_icon(cx, cy, icon_size, icon_color))
    
    return batches

def get_play_button_label(button: Button, is_paused: bool, ui_config: UIConfig) -> tuple[str, int, int]:
    """Get label position for play button."""
    # No text label for icon-based button
    return ("", 0, 0)

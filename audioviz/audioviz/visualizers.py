"""Visualization functions that transform audio data into draw commands.

Each visualizer takes frequency magnitudes and window dimensions, 
returning FrameCommands that the renderer will draw.
"""

from typing import Callable, Protocol
import numpy as np
import math

from .primitives import (
    Rect, Line, DrawBatch, FrameCommands, Color,
    GREEN, CYAN
)


class Visualizer(Protocol):
    """Protocol for visualizer functions."""
    def __call__(
        self, 
        magnitudes: np.ndarray, 
        width: int, 
        height: int
    ) -> FrameCommands:
        ...


BAR_SCALE = 0.9  # Scale factor for normalized log magnitudes (0-1 range)
BAR_DB_FLOOR = -60.0  # Fixed floor in dB (quietest visible level)
BAR_DB_CEILING = -10.0  # Fixed ceiling in dB (loudest expected level)


def bars_visualizer(
    magnitudes: np.ndarray, 
    width: int, 
    height: int,
    color: Color = GREEN,
    scale: float = BAR_SCALE,
    mirror: bool = True,
    log_scale: bool = True,
    db_floor: float = BAR_DB_FLOOR,
    db_ceiling: float = BAR_DB_CEILING,
) -> FrameCommands:
    """
    Classic bar visualization - vertical bars representing frequency magnitudes.
    
    Args:
        magnitudes: Frequency magnitude array
        width: Window width in pixels
        height: Window height in pixels
        color: Bar color
        scale: Magnitude scaling factor (multiplier for normalized values)
        mirror: If True, draw mirrored bars from center
        log_scale: If True, use logarithmic (dB) scaling for more balanced display
        db_floor: Fixed floor in dB (values below this show as 0 height)
        db_ceiling: Fixed ceiling in dB (values above this clip to max height)
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(color))
    
    # Apply logarithmic scaling to compress dynamic range
    if log_scale:
        eps = 1e-10
        db_values = 20.0 * np.log10(magnitudes + eps)
        
        # Normalize using fixed floor/ceiling so bars move with actual loudness
        db_range = db_ceiling - db_floor
        normalized = (db_values - db_floor) / db_range
        normalized = np.clip(normalized, 0.0, 1.0)
        processed_mags = normalized
    else:
        # Linear scaling fallback - normalize to a fixed max
        fixed_max = 0.1
        processed_mags = np.clip(magnitudes / fixed_max, 0.0, 1.0)
    
    rects: list[Rect] = []
    
    if mirror:
        bar_width = max(1, width // (size * 2))
        center_x = width // 2
        
        for i, mag in enumerate(processed_mags):
            bar_height = min(int(mag * scale * height), height)
            y = height - bar_height
            
            # Right side
            rects.append(Rect(
                x=center_x + i * bar_width,
                y=y,
                width=bar_width,
                height=bar_height
            ))
            # Left side (mirror)
            left_x = center_x - (i + 1) * bar_width
            if left_x >= 0:
                rects.append(Rect(
                    x=left_x,
                    y=y,
                    width=bar_width,
                    height=bar_height
                ))
            else:
                # Trim valid width if partially off-screen
                adjusted_width = bar_width + left_x # left_x is negative
                if adjusted_width > 0:
                    rects.append(Rect(
                        x=0,
                        y=y,
                        width=adjusted_width,
                        height=bar_height
                    ))
    else:
        bar_width = max(1, width // size)
        for i, mag in enumerate(processed_mags):
            bar_height = min(int(mag * scale * height), height)
            rects.append(Rect(
                x=i * bar_width,
                y=height - bar_height,
                width=bar_width,
                height=bar_height
            ))
    
    batch = DrawBatch.from_rects(rects, color)
    return FrameCommands.single_batch(batch)


CIRCLE_SCALE = 3000.0
BASE_RADIUS_RATIO = 0.2


def circle_visualizer(
    magnitudes: np.ndarray,
    width: int,
    height: int,
    color: Color = CYAN,
    scale: float = CIRCLE_SCALE,
    base_radius_ratio: float = BASE_RADIUS_RATIO,
    mirror: bool = True,
) -> FrameCommands:
    """
    Radial visualization - lines emanating from a central circle.
    
    Args:
        magnitudes: Frequency magnitude array
        width: Window width in pixels
        height: Window height in pixels
        color: Line color
        scale: Magnitude scaling factor
        base_radius_ratio: Inner circle radius as fraction of max radius
        mirror: If True, mirror lines across horizontal axis
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(color))
    
    center_x = width // 2
    center_y = height // 2
    max_radius = min(width, height) / 2.0
    base_radius = max_radius * base_radius_ratio
    
    lines: list[Line] = []
    angle_step = 2.0 * math.pi / size
    
    for i, mag in enumerate(magnitudes):
        line_len = min(mag * scale, max_radius - base_radius)
        angle = i * angle_step
        
        # Start point on base circle
        x1 = int(center_x + math.cos(angle) * base_radius)
        y1 = int(center_y + math.sin(angle) * base_radius)
        
        # End point
        x2 = int(center_x + math.cos(angle) * (base_radius + line_len))
        y2 = int(center_y + math.sin(angle) * (base_radius + line_len))
        
        lines.append(Line(x1, y1, x2, y2))
        
        if mirror:
            is_zero_angle = (i == 0)
            is_pi_angle = (size % 2 == 0 and i == size // 2)
            
            if not(is_zero_angle or is_pi_angle):
                # Mirror across horizontal axis
                angle_mirror = -angle
                x1m = int(center_x + math.cos(angle_mirror) * base_radius)
                y1m = int(center_y + math.sin(angle_mirror) * base_radius)
                x2m = int(center_x + math.cos(angle_mirror) * (base_radius + line_len))
                y2m = int(center_y + math.sin(angle_mirror) * (base_radius + line_len))
                lines.append(Line(x1m, y1m, x2m, y2m))
    
    batch = DrawBatch.from_lines(lines, color)
    return FrameCommands.single_batch(batch)


# Registry of available visualizers - easy to extend
VISUALIZERS: dict[str, Visualizer] = {
    "bars": bars_visualizer,
    "circle": circle_visualizer,
}

# Ordered list for cycling through modes
MODE_ORDER = list(VISUALIZERS.keys())


def get_visualizer(name: str) -> Visualizer:
    """Get a visualizer by name, with a fallback to bars."""
    return VISUALIZERS.get(name, bars_visualizer)


def next_mode(current: str) -> str:
    """Get the next mode in the cycle."""
    try:
        idx = MODE_ORDER.index(current)
        return MODE_ORDER[(idx + 1) % len(MODE_ORDER)]
    except ValueError:
        return MODE_ORDER[0]

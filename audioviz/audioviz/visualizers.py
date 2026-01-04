"""Visualization functions that transform audio data into draw commands.

Each visualizer takes frequency magnitudes and window dimensions, 
returning FrameCommands that the renderer will draw.
"""

from typing import Callable, Protocol
import numpy as np
import math

from .primitives import (
    Rect, Line, DrawBatch, FrameCommands, Color,
    GREEN, CYAN, BLACK
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


def bars_visualizer(
    magnitudes: np.ndarray, 
    width: int, 
    height: int,
    color: Color = GREEN,
    scale: float = 5000.0,
    mirror: bool = True,
) -> FrameCommands:
    """
    Classic bar visualization - vertical bars representing frequency magnitudes.
    
    Args:
        magnitudes: Frequency magnitude array
        width: Window width in pixels
        height: Window height in pixels
        color: Bar color
        scale: Magnitude scaling factor
        mirror: If True, draw mirrored bars from center
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(color))
    
    rects: list[Rect] = []
    
    if mirror:
        bar_width = max(1, width // (size * 2))
        center_x = width // 2
        
        for i, mag in enumerate(magnitudes):
            bar_height = min(int(mag * scale), height)
            y = height - bar_height
            
            # Right side
            rects.append(Rect(
                x=center_x + i * bar_width,
                y=y,
                width=bar_width,
                height=bar_height
            ))
            # Left side (mirror)
            rects.append(Rect(
                x=center_x - (i + 1) * bar_width,
                y=y,
                width=bar_width,
                height=bar_height
            ))
    else:
        bar_width = max(1, width // size)
        for i, mag in enumerate(magnitudes):
            bar_height = min(int(mag * scale), height)
            rects.append(Rect(
                x=i * bar_width,
                y=height - bar_height,
                width=bar_width,
                height=bar_height
            ))
    
    batch = DrawBatch.from_rects(rects, color)
    return FrameCommands.single_batch(batch)


def circle_visualizer(
    magnitudes: np.ndarray,
    width: int,
    height: int,
    color: Color = CYAN,
    scale: float = 3000.0,
    base_radius_ratio: float = 0.2,
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

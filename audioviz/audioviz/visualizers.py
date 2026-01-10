"""Visualization functions that transform audio data into draw commands.

Each visualizer takes frequency magnitudes and window dimensions, 
returning FrameCommands that the renderer will draw.
"""

from typing import Callable, Protocol
import numpy as np
import math

from .primitives import (
    Rect, Line, DrawBatch, FrameCommands, Color,
    GREEN, CYAN, YELLOW, PURPLE, RED, BLUE, ORANGE, MAGENTA
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


# ============================================================================
# WAVEFORM VISUALIZER - Oscilloscope-style horizontal wave
# ============================================================================

WAVEFORM_SCALE = 0.7  # Vertical amplitude as fraction of height


def waveform_visualizer(
    magnitudes: np.ndarray,
    width: int,
    height: int,
    color: Color = YELLOW,
    scale: float = WAVEFORM_SCALE,
) -> FrameCommands:
    """
    Oscilloscope-style waveform - lines connecting frequency bins as a wave.
    Mirrored from center like bars visualizer.
    
    Args:
        magnitudes: Frequency magnitude array
        width: Window width in pixels
        height: Window height in pixels
        color: Line color
        scale: Vertical amplitude as fraction of height
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(color))
    
    center_x = width // 2
    center_y = height // 2
    max_amplitude = height * scale / 2
    
    # Normalize magnitudes
    max_mag = np.max(magnitudes) if np.max(magnitudes) > 0 else 1.0
    normalized = magnitudes / max_mag
    
    # Subsample for wider wave segments (use every Nth point)
    subsample = 4
    sampled = normalized[::subsample]
    num_points = len(sampled)
    
    lines: list[Line] = []
    # Each half gets half the width
    x_step = (width // 2) / num_points if num_points > 1 else width // 2
    
    for i in range(num_points - 1):
        # Right side (from center going right)
        x1_right = int(center_x + i * x_step)
        x2_right = int(center_x + (i + 1) * x_step)
        y1 = int(center_y - sampled[i] * max_amplitude)
        y2 = int(center_y - sampled[i + 1] * max_amplitude)
        lines.append(Line(x1_right, y1, x2_right, y2))
        
        # Mirror below center (right side)
        y1_mirror = int(center_y + sampled[i] * max_amplitude)
        y2_mirror = int(center_y + sampled[i + 1] * max_amplitude)
        lines.append(Line(x1_right, y1_mirror, x2_right, y2_mirror))
        
        # Left side (from center going left - mirror)
        x1_left = int(center_x - i * x_step)
        x2_left = int(center_x - (i + 1) * x_step)
        lines.append(Line(x1_left, y1, x2_left, y2))
        lines.append(Line(x1_left, y1_mirror, x2_left, y2_mirror))
    
    batch = DrawBatch.from_lines(lines, color)
    return FrameCommands.single_batch(batch)


# ============================================================================
# SPECTRUM VISUALIZER - Multi-band frequency display with colors
# ============================================================================

SPECTRUM_SCALE = 0.85

# Band colors: sub-bass, bass, mids, high-mids, highs
BAND_COLORS = [
    Color(255, 50, 50),    # Red - sub-bass
    Color(255, 150, 0),    # Orange - bass
    Color(255, 255, 0),    # Yellow - low-mids
    Color(0, 255, 100),    # Green - mids
    Color(0, 200, 255),    # Cyan - high-mids
    Color(150, 100, 255),  # Purple - highs
]


def multiband_visualizer(
    magnitudes: np.ndarray,
    width: int,
    height: int,
    scale: float = SPECTRUM_SCALE,
    db_floor: float = BAR_DB_FLOOR,
    db_ceiling: float = BAR_DB_CEILING,
) -> FrameCommands:
    """
    Multi-band spectrum analyzer - many thin bars colored by frequency band.
    
    Bands: Sub-bass (red), Bass (orange), Low-mids (yellow), 
           Mids (green), High-mids (cyan), Highs (purple)
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(BAND_COLORS[0]))
    
    # Apply dB scaling to all magnitudes
    eps = 1e-10
    db_values = 20.0 * np.log10(magnitudes + eps)
    normalized = (db_values - db_floor) / (db_ceiling - db_floor)
    normalized = np.clip(normalized, 0.0, 1.0)
    
    # Define frequency band ranges (as fractions of the spectrum)
    band_ranges = [
        (0, size // 16),           # Sub-bass (0-6%)
        (size // 16, size // 8),   # Bass (6-12%)
        (size // 8, size // 4),    # Low-mids (12-25%)
        (size // 4, size // 2),    # Mids (25-50%)
        (size // 2, 3 * size // 4),# High-mids (50-75%)
        (3 * size // 4, size),     # Highs (75-100%)
    ]
    
    # Subsample for wider bars (use every 2nd bin)
    subsample = 2
    sampled = normalized[::subsample]
    num_bars = len(sampled)
    
    # Calculate bar layout
    center_x = width // 2
    bar_width = max(2, (width // 2) // num_bars)
    gap = max(1, bar_width // 4)
    actual_bar_width = max(1, bar_width - gap)
    
    # Create one batch per color band
    batches: list[DrawBatch] = []
    
    for band_idx, (start, end) in enumerate(band_ranges):
        color = BAND_COLORS[band_idx]
        rects: list[Rect] = []
        
        # Convert band range to subsampled indices
        sub_start = start // subsample
        sub_end = end // subsample
        
        for i in range(sub_start, min(sub_end, num_bars)):
            mag = sampled[i]
            bar_height = max(1, int(mag * scale * height))
            
            # Right side
            x_right = center_x + i * bar_width
            rects.append(Rect(
                x=x_right,
                y=height - bar_height,
                width=actual_bar_width,
                height=bar_height
            ))
            
            # Left side (mirror)
            x_left = center_x - (i + 1) * bar_width
            if x_left >= 0:
                rects.append(Rect(
                    x=x_left,
                    y=height - bar_height,
                    width=actual_bar_width,
                    height=bar_height
                ))
        
        if rects:
            batches.append(DrawBatch.from_rects(rects, color))
    
    return FrameCommands(batches=tuple(batches))


# ============================================================================
# PARTICLES VISUALIZER - Reactive starfield effect
# ============================================================================

PARTICLE_COUNT = 200


def particles_visualizer(
    magnitudes: np.ndarray,
    width: int,
    height: int,
    color: Color = MAGENTA,
    particle_count: int = PARTICLE_COUNT,
) -> FrameCommands:
    """
    Particle starfield - dots that scatter based on audio energy.
    
    Args:
        magnitudes: Frequency magnitude array
        width: Window width in pixels
        height: Window height in pixels
        color: Particle color
        particle_count: Number of particles to render
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(color))
    
    # Calculate overall energy (emphasize bass frequencies)
    bass_weight = np.linspace(2.0, 0.5, size)
    weighted_mags = magnitudes * bass_weight
    energy = np.mean(weighted_mags) * 3000
    energy = min(energy, 1.0)
    
    # Pre-calculate dB values for all magnitudes to use for particle movement
    eps = 1e-10
    db_floor = -60.0
    db_ceiling = -10.0
    db_values = 20.0 * np.log10(magnitudes + eps)
    normalized_mags = (db_values - db_floor) / (db_ceiling - db_floor)
    normalized_mags = np.clip(normalized_mags, 0.0, 1.0)
    
    rects: list[Rect] = []
    
    # Use magnitude values to seed positions deterministically
    for i in range(particle_count):
        # Use modular indexing into magnitudes for variety
        # Bias towards lower frequencies where more action usually happens
        mag_idx = int((i % size) * (0.5 + 0.5 * (i / particle_count))) % size
        mag = normalized_mags[mag_idx]
        
        # Deterministic but varied positioning based on index and magnitude
        angle = (i * 2.399) % (2 * math.pi)  # Golden angle
        base_radius = (i / particle_count) * min(width, height) * 0.45
        
        # Magnitude affects radial offset - increased multiplier
        radius_offset = mag * 300 * energy
        radius = base_radius + radius_offset
        
        center_x = width // 2
        center_y = height // 2
        
        x = int(center_x + math.cos(angle) * radius)
        y = int(center_y + math.sin(angle) * radius)
        
        # Particle size based on magnitude
        size_px = max(2, int(3 + mag * 15))
        
        if 0 <= x < width and 0 <= y < height:
            rects.append(Rect(x, y, size_px, size_px))
    
    batch = DrawBatch.from_rects(rects, color)
    return FrameCommands.single_batch(batch)


# ============================================================================
# SYMMETRY VISUALIZER - Four-quadrant mirrored kaleidoscope bars
# ============================================================================

SYMMETRY_SCALE = 0.8


def symmetry_visualizer(
    magnitudes: np.ndarray,
    width: int,
    height: int,
    color: Color = PURPLE,
    scale: float = SYMMETRY_SCALE,
    log_scale: bool = True,
    db_floor: float = BAR_DB_FLOOR,
    db_ceiling: float = BAR_DB_CEILING,
) -> FrameCommands:
    """
    Four-quadrant symmetric bars - kaleidoscope-like mirror effect.
    
    Args:
        magnitudes: Frequency magnitude array
        width: Window width in pixels
        height: Window height in pixels
        color: Bar color
        scale: Height scaling factor
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(color))
    
    # Apply logarithmic scaling
    if log_scale:
        eps = 1e-10
        db_values = 20.0 * np.log10(magnitudes + eps)
        db_range = db_ceiling - db_floor
        normalized = (db_values - db_floor) / db_range
        normalized = np.clip(normalized, 0.0, 1.0)
        processed_mags = normalized
    else:
        fixed_max = 0.1
        processed_mags = np.clip(magnitudes / fixed_max, 0.0, 1.0)
    
    rects: list[Rect] = []
    
    half_width = width // 2
    half_height = height // 2
    bar_width = max(1, half_width // size)
    
    for i, mag in enumerate(processed_mags):
        bar_height = max(1, int(mag * scale * half_height))
        x_offset = i * bar_width
        
        # Top-right quadrant
        rects.append(Rect(
            x=half_width + x_offset,
            y=half_height - bar_height,
            width=bar_width,
            height=bar_height
        ))
        
        # Top-left quadrant (mirror)
        if half_width - x_offset - bar_width >= 0:
            rects.append(Rect(
                x=half_width - x_offset - bar_width,
                y=half_height - bar_height,
                width=bar_width,
                height=bar_height
            ))
        
        # Bottom-right quadrant
        rects.append(Rect(
            x=half_width + x_offset,
            y=half_height,
            width=bar_width,
            height=bar_height
        ))
        
        # Bottom-left quadrant (mirror)
        if half_width - x_offset - bar_width >= 0:
            rects.append(Rect(
                x=half_width - x_offset - bar_width,
                y=half_height,
                width=bar_width,
                height=bar_height
            ))
    
    batch = DrawBatch.from_rects(rects, color)
    return FrameCommands.single_batch(batch)


# ============================================================================
# PULSE VISUALIZER - Breathing ring based on audio energy
# ============================================================================

PULSE_BASE_RADIUS = 0.02
PULSE_MAX_RADIUS = 0.70
PULSE_LINE_COUNT = 120


def pulse_visualizer(
    magnitudes: np.ndarray,
    width: int,
    height: int,
    color: Color = RED,
    base_radius_ratio: float = PULSE_BASE_RADIUS,
    max_radius_ratio: float = PULSE_MAX_RADIUS,
    line_count: int = PULSE_LINE_COUNT,
) -> FrameCommands:
    """
    Pulsing ring - expands and contracts based on bass energy.
    
    Args:
        magnitudes: Frequency magnitude array
        width: Window width in pixels
        height: Window height in pixels
        color: Ring color
        base_radius_ratio: Minimum radius as fraction of screen
        max_radius_ratio: Maximum radius as fraction of screen
    """
    size = len(magnitudes)
    if size == 0:
        return FrameCommands.single_batch(DrawBatch.empty(color))
    
    # Focus on bass frequencies (first 1/8 of spectrum)
    bass_end = max(1, size // 8)
    bass_mags = magnitudes[:bass_end]
    
    # Convert to dB for better dynamic range
    eps = 1e-10
    db_floor = -60.0
    db_ceiling = -20.0  # Lower ceiling makes it easier to reach max size
    
    bass_avg = np.mean(bass_mags)
    db_val = 20.0 * np.log10(bass_avg + eps)
    energy = (db_val - db_floor) / (db_ceiling - db_floor)
    energy = np.clip(energy, 0.0, 1.0)
    
    center_x = width // 2
    center_y = height // 2
    max_dim = min(width, height) / 2
    
    base_radius = max_dim * base_radius_ratio
    max_radius = max_dim * max_radius_ratio
    current_radius = base_radius + (max_radius - base_radius) * energy
    
    # Draw ring as connected lines
    lines: list[Line] = []
    angle_step = 2 * math.pi / line_count
    
    for i in range(line_count):
        angle1 = i * angle_step
        angle2 = (i + 1) * angle_step
        
        x1 = int(center_x + math.cos(angle1) * current_radius)
        y1 = int(center_y + math.sin(angle1) * current_radius)
        x2 = int(center_x + math.cos(angle2) * current_radius)
        y2 = int(center_y + math.sin(angle2) * current_radius)
        
        lines.append(Line(x1, y1, x2, y2))
    
    # Add inner ring for thickness effect
    inner_radius = current_radius * 0.85
    for i in range(line_count):
        angle1 = i * angle_step
        angle2 = (i + 1) * angle_step
        
        x1 = int(center_x + math.cos(angle1) * inner_radius)
        y1 = int(center_y + math.sin(angle1) * inner_radius)
        x2 = int(center_x + math.cos(angle2) * inner_radius)
        y2 = int(center_y + math.sin(angle2) * inner_radius)
        
        lines.append(Line(x1, y1, x2, y2))
    
    batch = DrawBatch.from_lines(lines, color)
    return FrameCommands.single_batch(batch)


# Registry of available visualizers - easy to extend
VISUALIZERS: dict[str, Visualizer] = {
    "bars": bars_visualizer,
    "circle": circle_visualizer,
    "waveform": waveform_visualizer,
    "multiband": multiband_visualizer,
    "spectrum": multiband_visualizer,  # Alias for backward compatibility
    "particles": particles_visualizer,
    "symmetry": symmetry_visualizer,
    "pulse": pulse_visualizer,
}

# Ordered list for cycling through modes (excludes aliases)
MODE_ORDER = [
    "bars",
    "circle",
    "waveform",
    "multiband",
    "particles",
    "symmetry",
    "pulse",
]


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

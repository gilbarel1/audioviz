"""Configuration module for AudioViz.

Centralizes all configuration constants to avoid scattered hardcoded values.
"""

from dataclasses import dataclass
from pathlib import Path
from enum import Enum, auto


class ButtonType(Enum):
    """Types of buttons that can be created."""
    MODE = auto()  # Mode selection buttons


@dataclass(frozen=True, slots=True)
class Color:
    """RGBA color representation."""
    r: int
    g: int
    b: int
    a: int = 255
    
    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)

# Common colors
BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)
GREEN = Color(0, 255, 0)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)
ORANGE = Color(255, 165, 0)
YELLOW = Color(255, 255, 0)
PURPLE = Color(148, 0, 211)
RED = Color(255, 50, 50)
BLUE = Color(50, 100, 255)


@dataclass(frozen=True, slots=True)
class Rect:
    """A filled rectangle primitive."""
    x: int
    y: int
    width: int
    height: int
    
    def __post_init__(self):
        if self.width < 0:
            raise ValueError(f"Width must be non-negative, got {self.width}")
        if self.height < 0:
            raise ValueError(f"Height must be non-negative, got {self.height}")


@dataclass(frozen=True, slots=True)
class Line:
    """A line primitive from (x1,y1) to (x2,y2)."""
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass(frozen=True, slots=True)
class DrawBatch:
    """A batch of primitives to draw with the same color."""
    rectangles: tuple[Rect, ...]
    lines: tuple[Line, ...]
    color: Color
    
    @staticmethod
    def empty(color: Color = GREEN) -> "DrawBatch":
        return DrawBatch(rectangles=(), lines=(), color=color)
    
    @staticmethod
    def from_rects(rects: list[Rect], color: Color) -> "DrawBatch":
        return DrawBatch(rectangles=tuple(rects), lines=(), color=color)
    
    @staticmethod
    def from_lines(lines: list[Line], color: Color) -> "DrawBatch":
        return DrawBatch(rectangles=(), lines=tuple(lines), color=color)


@dataclass(frozen=True, slots=True)
class FrameCommands:
    """All draw commands for a single frame."""
    batches: tuple[DrawBatch, ...]
    background: Color = BLACK
    
    @staticmethod
    def single_batch(batch: DrawBatch, background: Color = BLACK) -> "FrameCommands":
        return FrameCommands(batches=(batch,), background=background)



@dataclass(frozen=True)
class UIConfig:
    """UI styling and layout configuration."""
    
    # Mode button dimensions
    mode_button_height: int = 45
    mode_button_width: int = 110
    mode_button_padding: int = 8
    mode_button_y_offset: int = 10
    
    # Mode button colors
    mode_button_bg_color: Color = Color(40, 40, 40, 220)
    mode_button_hover_color: Color = Color(60, 60, 60, 220)
    mode_button_active_color: Color = Color(80, 120, 200, 220)
    mode_button_border_color: Color = Color(100, 100, 100, 255)

    
    # Mode button text rendering
    text_color: Color = WHITE
    mode_text_padding_x: int = 10
    mode_text_vertical_correction: int = 16  # Approx height for vertical centering







@dataclass(frozen=True)
class AppConfig:
    """Application-wide configuration."""
    
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    
    # Visualization settings
    default_mode: str = "bars"
    auto_switch_interval: float = 5.0
    
    # Button specifications (label, type) for the button panel
    button_specs: tuple[tuple[str, "ButtonType"], ...] = (
        ("bars", ButtonType.MODE),
        ("circle", ButtonType.MODE),
        ("waveform", ButtonType.MODE),
        ("multiband", ButtonType.MODE),
        ("particles", ButtonType.MODE),
        ("symmetry", ButtonType.MODE),
        ("pulse", ButtonType.MODE),
    )

    
    # Font path - resolved relative to this module (resources is in parent dir)
    font_path: str = str(Path(__file__).parent.parent / "resources" / "Roboto-Regular.ttf")


@dataclass(frozen=True)
class AudioConfig:
    """Audio processing configuration."""
    nperseg: int = 1024
    blocksize: int = 8192




# Common visualization constants
DB_FLOOR_DEFAULT = -60.0
DB_CEILING_DEFAULT = -10.0
LINEAR_SCALING_MAX = 0.1  # For non-log scaling fallback


@dataclass(frozen=True)
class BarsConfig:
    """Configuration for bars visualizer."""
    scale: float = 0.9
    color: Color = GREEN
    db_floor: float = DB_FLOOR_DEFAULT
    db_ceiling: float = DB_CEILING_DEFAULT


@dataclass(frozen=True)
class CircleConfig:
    """Configuration for circle visualizer."""
    scale: float = 3000.0
    color: Color = CYAN
    base_radius_ratio: float = 0.2


@dataclass(frozen=True)
class WaveformConfig:
    """Configuration for waveform visualizer."""
    scale: float = 0.7
    color: Color = YELLOW
    subsample: int = 4


@dataclass(frozen=True)
class SpectrumConfig:
    """Configuration for spectrum/multiband visualizer."""
    scale: float = 0.85
    subsample: int = 2
    db_floor: float = DB_FLOOR_DEFAULT
    db_ceiling: float = DB_CEILING_DEFAULT
    band_colors: tuple[Color, ...] = (
        RED,                   # Sub-bass (Red)
        Color(255, 150, 0),    # Bass (Orange)
        YELLOW,                # Low-mids (Yellow)
        Color(0, 255, 100),    # Mids (Green)
        Color(0, 200, 255),    # High-mids (Cyan)
        Color(150, 100, 255),  # Highs (Purple)
    )


@dataclass(frozen=True)
class ParticlesConfig:
    """Configuration for particles visualizer."""
    count: int = 200
    color: Color = MAGENTA
    energy_multiplier: float = 3000.0
    radius_multiplier: float = 300.0
    size_multiplier: float = 15.0
    db_floor: float = DB_FLOOR_DEFAULT
    db_ceiling: float = DB_CEILING_DEFAULT


@dataclass(frozen=True)
class SymmetryConfig:
    """Configuration for symmetry visualizer."""
    scale: float = 0.8
    color: Color = PURPLE
    db_floor: float = DB_FLOOR_DEFAULT
    db_ceiling: float = DB_CEILING_DEFAULT


@dataclass(frozen=True)
class PulseConfig:
    """Configuration for pulse visualizer."""
    base_radius: float = 0.02
    max_radius: float = 0.70
    line_count: int = 120
    color: Color = RED
    db_floor: float = DB_FLOOR_DEFAULT
    db_ceiling: float = -20.0


@dataclass(frozen=True)
class VizConfig:
    """Visualization-specific configuration."""
    
    # Common
    bar_db_floor: float = -60.0
    bar_db_ceiling: float = -10.0
    linear_scaling_max: float = 0.1  # For non-log scaling fallback

    
    # Bars
    bar_scale: float = 0.9
    bar_color: Color = GREEN

    
    # Circle
    circle_scale: float = 3000.0
    circle_color: Color = CYAN

    circle_base_radius_ratio: float = 0.2
    
    # Waveform
    waveform_scale: float = 0.7
    waveform_color: Color = YELLOW
    waveform_subsample: int = 4


    
    # Spectrum / Multiband
    spectrum_scale: float = 0.85
    spectrum_subsample: int = 2
    band_colors: tuple[Color, ...] = (

        RED,                   # Sub-bass (Red)
        Color(255, 150, 0),    # Bass (Orange)
        YELLOW,                # Low-mids (Yellow)
        Color(0, 255, 100),    # Mids (Green)
        Color(0, 200, 255),    # High-mids (Cyan)
        Color(150, 100, 255),  # Highs (Purple)
    )

    
    # Particles
    particle_count: int = 200
    particle_color: Color = MAGENTA
    particle_energy_multiplier: float = 3000.0
    particle_radius_multiplier: float = 300.0
    particle_size_multiplier: float = 15.0
    particle_db_floor: float = -60.0
    particle_db_ceiling: float = -10.0


    
    # Symmetry
    symmetry_scale: float = 0.8
    symmetry_color: Color = PURPLE

    
    # Pulse
    pulse_base_radius: float = 0.02
    pulse_max_radius: float = 0.70
    pulse_line_count: int = 120
    pulse_color: Color = RED
    pulse_db_floor: float = -60.0
    pulse_db_ceiling: float = -20.0


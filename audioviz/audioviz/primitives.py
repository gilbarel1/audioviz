"""Immutable primitive draw commands for the visualization layer."""

from dataclasses import dataclass


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


@dataclass(frozen=True, slots=True)
class Rect:
    """A filled rectangle primitive."""
    x: int
    y: int
    width: int
    height: int
    
    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)


@dataclass(frozen=True, slots=True)
class Line:
    """A line primitive from (x1,y1) to (x2,y2)."""
    x1: int
    y1: int
    x2: int
    y2: int
    
    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)


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

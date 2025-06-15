"""
Point slice type definitions for working with 3D point collections.

This module provides types for representing collections of 3D points
along with their associated metadata such as name, color, and slice type.
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


@dataclass
class Point3D:
    """Represents a 3D point with x, y, z coordinates."""

    x: float
    y: float
    z: float


class SliceType(Enum):
    """Enumeration for different slice types."""

    XY = "XY"
    XZ = "XZ"
    YZ = "YZ"
    UNKNOWN = "UNKNOWN"


@dataclass
class PointsSlice:
    """Represents a collection of 3D points with associated metadata."""

    points: List[Point3D]
    name: str
    color: int  # DXF color index
    slice_type: SliceType

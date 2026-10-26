# Point Slice Studio - Convert CSV point cloud data to DXF format
# Copyright (C) 2024 Kostas Patsis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Point slice type definitions for working with 3D point collections.

This module provides types for representing collections of 3D points
along with their associated metadata such as name, color, and slice type.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
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
    slice_type: SliceType


def rotate_slice_to_xy(slice_obj: PointsSlice) -> PointsSlice:
    """
    Rotate a slice to the XY plane.

    For XZ slices: Rotates around X-axis so Z becomes Y (x, y, z) -> (x, z, y)
    For YZ slices: Rotates around Z-axis so Y becomes X (x, y, z) -> (y, x, z)
    For XY slices: Returns the slice unchanged

    Args:
        slice_obj: The PointsSlice to rotate

    Returns:
        A new PointsSlice with rotated coordinates and updated slice_type
    """
    if slice_obj.slice_type == SliceType.XY:
        # Already in XY plane, return a copy
        return PointsSlice(
            points=[Point3D(p.x, p.y, p.z) for p in slice_obj.points],
            name=slice_obj.name,
            slice_type=SliceType.XY,
        )

    elif slice_obj.slice_type == SliceType.XZ:
        # Rotate XZ to XY: (x, y, z) -> (x, z, y)
        rotated_points = [Point3D(p.x, p.z, p.y) for p in slice_obj.points]

    elif slice_obj.slice_type == SliceType.YZ:
        # Rotate YZ to XY: (x, y, z) -> (y, z, x)
        rotated_points = [Point3D(p.y, p.z, p.x) for p in slice_obj.points]

    else:  # UNKNOWN
        # For unknown slice types, return unchanged
        return PointsSlice(
            points=[Point3D(p.x, p.y, p.z) for p in slice_obj.points],
            name=slice_obj.name,
            slice_type=slice_obj.slice_type,
        )

    return PointsSlice(
        points=rotated_points,
        name=f"{slice_obj.name}_rotated",
        slice_type=SliceType.XY,
    )


# Absorbs floating-point error so points lying exactly on a band edge are kept
_THICKNESS_EPSILON = 1e-9


def filter_slice_thickness(slice_obj: PointsSlice, thickness: float) -> PointsSlice:
    """
    Reduce a slice to the given thickness along its constant axis.

    The new band is centred on the midpoint of the slice's current range
    along that axis (Z for XY, Y for XZ, X for YZ), and only points inside
    the band are kept.

    UNKNOWN slices, and slices already no thicker than ``thickness``, are
    returned unchanged.

    Args:
        slice_obj: The PointsSlice to filter
        thickness: Desired slice thickness (must be positive)

    Returns:
        A new PointsSlice containing only the points inside the band

    Raises:
        ValueError: If thickness is not positive
    """
    if thickness <= 0:
        raise ValueError(f"Thickness must be positive, got {thickness}")

    if slice_obj.slice_type == SliceType.XY:
        axis = "z"
    elif slice_obj.slice_type == SliceType.XZ:
        axis = "y"
    elif slice_obj.slice_type == SliceType.YZ:
        axis = "x"
    else:  # UNKNOWN
        axis = None

    copied_points = [Point3D(p.x, p.y, p.z) for p in slice_obj.points]

    if axis is None or not copied_points:
        return PointsSlice(
            points=copied_points, name=slice_obj.name, slice_type=slice_obj.slice_type
        )

    values = [getattr(p, axis) for p in copied_points]
    low, high = min(values), max(values)
    if high - low <= thickness:
        return PointsSlice(
            points=copied_points, name=slice_obj.name, slice_type=slice_obj.slice_type
        )

    midpoint = (low + high) / 2
    half_thickness = thickness / 2 + _THICKNESS_EPSILON
    filtered_points = [
        p for p in copied_points if abs(getattr(p, axis) - midpoint) <= half_thickness
    ]

    return PointsSlice(
        points=filtered_points, name=slice_obj.name, slice_type=slice_obj.slice_type
    )


def format_level(values: List[float]) -> str:
    """
    Format the level of a set of values as a signed 2-decimal string.

    The level is the midpoint of the values' range, rounded half-up, so
    values from +0.93 to +0.98 give "+0.96".

    Args:
        values: Non-empty list of values along the slice's constant axis

    Returns:
        The level, e.g. "+0.96" or "-8.35"
    """
    midpoint = (min(values) + max(values)) / 2
    # Go through a 9-decimal string to drop float noise (0.955 is stored as
    # 0.9549999...) before rounding half-up
    level = Decimal(f"{midpoint:.9f}").quantize(Decimal("0.01"), ROUND_HALF_UP)
    if level == 0:
        level = abs(level)  # Avoid "-0.00"
    return f"{level:+}"

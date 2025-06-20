# Point Slice Studio - Convert CSV point cloud data to DXF format
# Copyright (C) 2024 [Your Name]
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

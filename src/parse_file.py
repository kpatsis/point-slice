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
CSV file parser for point cloud data.

This module provides functionality to parse space-separated CSV files
containing 3D point coordinates and create PointsSlice objects.
"""

import os
import random
from typing import Optional, List
from points_slice import Point3D, PointsSlice, SliceType


def detect_slice_type_from_data(
    points: List[Point3D], sample_size: int = 250, threshold: float = 0.015
) -> SliceType:
    """
    Detect slice type by analyzing the point data distribution.

    Determines which dimension has the smallest variation and checks if it's
    within the threshold to identify the slice plane.

    Args:
        points: List of Point3D objects to analyze
        sample_size: Number of points to sample for analysis (for performance)
        threshold: Maximum variation allowed to consider a dimension constant

    Returns:
        SliceType enum value based on data analysis
    """
    if not points:
        return SliceType.UNKNOWN

    # Use a random sample for performance with large datasets
    sample_points = random.sample(points, min(len(points), sample_size))

    # Extract coordinates
    xs = [p.x for p in sample_points]
    ys = [p.y for p in sample_points]
    zs = [p.z for p in sample_points]

    # Calculate ranges in each dimension
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)

    # Find the dimension with the smallest variation
    min_variation = min(dx, dy, dz)

    # Check if the smallest variation is within the threshold
    if min_variation > threshold:
        return SliceType.UNKNOWN

    # Determine slice type based on which dimension has the smallest variation
    if min_variation == dz:
        return SliceType.XY  # Z is constant, varies in X-Y plane
    elif min_variation == dy:
        return SliceType.XZ  # Y is constant, varies in X-Z plane
    elif min_variation == dx:
        return SliceType.YZ  # X is constant, varies in Y-Z plane
    else:
        return SliceType.UNKNOWN


def parse_csv_file(
    filepath: str,
    max_points: Optional[int] = None,
    threshold: float = 0.050,
) -> PointsSlice:
    """
    Parse a space-separated CSV file containing 3D point coordinates.

    Args:
        filepath: Path to the CSV file to parse
        max_points: Maximum number of points to read (None for all points)
        threshold: Maximum variation allowed to consider a dimension constant

    Returns:
        PointsSlice object containing the parsed points and metadata

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is invalid
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]

    points = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Split by whitespace
                values = line.split()

                # Ensure we have at least 3 values for X, Y, Z
                if len(values) < 3:
                    raise ValueError(
                        f"Line {line_num}: Expected at least 3 values (X, Y, Z), got {len(values)}"
                    )

                try:
                    x = float(values[0])
                    y = float(values[1])
                    z = float(values[2])

                    points.append(Point3D(x, y, z))

                    # Stop if we've reached the maximum points limit
                    if max_points and len(points) >= max_points:
                        break

                except ValueError as e:
                    raise ValueError(
                        f"Line {line_num}: Invalid coordinate values - {e}"
                    )

    except UnicodeDecodeError:
        raise ValueError(
            f"Unable to decode file {filepath}. Please check file encoding."
        )

    if not points:
        raise ValueError(f"No valid points found in file {filepath}")

    # Determine metadata
    slice_type = detect_slice_type_from_data(points, threshold=threshold)

    return PointsSlice(points=points, name=name, slice_type=slice_type)


def parse_directory(
    directory_path: str,
    max_points_per_file: Optional[int] = None,
    threshold: float = 0.050,
) -> List[PointsSlice]:
    """
    Parse all CSV files in a directory.

    Args:
        directory_path: Path to directory containing CSV files
        max_points_per_file: Maximum points to read per file (None for all)
        threshold: Maximum variation allowed to consider a dimension constant

    Returns:
        List of PointsSlice objects

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    if not os.path.isdir(directory_path):
        raise ValueError(f"Path is not a directory: {directory_path}")

    slices: List[PointsSlice] = []
    csv_files = [f for f in os.listdir(directory_path) if f.lower().endswith(".csv")]
    csv_files.sort()  # Sort filenames for consistent processing order

    if not csv_files:
        raise ValueError(f"No CSV files found in directory: {directory_path}")

    for filename in csv_files:
        filepath = os.path.join(directory_path, filename)
        try:
            slice_obj = parse_csv_file(
                filepath,
                max_points=max_points_per_file,
                threshold=threshold,
            )
            slices.append(slice_obj)
            print(
                f"Parsed {filename}: {len(slice_obj.points)} points, type: {slice_obj.slice_type.value}"
            )
        except Exception as e:
            print(f"Warning: Failed to parse {filename}: {e}")
            continue

    return slices

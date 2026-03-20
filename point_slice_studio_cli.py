#!/usr/bin/env python3

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
Point Slice Studio CLI

This script creates DXF files from CSV point cloud data. It parses CSV files
containing 3D point coordinates and converts them into DXF format with
proper layers, colors, and block organization.

Usage:
    python point_slice_studio_cli.py [input_directory] [output_file]

If no arguments are provided, defaults to:
    - Input directory: tests/testdata/02_csv
    - Output file: output.dxf
"""

import argparse

from ps_core.workflow import create_dxf_from_csv_directory


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Create DXF files from CSV point cloud data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python point_slice_studio_cli.py                                    # Use defaults
    python point_slice_studio_cli.py data/csv_files output.dxf         # Custom paths
    python point_slice_studio_cli.py /path/to/csv/files result.dxf     # Absolute paths
    python point_slice_studio_cli.py in/ out.dxf --anchor-x 10 --xz-rotated-x-offset -250
        """,
    )

    parser.add_argument(
        "input_directory",
        nargs="?",
        default="tests/testdata/02_csv",
        help="Directory containing CSV files (default: tests/testdata/02_csv)",
    )

    parser.add_argument(
        "output_file",
        nargs="?",
        default="output.dxf",
        help="Output DXF filename (default: output.dxf)",
    )

    parser.add_argument(
        "--colors",
        nargs="+",
        type=int,
        help="Custom color indices (1-256) for AutoCAD colors",
    )

    parser.add_argument(
        "--anchor-x",
        type=float,
        default=0.0,
        help="X coordinate of the starting point of the imported point cloud (default: 0.0)",
    )

    parser.add_argument(
        "--anchor-y",
        type=float,
        default=0.0,
        help="Y coordinate of the starting point of the imported point cloud (default: 0.0)",
    )

    parser.add_argument(
        "--xz-rotated-x-offset",
        type=float,
        default=-300.0,
        help=("X offset added to anchor X for rotated XZ slices (default: -300.0)"),
    )

    parser.add_argument(
        "--yz-rotated-x-offset",
        type=float,
        default=-200.0,
        help=("X offset added to anchor X for rotated YZ slices (default: -200.0)"),
    )

    parser.add_argument(
        "--label-x",
        type=float,
        default=-40.0,
        help="X position for label start (default: -40.0)",
    )

    parser.add_argument(
        "--label-y",
        type=float,
        default=0.0,
        help="Y position for label start (default: 0.0)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.050,
        help=(
            "Threshold for slice-type detection (max allowed variation of the"
            " smallest axis). Smaller means stricter; larger means more"
            " tolerant. Default: 0.050"
        ),
    )

    args = parser.parse_args()

    # Validate colors if provided
    if args.colors:
        invalid_colors = [c for c in args.colors if c < 1 or c > 256]
        if invalid_colors:
            print(
                f"❌ Error: Invalid color indices: {invalid_colors}. Colors must be between 1-256."
            )
            return

    label_position = (args.label_x, args.label_y)
    anchor_point = (args.anchor_x, args.anchor_y)

    create_dxf_from_csv_directory(
        args.input_directory,
        args.output_file,
        anchor_point=anchor_point,
        xz_rotated_x_offset=args.xz_rotated_x_offset,
        yz_rotated_x_offset=args.yz_rotated_x_offset,
        colors=args.colors,
        label_position=label_position,
        threshold=args.threshold,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

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

import os
import sys
import argparse
import time
from typing import List

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dxf_document import DXFDocument, Block  # noqa: E402
from parse_file import parse_directory  # noqa: E402
from points_slice import SliceType, rotate_slice_to_xy  # noqa: E402


def create_dxf_from_csv_directory(
    input_directory: str, 
    output_file: str,
    colors: List[int] = None,
    label_position: tuple[float, float] = None
) -> None:
    """
    Create a DXF file from CSV files in a directory.
    
    Args:
        input_directory: Directory containing CSV files
        output_file: Output DXF filename
        colors: List of AutoCAD color indices to use
        label_position: Starting position for labels
    """
    # Start timing the entire execution
    execution_start_time = time.perf_counter()
    
    print("\n" + "=" * 80)
    print("DXF DOCUMENT CREATION WORKFLOW")
    print("=" * 80)
    
    # Validate input directory
    if not os.path.exists(input_directory):
        print(f"❌ Error: Input directory '{input_directory}' does not exist")
        return
    
    if not os.path.isdir(input_directory):
        print(f"❌ Error: '{input_directory}' is not a directory")
        return

    # Step 1: Parse all CSV files from the input directory
    print(f"📂 Parsing CSV files from: {input_directory}")
    parsing_start_time = time.perf_counter()
    try:
        points_slices = parse_directory(input_directory)
    except Exception as e:
        print(f"❌ Error parsing CSV files: {e}")
        return
    parsing_end_time = time.perf_counter()
    parsing_duration = parsing_end_time - parsing_start_time

    if not points_slices:
        print("❌ Error: No valid CSV files found or parsed")
        return

    print(f"✅ Successfully parsed {len(points_slices)} CSV files in {parsing_duration:.3f} seconds")

    # Step 2: Create DXF document with custom colors and label position
    default_colors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # More colors for variety
    default_label_position = (-40.0, 0.0)
    
    colors = colors or default_colors
    label_position = label_position or default_label_position
    
    doc = DXFDocument(colors=colors, label_start_position=label_position)
    print(f"📋 Created initial DXFDocument")
    print(f"🏷️  Label start position: {label_position}")

    # Step 3: Add each PointsSlice as a block with appropriate positioning
    for points_slice in points_slices:
        layer_name = f"Layer_{points_slice.name}"

        # Rotate XZ and YZ slices to XY plane
        if points_slice.slice_type == SliceType.XZ or points_slice.slice_type == SliceType.YZ:
            points_slice_rotated = rotate_slice_to_xy(points_slice)
            block_name_rotated = f"Block_{points_slice.name}_rotated"
            insert_position_rotated = (100.0 if points_slice.slice_type == SliceType.XZ else 200.0, 0.0, 0.0)
            block_rotated = Block(
                points_slice=points_slice_rotated,
                layer_name=layer_name,
                block_name=block_name_rotated,
                insert_position=insert_position_rotated,
            )
            doc.add_block(block_rotated)
            print(f"➕ Added rotated block '{points_slice_rotated.name}' with {len(points_slice_rotated.points)} points ({points_slice_rotated.slice_type.value})")

        # XY and UNKNOWN slices positioned at origin
        block = Block(
            points_slice=points_slice,
            layer_name=layer_name,
            block_name=f"Block_{points_slice.name}",
            insert_position=(0.0, 0.0, 0.0),
        )
        
        doc.add_block(block)
        print(f"➕ Added block '{points_slice.name}' with {len(points_slice.points)} points ({points_slice.slice_type.value})")

    print(f"📦 Total blocks in document: {len(doc.blocks)}")

    # Step 4: Plot all blocks to the DXF document
    print("🎨 Plotting blocks to DXF document...")
    plotting_start_time = time.perf_counter()
    try:
        doc.plot()
        plotting_end_time = time.perf_counter()
        plotting_duration = plotting_end_time - plotting_start_time
        print(f"✅ Successfully plotted all blocks in {plotting_duration:.3f} seconds")
    except Exception as e:
        print(f"❌ Error plotting blocks: {e}")
        return

    # Step 5: Save the DXF file
    print(f"💾 Saving DXF file to: {output_file}")
    saving_start_time = time.perf_counter()
    try:
        doc.save(output_file)
        saving_end_time = time.perf_counter()
        saving_duration = saving_end_time - saving_start_time
        
        # Check file size
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ DXF file saved successfully in {saving_duration:.3f} seconds")
        else:
            print("❌ Error: DXF file was not created")
            return
            
    except Exception as e:
        print(f"❌ Error saving DXF file: {e}")
        return

    # Step 6: Display summary
    execution_end_time = time.perf_counter()
    total_execution_time = execution_end_time - execution_start_time
    
    print("\n📊 CREATION SUMMARY:")
    print(f"   • CSV files parsed: {len(points_slices)}")
    print(f"   • Blocks created: {len(doc.blocks)}")
    print(f"   • Output file: {output_file}")
    
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"   • File size: {file_size / 1024:.1f} KB")
    
    print(f"\n⏱️  TIMING BREAKDOWN:")
    print(f"   • Parsing: {parsing_duration:.3f} seconds")
    print(f"   • Plotting: {plotting_duration:.3f} seconds")
    print(f"   • Saving: {saving_duration:.3f} seconds")
    print(f"   • Total execution: {total_execution_time:.3f} seconds")
    
    print("=" * 80)
    print("🎉 DXF creation completed successfully!")


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
        """
    )
    
    parser.add_argument(
        "input_directory",
        nargs="?",
        default="tests/testdata/02_csv",
        help="Directory containing CSV files (default: tests/testdata/02_csv)"
    )
    
    parser.add_argument(
        "output_file", 
        nargs="?",
        default="output.dxf",
        help="Output DXF filename (default: output.dxf)"
    )
    
    parser.add_argument(
        "--colors",
        nargs="+",
        type=int,
        help="Custom color indices (1-256) for AutoCAD colors"
    )
    
    parser.add_argument(
        "--label-x",
        type=float,
        default=-40.0,
        help="X position for label start (default: -40.0)"
    )
    
    parser.add_argument(
        "--label-y", 
        type=float,
        default=0.0,
        help="Y position for label start (default: 0.0)"
    )

    args = parser.parse_args()
    
    # Validate colors if provided
    if args.colors:
        invalid_colors = [c for c in args.colors if c < 1 or c > 256]
        if invalid_colors:
            print(f"❌ Error: Invalid color indices: {invalid_colors}. Colors must be between 1-256.")
            return
    
    label_position = (args.label_x, args.label_y)
    
    create_dxf_from_csv_directory(
        args.input_directory,
        args.output_file, 
        args.colors,
        label_position
    )


if __name__ == "__main__":
    main() 
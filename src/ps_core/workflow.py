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
DXF creation workflow.

Orchestrates parsing CSV point cloud files and writing them to a DXF document.
"""

import os
import time
from typing import List

from ps_core.dxf_document import DXFDocument, Block
from ps_core.parse_file import parse_directory
from ps_core.points_slice import SliceType, rotate_slice_to_xy


def create_dxf_from_csv_directory(
    input_directory: str,
    output_file: str,
    colors: List[int] = None,
    label_position: tuple[float, float] = None,
    threshold: float = 0.050,
) -> None:
    """
    Create a DXF file from CSV files in a directory.

    Args:
        input_directory: Directory containing CSV files
        output_file: Output DXF filename
        colors: List of AutoCAD color indices to use
        label_position: Starting position for labels
        threshold: Threshold for slice-type detection
    """
    execution_start_time = time.perf_counter()

    print("\n" + "=" * 80)
    print("DXF DOCUMENT CREATION WORKFLOW")
    print("=" * 80)

    if not os.path.exists(input_directory):
        print(f"❌ Error: Input directory '{input_directory}' does not exist")
        return

    if not os.path.isdir(input_directory):
        print(f"❌ Error: '{input_directory}' is not a directory")
        return

    print(f"📂 Parsing CSV files from: {input_directory}")
    parsing_start_time = time.perf_counter()
    try:
        points_slices = parse_directory(input_directory, threshold=threshold)
    except Exception as e:
        print(f"❌ Error parsing CSV files: {e}")
        return
    parsing_end_time = time.perf_counter()
    parsing_duration = parsing_end_time - parsing_start_time

    if not points_slices:
        print("❌ Error: No valid CSV files found or parsed")
        return

    print(
        f"✅ Successfully parsed {len(points_slices)} CSV files in {parsing_duration:.3f} seconds"
    )

    default_colors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    default_label_position = (-40.0, 0.0)

    colors = colors or default_colors
    label_position = label_position or default_label_position

    doc = DXFDocument(colors=colors, label_start_position=label_position)
    print(f"📋 Created initial DXFDocument")
    print(f"🏷️  Label start position: {label_position}")

    for points_slice in points_slices:
        layer_name = f"Layer_{points_slice.name}"

        if (
            points_slice.slice_type == SliceType.XZ
            or points_slice.slice_type == SliceType.YZ
        ):
            points_slice_rotated = rotate_slice_to_xy(points_slice)
            block_name_rotated = f"Block_{points_slice.name}_rotated"
            insert_position_rotated = (
                100.0 if points_slice.slice_type == SliceType.XZ else 200.0,
                0.0,
                0.0,
            )
            block_rotated = Block(
                points_slice=points_slice_rotated,
                layer_name=layer_name,
                block_name=block_name_rotated,
                insert_position=insert_position_rotated,
            )
            doc.add_block(block_rotated)
            print(
                f"➕ Added rotated block '{points_slice_rotated.name}' with {len(points_slice_rotated.points)} points ({points_slice_rotated.slice_type.value})"
            )

        block = Block(
            points_slice=points_slice,
            layer_name=layer_name,
            block_name=f"Block_{points_slice.name}",
            insert_position=(0.0, 0.0, 0.0),
        )

        doc.add_block(block)
        print(
            f"➕ Added block '{points_slice.name}' with {len(points_slice.points)} points ({points_slice.slice_type.value})"
        )

    print(f"📦 Total blocks in document: {len(doc.blocks)}")

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

    print(f"💾 Saving DXF file to: {output_file}")
    saving_start_time = time.perf_counter()
    try:
        doc.save(output_file)
        saving_end_time = time.perf_counter()
        saving_duration = saving_end_time - saving_start_time

        if os.path.exists(output_file):
            print(f"✅ DXF file saved successfully in {saving_duration:.3f} seconds")
        else:
            print("❌ Error: DXF file was not created")
            return

    except Exception as e:
        print(f"❌ Error saving DXF file: {e}")
        return

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

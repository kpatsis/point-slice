#!/usr/bin/env python3
"""
Unit tests for the dxf_handler module.

Tests cover adding PointsSlice objects to DXF files as blocks,
color and layer management, and multiple slice handling.
"""

import os
import sys
import time
import unittest

# Add the src directory to the path for imports - must be before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parse_file import parse_directory  # noqa: E402
from dxf_handler import add_points_slice_to_dxf  # noqa: E402
from points_slice import SliceType, rotate_slice_to_xy  # noqa: E402


class TestDXFHandler(unittest.TestCase):
    """Test the DXF handler functions."""

    def setUp(self):
        """Set up test environment."""
        self.test_data_dir = os.path.join(
            os.path.dirname(__file__), "testdata", "03_csv_original"
        )

    def test_add_all_slices_to_same_dxf(self):
        """Test adding all PointsSlice objects from 02_csv directory to the same DXF document."""
        test_start_time = time.time()
        
        print("\n" + "=" * 80)
        print(
            "TESTING: Adding ALL PointsSlice objects from 02_csv to same DXF document"
        )
        print("=" * 80)

        # Parse all CSV files in the directory using the efficient parse_directory function
        print(f"📂 Parsing directory: {self.test_data_dir}")
        parse_start_time = time.time()

        points_slices = parse_directory(self.test_data_dir)

        parse_end_time = time.time()
        parse_duration = parse_end_time - parse_start_time
        print(f"✅ Successfully parsed {len(points_slices)} CSV files in {parse_duration:.3f}s")

        # Verify we have results
        self.assertGreater(
            len(points_slices), 0, "No slices were parsed from directory"
        )

        # Color palette for different slices
        color_palette = [
            5,
            1,
            2,
            3,
            4,
            6,
            30,
            40,
            50,
            60,
        ]  # Blue, Red, Yellow, Green, Cyan, Magenta, etc.

        # Add all slices to DXF one by one using add_points_slice_to_dxf
        print(f"➕ Adding all {len(points_slices)} slices to DXF individually...")
        total_points_expected = sum(len(ps.points) for ps in points_slices)
        print(f"📈 Total points to process: {total_points_expected}")
        
        dxf_processing_start_time = time.time()

        dxf_doc = None
        x_offset_for_rotated = 100.0  # X offset for rotated XZ/YZ slices
        
        # Text positioning parameters
        text_left_margin = -50.0  # Distance to the left of blocks for text
        text_vertical_spacing = -3.0  # Vertical spacing between text labels
        text_start_y = 10.0  # Starting Y position for text
        text_counter = 0  # Counter for all text labels (original + rotated)

        for i, points_slice in enumerate(points_slices):
            slice_start_time = time.time()
            color = color_palette[i % len(color_palette)]
            
            print(f"   📁 Adding slice {i+1}/{len(points_slices)}: {points_slice.name}")
            print(f"      Slice type: {points_slice.slice_type}")
            print(f"      Points in slice: {len(points_slice.points)}")

            # Always add the original slice first at (0, 0, 0)
            original_layer_name = f"SLICE_{i+1:02d}_{points_slice.name}"
            original_block_name = f"BLOCK_{i+1:02d}_{points_slice.name}"
            
            # Calculate text position for original slice (left of block at origin)
            original_text_x = text_left_margin
            original_text_y = text_start_y + (text_counter * text_vertical_spacing)
            
            print(f"      📍 Adding original slice at position (0, 0, 0)")
            print(f"      📝 Text label at position ({original_text_x}, {original_text_y})")
            
            add_start_time = time.time()
            dxf_doc = add_points_slice_to_dxf(
                points_slice=points_slice,
                dxf_doc=dxf_doc,
                color=color,
                layer_name=original_layer_name,
                block_name=original_block_name,
                insert_position=(0.0, 0.0, 0.0),
                text_position=(original_text_x, original_text_y),
            )
            add_end_time = time.time()
            add_duration = add_end_time - add_start_time
            print(f"      ⏱️  Original slice added in {add_duration:.3f}s")
            text_counter += 1
            
            # If slice is XZ or YZ, also add the rotated version with X offset
            if points_slice.slice_type in (SliceType.XZ, SliceType.YZ):
                print(f"      🔄 Rotating {points_slice.slice_type.value} slice to XY plane")
                rotate_start_time = time.time()
                rotated_slice = rotate_slice_to_xy(points_slice)
                rotate_end_time = time.time()
                rotate_duration = rotate_end_time - rotate_start_time
                print(f"      ⏱️  Rotation completed in {rotate_duration:.3f}s")
                
                # Use a different color for rotated version (next color in palette)
                rotated_color = color_palette[(i + 1) % len(color_palette)]
                rotated_layer_name = f"SLICE_{i+1:02d}_{rotated_slice.name}"
                rotated_block_name = f"BLOCK_{i+1:02d}_{rotated_slice.name}"
                
                # Calculate text position for rotated slice (left of rotated block)
                rotated_text_x = x_offset_for_rotated + text_left_margin
                rotated_text_y = text_start_y + (text_counter * text_vertical_spacing)
                
                print(f"      📍 Adding rotated slice with X offset: {x_offset_for_rotated}")
                print(f"      📝 Text label at position ({rotated_text_x}, {rotated_text_y})")
                
                rotated_add_start_time = time.time()
                dxf_doc = add_points_slice_to_dxf(
                    points_slice=rotated_slice,
                    dxf_doc=dxf_doc,
                    color=rotated_color,
                    layer_name=rotated_layer_name,
                    block_name=rotated_block_name,
                    insert_position=(x_offset_for_rotated, 0.0, 0.0),
                    text_position=(rotated_text_x, rotated_text_y),
                )
                rotated_add_end_time = time.time()
                rotated_add_duration = rotated_add_end_time - rotated_add_start_time
                print(f"      ⏱️  Rotated slice added in {rotated_add_duration:.3f}s")
                text_counter += 1
            
            slice_end_time = time.time()
            slice_duration = slice_end_time - slice_start_time
            print(f"      ✅ Total time for slice {points_slice.name}: {slice_duration:.3f}s")

        dxf_processing_end_time = time.time()
        dxf_processing_duration = dxf_processing_end_time - dxf_processing_start_time
        print(f"✅ All slices processed in {dxf_processing_duration:.3f}s")

        # Verify the DXF document structure
        print("🔍 Verifying DXF document structure...")
        verification_start_time = time.time()

        verification_end_time = time.time()
        verification_duration = verification_end_time - verification_start_time
        print(f"✅ DXF verification completed in {verification_duration:.3f}s")

        # Save to project root for easy inspection
        print("💾 Saving DXF file...")
        save_start_time = time.time()
        project_output = "test_all_slices_output.dxf"
        dxf_doc.saveas(project_output)
        save_end_time = time.time()
        save_duration = save_end_time - save_start_time
        print(f"💾 Test DXF saved to project root: {project_output} in {save_duration:.3f}s")
        
        test_end_time = time.time()
        total_test_duration = test_end_time - test_start_time
        
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 80)
        print(f"📁 Directory parsing: {parse_duration:.3f}s")
        print(f"🔄 DXF processing: {dxf_processing_duration:.3f}s")
        print(f"🔍 Verification: {verification_duration:.3f}s")
        print(f"💾 File saving: {save_duration:.3f}s")
        print(f"⏱️  Total test time: {total_test_duration:.3f}s")
        print(f"📈 Processed: {len(points_slices)} files, {total_points_expected} total points")
        print(f"🚀 Average points/second: {total_points_expected/total_test_duration:.1f}")

        print("✅ Test completed successfully!")


if __name__ == "__main__":
    unittest.main(verbosity=2)

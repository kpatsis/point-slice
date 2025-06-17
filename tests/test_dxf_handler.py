#!/usr/bin/env python3
"""
Unit tests for the dxf_handler module.

Tests cover adding PointsSlice objects to DXF files as blocks,
color and layer management, and multiple slice handling.
"""

import os
import sys
import unittest

# Add the src directory to the path for imports - must be before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parse_file import parse_directory  # noqa: E402
from dxf_handler import add_points_slice_to_dxf  # noqa: E402


class TestDXFHandler(unittest.TestCase):
    """Test the DXF handler functions."""

    def setUp(self):
        """Set up test environment."""
        self.test_data_dir = os.path.join(
            os.path.dirname(__file__), "testdata", "02_csv"
        )

    def test_add_all_slices_to_same_dxf(self):
        """Test adding all PointsSlice objects from 02_csv directory to the same DXF document."""
        print("\n" + "=" * 80)
        print(
            "TESTING: Adding ALL PointsSlice objects from 02_csv to same DXF document"
        )
        print("=" * 80)

        # Parse all CSV files in the directory using the efficient parse_directory function
        print(f"📂 Parsing directory: {self.test_data_dir}")

        points_slices = parse_directory(self.test_data_dir)

        print(f"✅ Successfully parsed {len(points_slices)} CSV files")

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

        dxf_doc = None

        for i, points_slice in enumerate(points_slices):
            color = color_palette[i % len(color_palette)]
            layer_name = f"SLICE_{i+1:02d}_{points_slice.name}"
            block_name = f"BLOCK_{i+1:02d}_{points_slice.name}"

            print(f"   📁 Adding slice {i+1}/{len(points_slices)}: {points_slice.name}")

            dxf_doc = add_points_slice_to_dxf(
                points_slice=points_slice,
                dxf_doc=dxf_doc,
                color=color,
                layer_name=layer_name,
                block_name=block_name,
                insert_position=(0.0, 0.0, 0.0),
                add_text_label=True,
                text_offset=(5.0, 5.0),
            )

        # Verify the DXF document structure
        print("🔍 Verifying DXF document structure...")

        # Check that all blocks exist
        block_names = [block.name for block in dxf_doc.blocks]
        slice_blocks = [name for name in block_names if name.startswith("BLOCK_")]
        self.assertEqual(len(slice_blocks), len(points_slices))
        print(f"   ✅ Found {len(slice_blocks)} slice blocks")

        # Check that all layers exist
        layer_names = [layer.dxf.name for layer in dxf_doc.layers]
        slice_layers = [name for name in layer_names if name.startswith("SLICE_")]
        self.assertEqual(len(slice_layers), len(points_slices))
        print(f"   ✅ Found {len(slice_layers)} slice layers")

        # Check that all blocks are referenced in modelspace
        modelspace = dxf_doc.modelspace()
        block_refs = [entity for entity in modelspace if entity.dxftype() == "INSERT"]

        # Verify each points slice has a corresponding block reference
        for points_slice in points_slices:
            matching_refs = [
                ref for ref in block_refs if points_slice.name in ref.dxf.name
            ]
            self.assertGreater(
                len(matching_refs),
                0,
                f"No block reference found for {points_slice.name}",
            )

        print(f"   ✅ Found {len(block_refs)} block references in modelspace")

        # Verify total points in all blocks
        total_points_in_dxf = 0

        for i, points_slice in enumerate(points_slices):
            block_name = f"BLOCK_{i+1:02d}_{points_slice.name}"
            block = dxf_doc.blocks.get(block_name)

            self.assertIsNotNone(block, f"No block found for {block_name}")

            if block:
                block_points = [
                    entity for entity in block if entity.dxftype() == "POINT"
                ]
                total_points_in_dxf += len(block_points)
                self.assertEqual(
                    len(block_points),
                    len(points_slice.points),
                    f"Point count mismatch in block {block_name}",
                )

        self.assertEqual(total_points_in_dxf, total_points_expected)
        print(
            f"   ✅ Total points verified: {total_points_in_dxf} points across all slices"
        )

        # Save to project root for easy inspection
        project_output = "test_all_slices_output.dxf"
        dxf_doc.saveas(project_output)
        print(f"💾 Test DXF saved to project root: {project_output}")
        print(
            f"📈 Performance summary: {len(points_slices)} files, {total_points_expected} total points"
        )

        print("✅ Test completed successfully!")


if __name__ == "__main__":
    unittest.main(verbosity=2)

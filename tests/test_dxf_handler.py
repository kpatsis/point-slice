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

from parse_file import parse_csv_file  # noqa: E402
from dxf_handler import add_points_slice_to_dxf  # noqa: E402


class TestDXFHandler(unittest.TestCase):
    """Test the DXF handler functions."""

    def setUp(self):
        """Set up test environment."""
        self.test_data_dir = os.path.join(
            os.path.dirname(__file__), "testdata", "02_csv"
        )

    def test_add_two_slices_to_same_dxf(self):
        """Test adding two PointsSlice objects to the same DXF document."""
        print("\n" + "=" * 80)
        print("TESTING: Adding two PointsSlice objects to same DXF document")
        print("=" * 80)

        # Test file paths
        csv_file_1 = os.path.join(self.test_data_dir, "01_-1f_L.csv")
        csv_file_2 = os.path.join(self.test_data_dir, "04_2f_L.csv")

        # Verify test files exist
        self.assertTrue(
            os.path.exists(csv_file_1), f"Test file not found: {csv_file_1}"
        )
        self.assertTrue(
            os.path.exists(csv_file_2), f"Test file not found: {csv_file_2}"
        )

        # Parse the first CSV file
        print(f"📁 Parsing first file: {os.path.basename(csv_file_1)}")
        points_slice_1 = parse_csv_file(csv_file_1)
        print(f"   📊 Points: {len(points_slice_1.points)}")
        print(f"   🎯 Type: {points_slice_1.slice_type.value}")
        print(f"   📛 Name: {points_slice_1.name}")

        # Parse the second CSV file
        print(f"📁 Parsing second file: {os.path.basename(csv_file_2)}")
        points_slice_2 = parse_csv_file(csv_file_2)
        print(f"   📊 Points: {len(points_slice_2.points)}")
        print(f"   🎯 Type: {points_slice_2.slice_type.value}")
        print(f"   📛 Name: {points_slice_2.name}")

        # Add first slice to the document
        print("➕ Adding first PointsSlice to DXF...")
        dxf_doc = add_points_slice_to_dxf(
            points_slice=points_slice_1,
            color=5,  # Blue color
            layer_name="SLICE_1_LAYER",
            block_name="SLICE_1_BLOCK",
            insert_position=(0.0, 0.0, 0.0),
            add_text_label=True,
            text_offset=(5.0, 5.0),
        )

        # Add second slice to the same document
        print("➕ Adding second PointsSlice to same DXF...")
        dxf_doc = add_points_slice_to_dxf(
            points_slice=points_slice_2,
            dxf_doc=dxf_doc,
            color=1,  # Red color
            layer_name="SLICE_2_LAYER",
            block_name="SLICE_2_BLOCK",
            insert_position=(0.0, 0.0, 0.0),  # Offset in Y direction
            add_text_label=True,
            text_offset=(5.0, 5.0),
        )

        # Verify the DXF document structure
        print("🔍 Verifying DXF document structure...")

        # Check that both blocks exist
        block_names = [block.name for block in dxf_doc.blocks]
        self.assertIn("SLICE_1_BLOCK", block_names)
        self.assertIn("SLICE_2_BLOCK", block_names)
        print(
            f"   ✅ Found blocks: {[name for name in block_names if 'SLICE_' in name]}"
        )

        # Check that both layers exist
        layer_names = [layer.dxf.name for layer in dxf_doc.layers]
        self.assertIn("SLICE_1_LAYER", layer_names)
        self.assertIn("SLICE_2_LAYER", layer_names)
        print(
            f"   ✅ Found layers: {[name for name in layer_names if 'SLICE_' in name]}"
        )

        # Check that both blocks are referenced in modelspace
        modelspace = dxf_doc.modelspace()
        block_refs = [entity for entity in modelspace if entity.dxftype() == "INSERT"]
        block_ref_names = [ref.dxf.name for ref in block_refs]
        self.assertIn("SLICE_1_BLOCK", block_ref_names)
        self.assertIn("SLICE_2_BLOCK", block_ref_names)
        print(f"   ✅ Found block references: {block_ref_names}")

        # Verify points in blocks
        slice_1_block = dxf_doc.blocks.get("SLICE_1_BLOCK")
        slice_2_block = dxf_doc.blocks.get("SLICE_2_BLOCK")

        # Count points in each block
        slice_1_points = [
            entity for entity in slice_1_block if entity.dxftype() == "POINT"
        ]
        slice_2_points = [
            entity for entity in slice_2_block if entity.dxftype() == "POINT"
        ]

        self.assertEqual(len(slice_1_points), len(points_slice_1.points))
        self.assertEqual(len(slice_2_points), len(points_slice_2.points))
        print(f"   ✅ Slice 1 block contains {len(slice_1_points)} points")
        print(f"   ✅ Slice 2 block contains {len(slice_2_points)} points")

        # save to project root for easy inspection
        project_output = "test_two_slices_output.dxf"
        dxf_doc.saveas(project_output)
        print(f"💾 Test DXF saved to project root: {project_output}")

        print("✅ Test completed successfully!")


if __name__ == "__main__":
    unittest.main(verbosity=2)

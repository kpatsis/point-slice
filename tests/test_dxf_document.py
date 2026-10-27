#!/usr/bin/env python3

import os
import unittest

import ezdxf

from ps_core.dxf_document import DXFDocument, Block, XDATA_APPID
from ps_core.parse_file import parse_directory
from ps_core.points_slice import (
    Point3D,
    PointsSlice,
    SectionLine,
    SliceType,
    rotate_slice_to_xy,
)


class TestDXFDocument(unittest.TestCase):
    """Test the DXFDocument class functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_data_dir = os.path.join(
            os.path.dirname(__file__), "testdata", "02_csv"
        )
        self.output_file = "test_output.dxf"

    def test_parse_and_create_dxf_complete_workflow(self):
        """Test complete workflow: parse CSV files, create blocks, plot, and save."""
        print("\n" + "=" * 80)
        print("COMPLETE DXF DOCUMENT WORKFLOW TEST")
        print("=" * 80)

        # Step 1: Parse all CSV files from the test data directory
        print(f"📂 Parsing CSV files from: {self.test_data_dir}")
        points_slices = parse_directory(self.test_data_dir)

        print(f"✅ Successfully parsed {len(points_slices)} CSV files")

        # Step 2: Create DXF document with custom colors and label position
        custom_colors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # More colors for variety
        label_position = (-40.0, 0.0)
        doc = DXFDocument(colors=custom_colors, label_start_position=label_position)
        print(f"📋 Created DXFDocument with {len(custom_colors)} colors")
        print(f"🏷️  Label start position: {label_position}")

        # Step 3: Add each PointsSlice as a block
        for points_slice in points_slices:
            if points_slice.slice_type == SliceType.XZ:
                block = Block(
                    points_slice=rotate_slice_to_xy(points_slice),
                    layer_name=f"Layer_{points_slice.name}",
                    block_name=f"Block_{points_slice.name}",
                    insert_position=(100.0, 0.0, 0.0),
                )
            elif points_slice.slice_type == SliceType.YZ:
                block = Block(
                    points_slice=rotate_slice_to_xy(points_slice),
                    layer_name=f"Layer_{points_slice.name}",
                    block_name=f"Block_{points_slice.name}",
                    insert_position=(200.0, 0.0, 0.0),
                )
            else:
                block = Block(
                    points_slice=points_slice,
                    layer_name=f"Layer_{points_slice.name}",
                    block_name=f"Block_{points_slice.name}",
                    insert_position=(0.0, 0.0, 0.0),
                )
            doc.add_block(block)

            print(
                f"➕ Added block '{points_slice.name}' with {len(points_slice.points)} points"
            )

        self.assertEqual(
            len(doc.blocks), len(points_slices), "Not all blocks were added"
        )
        print(f"📦 Total blocks in document: {len(doc.blocks)}")

        # Step 4: Plot all blocks to the DXF document
        print("🎨 Plotting blocks to DXF document...")
        doc.plot()
        self.assertIsNotNone(
            doc.dxf_doc, "DXF document should not be None after plotting"
        )
        print("✅ Successfully plotted all blocks")

        # Step 5: Save the DXF file
        print(f"💾 Saving DXF file to: {self.output_file}")
        doc.save(self.output_file)

        # Check file size (should be > 0)
        file_size = os.path.getsize(self.output_file)
        self.assertGreater(file_size, 0, "DXF file is empty")
        print(f"✅ DXF file saved successfully (size: {file_size} bytes)")

        # Step 6: Display summary
        print("\n📊 WORKFLOW SUMMARY:")
        print(f"   • CSV files parsed: {len(points_slices)}")
        print(f"   • Blocks created: {len(doc.blocks)}")
        print(f"   • Colors used: {len(custom_colors)}")
        print(f"   • Output file: {self.output_file}")
        print(f"   • File size: {file_size} bytes")
        print("=" * 80)

    def test_section_lines_replace_points(self):
        """A block with section lines and no points writes tagged LWPOLYLINEs."""
        points = [Point3D(float(i), 5.0, float(i)) for i in range(4)]
        points_slice = PointsSlice(points=points, name="wall", slice_type=SliceType.XZ)
        line = SectionLine(Point3D(0.0, 5.0, 1.5), Point3D(3.0, 5.0, 1.5))
        doc = DXFDocument()
        doc.add_block(
            Block(
                points_slice=points_slice,
                layer_name="L_wall",
                block_name="Block_wall",
                section_lines=[line],
                include_points=False,
            )
        )

        doc.plot()
        doc.save(self.output_file)

        block = ezdxf.readfile(self.output_file).blocks.get("Block_wall")
        polylines = block.query("LWPOLYLINE")
        self.assertEqual(len(polylines), 1)
        self.assertEqual(len(block.query("POINT")), 0)
        self.assertEqual([text.dxf.text for text in block.query("TEXT")], ["wall"])

        polyline = polylines[0]
        self.assertEqual(polyline.dxf.layer, "L_wall")
        self.assertAlmostEqual(polyline.dxf.elevation, 1.5)
        self.assertEqual(
            [(v[0], v[1]) for v in polyline.get_points(format="xy")],
            [(0.0, 5.0), (3.0, 5.0)],
        )
        xdata = [(tag.code, tag.value) for tag in polyline.get_xdata(XDATA_APPID)]
        self.assertEqual(xdata, [(1000, "wall"), (1070, 0)])


if __name__ == "__main__":
    unittest.main()

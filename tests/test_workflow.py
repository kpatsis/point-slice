#!/usr/bin/env python3
"""
Unit tests for the workflow module.

Tests cover the success/failure result of create_dxf_from_csv_directory,
the slice labels it writes and the experimental section lines.
"""

import contextlib
import io
import os
import shutil
import tempfile
import unittest

import ezdxf

from ps_core.workflow import create_dxf_from_csv_directory


class TestCreateDxfFromCsvDirectory(unittest.TestCase):
    """Test the create_dxf_from_csv_directory function."""

    def setUp(self):
        """Create a temporary directory holding one small XY slice CSV."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "csv")
        os.mkdir(self.input_dir)
        with open(os.path.join(self.input_dir, "slice.csv"), "w") as f:
            for i in range(10):
                f.write(f"{i}.0 {i * 2}.0 1.0\n")
        self.output_file = os.path.join(self.temp_dir, "out.dxf")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def run_workflow(self, input_dir, output_file, **kwargs):
        """Run the workflow with its output captured; return (result, output)."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = create_dxf_from_csv_directory(input_dir, output_file, **kwargs)
        return result, output.getvalue()

    def write_wall_csv(self):
        """Add an XZ slice (y = 5.0) with 10 points one unit apart along X."""
        with open(os.path.join(self.input_dir, "wall.csv"), "w") as f:
            for i in range(10):
                f.write(f"{i}.0 5.0 {i * 2}.0\n")

    def test_success_returns_true(self):
        """A valid run writes the DXF file and returns True."""
        result, _ = self.run_workflow(self.input_dir, self.output_file)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_file))

    def test_missing_input_directory_returns_false(self):
        """A non-existent input directory returns False."""
        missing_dir = os.path.join(self.temp_dir, "missing")

        result, output = self.run_workflow(missing_dir, self.output_file)

        self.assertFalse(result)
        self.assertIn("does not exist", output)
        self.assertFalse(os.path.exists(self.output_file))

    def test_directory_without_csv_files_returns_false(self):
        """An input directory with no CSV files returns False."""
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.mkdir(empty_dir)

        result, output = self.run_workflow(empty_dir, self.output_file)

        self.assertFalse(result)
        self.assertIn("Error parsing CSV files", output)
        self.assertFalse(os.path.exists(self.output_file))

    def test_save_failure_returns_false(self):
        """A DXF file that cannot be written returns False."""
        unwritable_file = os.path.join(self.temp_dir, "no_such_dir", "out.dxf")

        result, output = self.run_workflow(self.input_dir, unwritable_file)

        self.assertFalse(result)
        self.assertIn("Error saving DXF file", output)

    def read_names(self):
        """Return the (layer, block, label) names of the written DXF file."""
        doc = ezdxf.readfile(self.output_file)
        layers = {layer.dxf.name for layer in doc.layers if layer.dxf.name[:2] == "L_"}
        blocks = {block.name for block in doc.blocks if block.name[:6] == "Block_"}
        labels = {text.dxf.text for block in doc.blocks for text in block.query("TEXT")}
        return layers, blocks, labels

    def test_xy_names_include_level(self):
        """XY slice layer, block and label names are suffixed with the level."""
        self.run_workflow(self.input_dir, self.output_file)

        layers, blocks, labels = self.read_names()

        self.assertEqual(layers, {"L_slice+1.00"})
        self.assertEqual(blocks, {"Block_slice+1.00"})
        self.assertEqual(labels, {"slice+1.00"})

    def test_xz_names_have_no_level(self):
        """XZ slices, and their rotated copies, keep the plain name."""
        self.write_wall_csv()

        self.run_workflow(self.input_dir, self.output_file)

        layers, blocks, labels = self.read_names()

        self.assertEqual(layers, {"L_slice+1.00", "L_wall"})
        self.assertEqual(
            blocks, {"Block_slice+1.00", "Block_wall", "Block_wall_rotated"}
        )
        self.assertEqual(labels, {"slice+1.00", "wall", "wall_rotated"})

    def count_entities(self, block_name, entity_type):
        """Return how many entities of the given DXF type a block holds."""
        block = ezdxf.readfile(self.output_file).blocks.get(block_name)
        return len(block.query(entity_type))

    def test_section_lines_off_by_default(self):
        """Without the option every block is still a point cloud."""
        self.write_wall_csv()

        self.run_workflow(self.input_dir, self.output_file)

        self.assertEqual(self.count_entities("Block_wall", "LWPOLYLINE"), 0)
        self.assertEqual(self.count_entities("Block_wall", "POINT"), 10)
        self.assertEqual(self.count_entities("Block_wall_rotated", "POINT"), 10)

    def test_section_lines_replace_vertical_points_in_main_drawing(self):
        """Section lines replace the XZ points in Block_wall only."""
        self.write_wall_csv()

        result, output = self.run_workflow(
            self.input_dir, self.output_file, section_lines=True
        )

        self.assertTrue(result)
        self.assertIn("1 section line(s) replacing 10 points", output)
        self.assertEqual(self.count_entities("Block_wall", "LWPOLYLINE"), 1)
        self.assertEqual(self.count_entities("Block_wall", "POINT"), 0)
        self.assertEqual(self.count_entities("Block_wall_rotated", "LWPOLYLINE"), 0)
        self.assertEqual(self.count_entities("Block_wall_rotated", "POINT"), 10)
        self.assertEqual(self.count_entities("Block_slice+1.00", "LWPOLYLINE"), 0)
        self.assertEqual(self.count_entities("Block_slice+1.00", "POINT"), 10)

        layers, blocks, labels = self.read_names()
        self.assertEqual(layers, {"L_slice+1.00", "L_wall"})
        self.assertEqual(
            blocks, {"Block_slice+1.00", "Block_wall", "Block_wall_rotated"}
        )
        self.assertEqual(labels, {"slice+1.00", "wall", "wall_rotated"})

    def test_invalid_section_line_gap_returns_false(self):
        """A non-positive gap is reported and no file is written."""
        self.write_wall_csv()

        result, output = self.run_workflow(
            self.input_dir, self.output_file, section_lines=True, section_line_gap=0
        )

        self.assertFalse(result)
        self.assertIn("Error computing section lines", output)
        self.assertFalse(os.path.exists(self.output_file))


if __name__ == "__main__":
    unittest.main(verbosity=2)

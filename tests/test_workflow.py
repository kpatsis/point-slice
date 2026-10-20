#!/usr/bin/env python3
"""
Unit tests for the workflow module.

Tests cover the success/failure result of create_dxf_from_csv_directory.
"""

import contextlib
import io
import os
import shutil
import tempfile
import unittest

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

    def run_workflow(self, input_dir, output_file):
        """Run the workflow with its output captured; return (result, output)."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = create_dxf_from_csv_directory(input_dir, output_file)
        return result, output.getvalue()

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


if __name__ == "__main__":
    unittest.main(verbosity=2)

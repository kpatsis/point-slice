#!/usr/bin/env python3
"""
Unit tests for the parse_file module.

Tests cover slice type detection, color determination, file parsing,
and directory parsing functionality.
"""

import os
import sys

# Add the src directory to the path for imports - must be before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import shutil  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402

from parse_file import (  # noqa: E402
    detect_slice_type_from_data,
    parse_csv_file,
    parse_directory,
)
from points_slice import Point3D, SliceType, PointsSlice  # noqa: E402


class TestDetectSliceType(unittest.TestCase):
    """Test the detect_slice_type_from_data function."""

    def test_xy_slice_detection(self):
        """Test detection of XY slice (Z constant)."""
        # Create points with constant Z (5.0) and varying X, Y
        points = [Point3D(i, j, 5.0) for i in range(10) for j in range(10)]
        result = detect_slice_type_from_data(points)
        self.assertEqual(result, SliceType.XY)

    def test_xz_slice_detection(self):
        """Test detection of XZ slice (Y constant)."""
        # Create points with constant Y (3.0) and varying X, Z
        points = [Point3D(i, 3.0, k) for i in range(10) for k in range(10)]
        result = detect_slice_type_from_data(points)
        self.assertEqual(result, SliceType.XZ)

    def test_yz_slice_detection(self):
        """Test detection of YZ slice (X constant)."""
        # Create points with constant X (2.0) and varying Y, Z
        points = [Point3D(2.0, j, k) for j in range(10) for k in range(10)]
        result = detect_slice_type_from_data(points)
        self.assertEqual(result, SliceType.YZ)

    def test_unknown_slice_detection(self):
        """Test detection when no dimension is constant enough."""
        # Create 3D point cloud with significant variation in all dimensions
        points = [
            Point3D(i * 0.1, j * 0.1, k * 0.1)
            for i in range(10)
            for j in range(10)
            for k in range(10)
        ]
        result = detect_slice_type_from_data(points)
        self.assertEqual(result, SliceType.UNKNOWN)

    def test_empty_points_list(self):
        """Test behavior with empty points list."""
        points = []
        result = detect_slice_type_from_data(points)
        self.assertEqual(result, SliceType.UNKNOWN)

    def test_custom_threshold(self):
        """Test with custom threshold values."""
        # Create points with small but measurable Z variation
        points = [
            Point3D(i, j, 5.0 + k * 0.01)
            for i in range(5)
            for j in range(5)
            for k in range(3)
        ]

        # With strict threshold, should be UNKNOWN
        result_strict = detect_slice_type_from_data(points, threshold=0.005)
        self.assertEqual(result_strict, SliceType.UNKNOWN)

        # With loose threshold, should detect XY
        result_loose = detect_slice_type_from_data(points, threshold=0.05)
        self.assertEqual(result_loose, SliceType.XY)


class TestParseCSVFile(unittest.TestCase):
    """Test the parse_csv_file function."""

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()

        # Create a sample CSV file
        self.test_file = os.path.join(self.temp_dir, "test_data.csv")
        with open(self.test_file, "w") as f:
            # XY slice data (Z constant at ~5.0)
            for i in range(10):
                for j in range(10):
                    f.write(f"{i}.{i} {j}.{j} 5.000 100.0 0 201 54\n")

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def test_parse_valid_file(self):
        """Test parsing a valid CSV file."""
        result = parse_csv_file(self.test_file)

        self.assertIsInstance(result, PointsSlice)
        self.assertEqual(result.name, "test_data")
        self.assertEqual(len(result.points), 100)  # 10x10 grid
        self.assertEqual(result.slice_type, SliceType.XY)

    def test_parse_with_max_points(self):
        """Test parsing with max_points limit."""
        result = parse_csv_file(self.test_file, max_points=50)

        self.assertEqual(len(result.points), 50)
        self.assertEqual(result.slice_type, SliceType.XY)

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            parse_csv_file("nonexistent_file.csv")

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        empty_file = os.path.join(self.temp_dir, "empty.csv")
        with open(empty_file, "w"):
            pass  # Create empty file

        with self.assertRaises(ValueError):
            parse_csv_file(empty_file)

    def test_parse_invalid_format(self):
        """Test parsing file with invalid format."""
        invalid_file = os.path.join(self.temp_dir, "invalid.csv")
        with open(invalid_file, "w") as f:
            f.write("1.0 2.0\n")  # Only 2 values, need at least 3
            f.write("3.0 4.0 5.0\n")

        with self.assertRaises(ValueError):
            parse_csv_file(invalid_file)

    def test_parse_non_numeric_coordinates(self):
        """Test parsing file with non-numeric coordinates."""
        invalid_file = os.path.join(self.temp_dir, "non_numeric.csv")
        with open(invalid_file, "w") as f:
            f.write("abc def ghi\n")

        with self.assertRaises(ValueError):
            parse_csv_file(invalid_file)


class TestParseAllTestData(unittest.TestCase):
    """Test parsing all CSV files in the testdata/02_csv directory using parse_directory."""

    def setUp(self):
        """Set up paths for test data."""
        self.test_data_dir = os.path.join(
            os.path.dirname(__file__), "testdata", "02_csv"
        )
        self.assertTrue(
            os.path.exists(self.test_data_dir),
            f"Test data directory not found: {self.test_data_dir}",
        )

    def test_parse_directory_all_files(self):
        """Parse all CSV files using parse_directory function and analyze results."""
        print("\n" + "=" * 80)
        print("PARSING ALL TEST DATA FILES WITH parse_directory()")
        print("=" * 80)

        try:
            # Use parse_directory with limited points for faster testing
            import time
            start_time = time.time()
            results = parse_directory(self.test_data_dir)
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"⏱️  Parsing execution time: {execution_time:.4f} seconds")

            print(f"✅ Successfully parsed directory: {self.test_data_dir}")
            print(f"📊 Total slices parsed: {len(results)}")

            # Verify we have results
            self.assertGreater(len(results), 0, "No slices were parsed from directory")

            # Analyze each slice
            for i, slice_obj in enumerate(results, 1):
                print(f"\n📁 Slice {i}: {slice_obj.name}")
                print(f"   📊 Points parsed: {len(slice_obj.points)}")
                print(f"   🎯 Slice type: {slice_obj.slice_type.value}")

                # Validate that each slice is a PointsSlice object
                self.assertIsInstance(
                    slice_obj, PointsSlice, f"Result {i} is not a PointsSlice object"
                )
                self.assertGreater(
                    len(slice_obj.points), 0, f"Slice {slice_obj.name} has no points"
                )

        except Exception as e:
            self.fail(f"Failed to parse directory: {str(e)}")

        # Summary analysis
        print(f"\n" + "=" * 80)
        print("SUMMARY ANALYSIS")
        print("=" * 80)
        print(f"Total slices processed: {len(results)}")

        self.assertEqual(len(results), 10, f"Expected 6 files, got {len(results)}")

    def test_directory_error_handling(self):
        """Test error handling for parse_directory function."""
        # Test non-existent directory
        with self.assertRaises(FileNotFoundError):
            parse_directory("non_existent_directory")

        # Test empty directory (create temporary empty directory)
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                parse_directory(temp_dir)

        print("✅ Directory error handling tests passed!")


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""
Unit tests for the points_slice module.

Tests cover the slice thickness filter and the XY slice level label.
"""

import unittest

from ps_core.points_slice import (
    Point3D,
    PointsSlice,
    SliceType,
    filter_slice_thickness,
    format_level,
)


class TestFilterSliceThickness(unittest.TestCase):
    """Test the filter_slice_thickness function."""

    def test_issue_example_xy(self):
        """5 cm XY slice from +0.93 to +0.98 filtered to 1 cm keeps +0.95..+0.96."""
        levels = [0.93, 0.94, 0.95, 0.955, 0.96, 0.97, 0.98]
        points = [Point3D(i, i, z) for i, z in enumerate(levels)]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.XY)

        result = filter_slice_thickness(slice_obj, 0.01)

        self.assertEqual([p.z for p in result.points], [0.95, 0.955, 0.96])
        self.assertEqual(result.name, "s")
        self.assertEqual(result.slice_type, SliceType.XY)

    def test_uses_midpoint_not_mean(self):
        """Band is centred on the range midpoint, not on the mean of the points."""
        levels = [0.0] * 10 + [0.1]
        points = [Point3D(0.0, 0.0, z) for z in levels]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.XY)

        # Midpoint is 0.05, so the band 0.04..0.06 excludes every point
        result = filter_slice_thickness(slice_obj, 0.02)

        self.assertEqual(result.points, [])

    def test_xz_filters_on_y(self):
        """XZ slices are filtered along Y."""
        points = [Point3D(5.0, y, 5.0) for y in (1.0, 1.02, 1.04)]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.XZ)

        result = filter_slice_thickness(slice_obj, 0.01)

        self.assertEqual([p.y for p in result.points], [1.02])

    def test_yz_filters_on_x(self):
        """YZ slices are filtered along X."""
        points = [Point3D(x, 5.0, 5.0) for x in (2.0, 2.02, 2.04)]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.YZ)

        result = filter_slice_thickness(slice_obj, 0.01)

        self.assertEqual([p.x for p in result.points], [2.02])

    def test_unknown_slice_unchanged(self):
        """UNKNOWN slices keep all their points."""
        points = [Point3D(i, i, i) for i in range(5)]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.UNKNOWN)

        result = filter_slice_thickness(slice_obj, 0.01)

        self.assertEqual(result.points, points)
        self.assertEqual(result.slice_type, SliceType.UNKNOWN)

    def test_thinner_slice_unchanged(self):
        """Slices already thinner than the requested thickness keep all points."""
        points = [Point3D(i, i, 1.0 + i * 0.001) for i in range(5)]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.XY)

        result = filter_slice_thickness(slice_obj, 0.05)

        self.assertEqual(result.points, points)

    def test_does_not_mutate_input(self):
        """The original slice and its points are left untouched."""
        points = [Point3D(0.0, 0.0, z) for z in (0.0, 0.05, 0.1)]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.XY)

        result = filter_slice_thickness(slice_obj, 0.01)

        self.assertEqual(len(slice_obj.points), 3)
        self.assertIsNot(result.points[0], slice_obj.points[1])

    def test_non_positive_thickness_raises(self):
        """Zero or negative thickness is rejected."""
        slice_obj = PointsSlice(
            points=[Point3D(0.0, 0.0, 0.0)], name="s", slice_type=SliceType.XY
        )

        with self.assertRaises(ValueError):
            filter_slice_thickness(slice_obj, 0.0)
        with self.assertRaises(ValueError):
            filter_slice_thickness(slice_obj, -0.01)


class TestFormatLevel(unittest.TestCase):
    """Test the format_level function."""

    def test_issue_example(self):
        """Values from +0.93 to +0.98 have midpoint 0.955, rounded half-up."""
        self.assertEqual(format_level([0.93, 0.98]), "+0.96")

    def test_uses_midpoint_not_mean(self):
        """The level is the range midpoint, not the mean of the values."""
        self.assertEqual(format_level([0.0] * 10 + [0.1]), "+0.05")

    def test_rounds_half_up_despite_float_noise(self):
        """Midpoints stored just below a .xx5 boundary still round up."""
        # (2.135 + 2.145) / 2 is 2.1399999999999997 as a float
        self.assertEqual(format_level([2.135, 2.145]), "+2.14")
        self.assertEqual(format_level([1.005]), "+1.01")

    def test_negative_level(self):
        """Negative levels carry a minus sign."""
        self.assertEqual(format_level([-8.3542, -8.3402]), "-8.35")

    def test_zero_level_has_plus_sign(self):
        """A level that rounds to zero is "+0.00", never "-0.00"."""
        self.assertEqual(format_level([-0.001]), "+0.00")


if __name__ == "__main__":
    unittest.main(verbosity=2)

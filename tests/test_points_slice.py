#!/usr/bin/env python3
"""
Unit tests for the points_slice module.

Tests cover the slice thickness filter.
"""

import unittest

from ps_core.points_slice import (
    Point3D,
    PointsSlice,
    SliceType,
    filter_slice_thickness,
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

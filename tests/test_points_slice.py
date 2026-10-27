#!/usr/bin/env python3
"""
Unit tests for the points_slice module.

Tests cover the slice thickness filter, the plan-view section lines and
the XY slice level label.
"""

import random
import unittest

from ps_core.points_slice import (
    Point3D,
    PointsSlice,
    SliceType,
    filter_slice_thickness,
    format_level,
    section_lines,
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


class TestSectionLines(unittest.TestCase):
    """Test the section_lines function."""

    @staticmethod
    def xz_slice(x_values):
        """An XZ slice with points at the given X values, Y 4.99..5.01, Z 0..3."""
        points = [
            Point3D(x, 4.99 + 0.02 * (i % 2), 3.0 * (i % 4) / 3)
            for i, x in enumerate(x_values)
        ]
        return PointsSlice(points=points, name="s", slice_type=SliceType.XZ)

    def test_continuous_xz_slice_gives_one_line(self):
        """A continuous XZ slice is one line at the Y and Z midpoints."""
        slice_obj = self.xz_slice([0.0, 0.5, 1.0, 1.5, 2.0])

        lines = section_lines(slice_obj, 1.0)

        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].start, Point3D(0.0, 5.0, 1.5))
        self.assertEqual(lines[0].end, Point3D(2.0, 5.0, 1.5))

    def test_splits_at_gaps_larger_than_max_gap(self):
        """Stretches longer than max_gap break the line; shorter ones are bridged."""
        slice_obj = self.xz_slice([0.0, 0.5, 1.0, 3.0, 3.5, 4.0])

        two = section_lines(slice_obj, 1.0)
        one = section_lines(slice_obj, 2.5)

        self.assertEqual(
            [(line.start.x, line.end.x) for line in two], [(0.0, 1.0), (3.0, 4.0)]
        )
        self.assertEqual([(line.start.x, line.end.x) for line in one], [(0.0, 4.0)])

    def test_yz_slice_runs_along_y(self):
        """YZ slices lie on x = constant and run along Y."""
        points = [
            Point3D(1.99 + 0.02 * (i % 2), y, z)
            for i, (y, z) in enumerate([(0.0, 0.0), (1.0, 2.0), (2.0, 4.0)])
        ]
        slice_obj = PointsSlice(points=points, name="s", slice_type=SliceType.YZ)

        lines = section_lines(slice_obj, 1.0)

        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].start, Point3D(2.0, 0.0, 2.0))
        self.assertEqual(lines[0].end, Point3D(2.0, 2.0, 2.0))

    def test_isolated_point_gives_no_line(self):
        """A stretch made of a single point has no length and is dropped."""
        slice_obj = self.xz_slice([0.0, 0.5, 1.0, 5.0])

        lines = section_lines(slice_obj, 1.0)

        self.assertEqual([(line.start.x, line.end.x) for line in lines], [(0.0, 1.0)])

    def test_xy_unknown_and_empty_slices_give_no_lines(self):
        """Only vertical slices have plan-view lines."""
        points = [Point3D(float(i), float(i), 1.0) for i in range(3)]

        for slice_type in (SliceType.XY, SliceType.UNKNOWN):
            slice_obj = PointsSlice(points=points, name="s", slice_type=slice_type)
            self.assertEqual(section_lines(slice_obj, 1.0), [])

        empty = PointsSlice(points=[], name="s", slice_type=SliceType.XZ)
        self.assertEqual(section_lines(empty, 1.0), [])

    def test_non_positive_gap_raises(self):
        """Zero or negative gap is rejected."""
        slice_obj = self.xz_slice([0.0, 1.0])

        with self.assertRaises(ValueError):
            section_lines(slice_obj, 0.0)
        with self.assertRaises(ValueError):
            section_lines(slice_obj, -1.0)

    def test_point_order_does_not_matter(self):
        """Shuffling the input points gives the same lines."""
        x_values = [i * 0.1 for i in range(30)] + [5.0 + i * 0.1 for i in range(30)]
        slice_obj = self.xz_slice(x_values)
        expected = section_lines(slice_obj, 1.0)

        shuffled_points = list(slice_obj.points)
        random.Random(0).shuffle(shuffled_points)
        shuffled = PointsSlice(
            points=shuffled_points, name="s", slice_type=SliceType.XZ
        )

        self.assertEqual(section_lines(shuffled, 1.0), expected)
        self.assertEqual(len(expected), 2)


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

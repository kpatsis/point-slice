#!/usr/bin/env python3
"""
Unit tests for the points_slice module.

Tests cover translating slices, rotating slices to the XY plane, and the
combination of both, which is how rotated XZ/YZ blocks are placed relative
to the anchor point.
"""

import unittest

from ps_core.points_slice import (
    Point3D,
    PointsSlice,
    SliceType,
    rotate_slice_to_xy,
    translate_slice,
)

# Anchor of an imported point cloud with a large elevation offset
ANCHOR_X = 1000.0
ANCHOR_Y = 2000.0
ANCHOR_Z = 3000.0

XZ_ROTATED_X_OFFSET = -300.0
YZ_ROTATED_X_OFFSET = -200.0


def make_xz_slice() -> PointsSlice:
    """XZ slice (constant Y) of a cloud anchored at (1000, 2000, 3000)."""
    points = [
        Point3D(ANCHOR_X + i, ANCHOR_Y, ANCHOR_Z + k)
        for i in range(10)
        for k in range(10)
    ]
    return PointsSlice(points=points, name="xz_slice", slice_type=SliceType.XZ)


def make_yz_slice() -> PointsSlice:
    """YZ slice (constant X) of a cloud anchored at (1000, 2000, 3000)."""
    points = [
        Point3D(ANCHOR_X, ANCHOR_Y + j, ANCHOR_Z + k)
        for j in range(10)
        for k in range(10)
    ]
    return PointsSlice(points=points, name="yz_slice", slice_type=SliceType.YZ)


class TestTranslateSlice(unittest.TestCase):
    """Test the translate_slice function."""

    def test_points_are_shifted(self):
        original = PointsSlice(
            points=[Point3D(1.0, 2.0, 3.0), Point3D(-1.0, -2.0, -3.0)],
            name="slice",
            slice_type=SliceType.XY,
        )

        result = translate_slice(original, (10.0, 20.0, 30.0))

        self.assertEqual(
            [(p.x, p.y, p.z) for p in result.points],
            [(11.0, 22.0, 33.0), (9.0, 18.0, 27.0)],
        )

    def test_metadata_is_preserved(self):
        original = make_xz_slice()

        result = translate_slice(original, (-ANCHOR_X, -ANCHOR_Y, -ANCHOR_Z))

        self.assertEqual(result.name, original.name)
        self.assertEqual(result.slice_type, SliceType.XZ)

    def test_original_slice_is_not_modified(self):
        original = PointsSlice(
            points=[Point3D(1.0, 2.0, 3.0)], name="slice", slice_type=SliceType.XY
        )

        translate_slice(original, (5.0, 5.0, 5.0))

        self.assertEqual(
            (original.points[0].x, original.points[0].y, original.points[0].z),
            (1.0, 2.0, 3.0),
        )


class TestRotateSliceToXY(unittest.TestCase):
    """Test the rotate_slice_to_xy function."""

    def test_xz_slice_maps_z_to_y(self):
        slice_obj = PointsSlice(
            points=[Point3D(1.0, 2.0, 3.0)], name="slice", slice_type=SliceType.XZ
        )

        result = rotate_slice_to_xy(slice_obj)

        self.assertEqual((result.points[0].x, result.points[0].y), (1.0, 3.0))
        self.assertEqual(result.slice_type, SliceType.XY)
        self.assertEqual(result.name, "slice_rotated")

    def test_yz_slice_maps_y_to_x_and_z_to_y(self):
        slice_obj = PointsSlice(
            points=[Point3D(1.0, 2.0, 3.0)], name="slice", slice_type=SliceType.YZ
        )

        result = rotate_slice_to_xy(slice_obj)

        self.assertEqual((result.points[0].x, result.points[0].y), (2.0, 3.0))
        self.assertEqual(result.slice_type, SliceType.XY)


class TestAnchorLocalRotation(unittest.TestCase):
    """
    Test translating into anchor-local space before rotating.

    This is what the DXF workflow does so that a point cloud with a large
    X/Y/Z offset still produces rotated blocks next to the anchor point.
    """

    def rotate_around_anchor(self, slice_obj: PointsSlice) -> PointsSlice:
        local_slice = translate_slice(slice_obj, (-ANCHOR_X, -ANCHOR_Y, -ANCHOR_Z))
        return rotate_slice_to_xy(local_slice)

    def test_xz_rotated_coordinates_are_local(self):
        rotated = self.rotate_around_anchor(make_xz_slice())

        # Local extents stay in the size range of the slice itself (0..9),
        # instead of carrying the 1000/3000 world offsets
        self.assertEqual(min(p.x for p in rotated.points), 0.0)
        self.assertEqual(max(p.x for p in rotated.points), 9.0)
        self.assertEqual(min(p.y for p in rotated.points), 0.0)
        self.assertEqual(max(p.y for p in rotated.points), 9.0)

    def test_yz_rotated_coordinates_are_local(self):
        rotated = self.rotate_around_anchor(make_yz_slice())

        self.assertEqual(min(p.x for p in rotated.points), 0.0)
        self.assertEqual(max(p.x for p in rotated.points), 9.0)
        self.assertEqual(min(p.y for p in rotated.points), 0.0)
        self.assertEqual(max(p.y for p in rotated.points), 9.0)

    def test_xz_world_placement_follows_anchor_and_offset(self):
        slice_obj = make_xz_slice()
        rotated = self.rotate_around_anchor(slice_obj)
        insert_position = (ANCHOR_X + XZ_ROTATED_X_OFFSET, ANCHOR_Y, 0.0)

        world = [
            (p.x + insert_position[0], p.y + insert_position[1]) for p in rotated.points
        ]
        expected = [
            (p.x + XZ_ROTATED_X_OFFSET, ANCHOR_Y + (p.z - ANCHOR_Z))
            for p in slice_obj.points
        ]

        self.assertEqual(world, expected)

    def test_yz_world_placement_follows_anchor_and_offset(self):
        slice_obj = make_yz_slice()
        rotated = self.rotate_around_anchor(slice_obj)
        insert_position = (ANCHOR_X + YZ_ROTATED_X_OFFSET, ANCHOR_Y, 0.0)

        world = [
            (p.x + insert_position[0], p.y + insert_position[1]) for p in rotated.points
        ]
        expected = [
            (
                ANCHOR_X + YZ_ROTATED_X_OFFSET + (p.y - ANCHOR_Y),
                ANCHOR_Y + (p.z - ANCHOR_Z),
            )
            for p in slice_obj.points
        ]

        self.assertEqual(world, expected)

    def test_rotated_block_stays_near_anchor_despite_z_offset(self):
        """A large elevation offset must not push the block away vertically."""
        rotated = self.rotate_around_anchor(make_xz_slice())
        insert_y = ANCHOR_Y

        max_world_y = max(p.y + insert_y for p in rotated.points)

        self.assertLess(abs(max_world_y - ANCHOR_Y), 100.0)


if __name__ == "__main__":
    unittest.main()

"""
DXF file handler for PointsSlice objects.

This module provides functionality to export PointsSlice objects to DXF files
as blocks with customizable colors and layers.
"""

import ezdxf
from typing import Optional
from points_slice import PointsSlice


def add_points_slice_to_dxf(
    points_slice: PointsSlice,
    dxf_doc: Optional[ezdxf.document.Drawing] = None,
    color: int = 7,
    layer_name: Optional[str] = None,
    block_name: Optional[str] = None,
    insert_position: tuple[float, float, float] = (0.0, 0.0, 0.0),
    text_position: tuple[float, float] = None,
) -> ezdxf.document.Drawing:
    """
    Add a PointsSlice object to a DXF file as a single block.

    Args:
        points_slice: The PointsSlice object to add to the DXF file
        dxf_doc: Existing DXF document to add to (creates new if None)
        color: AutoCAD color index (0-256), default is 7 (white)
        layer_name: Name of the layer to create points on (uses points_slice.name if None)
        block_name: Name for the block (uses points_slice.name if None)
        insert_position: Position where to insert the block reference (x, y, z)
        add_text_label: Whether to add a text label with slice information
        text_offset: Offset for text label relative to first point

    Returns:
        The DXF document with the added block

    Raises:
        ValueError: If points_slice is empty or invalid
    """
    if not points_slice.points:
        raise ValueError("PointsSlice contains no points")

    # Create new document if none provided
    if dxf_doc is None:
        dxf_doc = ezdxf.new(setup=True)

    # Set default names if not provided
    if layer_name is None:
        layer_name = points_slice.name
    if block_name is None:
        block_name = points_slice.name

    # Create the layer if it doesn't exist
    if layer_name not in dxf_doc.layers:
        dxf_doc.layers.add(layer_name, color=color)

    # Create a new block definition
    block = dxf_doc.blocks.new(name=block_name, dxfattribs={"layer": layer_name})

    # Add all points to the block
    for point in points_slice.points:
        location = (
            round(point.x, 4),
            round(point.y, 4),
            round(point.z, 4),
        )
        block.add_point(location, dxfattribs={"layer": layer_name})

    # Add text label if requested
    if text_position:
        first_point = points_slice.points[0]
        text_position = (
            text_position[0],
            text_position[1],
            first_point.z,
        )

        label_text = f"{points_slice.name}"

        text_entity = block.add_text(
            label_text,
            dxfattribs={"height": 0.5, "layer": layer_name},
        )
        text_entity.set_placement(text_position)

    # Insert the block into the modelspace
    modelspace = dxf_doc.modelspace()
    modelspace.add_blockref(
        block_name, insert=insert_position, dxfattribs={"layer": layer_name}
    )

    return dxf_doc

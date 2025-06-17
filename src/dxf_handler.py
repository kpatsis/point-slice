"""
DXF file handler for PointsSlice objects.

This module provides functionality to export PointsSlice objects to DXF files
as blocks with customizable colors and layers.
"""

import ezdxf
from typing import Optional, Union
from pathlib import Path
from points_slice import PointsSlice


def add_points_slice_to_dxf(
    points_slice: PointsSlice,
    dxf_doc: Optional[ezdxf.document.Drawing] = None,
    color: int = 7,
    layer_name: Optional[str] = None,
    block_name: Optional[str] = None,
    insert_position: tuple[float, float, float] = (0.0, 0.0, 0.0),
    add_text_label: bool = True,
    text_offset: tuple[float, float] = (0.0, 5.0),
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
        block.add_point((point.x, point.y, point.z), dxfattribs={"layer": layer_name})

    # Add text label if requested
    if add_text_label and points_slice.points:
        first_point = points_slice.points[0]
        text_position = (
            first_point.x + text_offset[0],
            first_point.y + text_offset[1],
            first_point.z,
        )

        # Calculate average Z coordinate for the label
        avg_z = sum(p.z for p in points_slice.points) / len(points_slice.points)

        label_text = f"{points_slice.name} | Type: {points_slice.slice_type.value} | Points: {len(points_slice.points)} | Avg Z: {avg_z:.2f}"

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


def save_points_slice_to_dxf(
    points_slice: PointsSlice,
    filepath: Union[str, Path],
    color: int = 7,
    layer_name: Optional[str] = None,
    block_name: Optional[str] = None,
    add_text_label: bool = True,
) -> None:
    """
    Save a single PointsSlice object to a new DXF file.

    Args:
        points_slice: The PointsSlice object to save
        filepath: Path where to save the DXF file
        color: AutoCAD color index (0-256), default is 7 (white)
        layer_name: Name of the layer (uses points_slice.name if None)
        block_name: Name for the block (uses points_slice.name if None)
        add_text_label: Whether to add a text label with slice information

    Raises:
        ValueError: If points_slice is empty or invalid
    """
    dxf_doc = add_points_slice_to_dxf(
        points_slice=points_slice,
        color=color,
        layer_name=layer_name,
        block_name=block_name,
        add_text_label=add_text_label,
    )

    dxf_doc.saveas(str(filepath))


def add_multiple_points_slices_to_dxf(
    points_slices: list[PointsSlice],
    dxf_doc: Optional[ezdxf.document.Drawing] = None,
    color_palette: Optional[list[int]] = None,
    layer_prefix: str = "slice_",
    spacing_offset: float = 50.0,
    add_text_labels: bool = True,
) -> ezdxf.document.Drawing:
    """
    Add multiple PointsSlice objects to a DXF file as separate blocks.

    Args:
        points_slices: List of PointsSlice objects to add
        dxf_doc: Existing DXF document to add to (creates new if None)
        color_palette: List of AutoCAD color indices to cycle through
        layer_prefix: Prefix for layer names
        spacing_offset: Y-offset between each slice when inserted
        add_text_labels: Whether to add text labels

    Returns:
        The DXF document with all added blocks

    Raises:
        ValueError: If points_slices is empty
    """
    if not points_slices:
        raise ValueError("No PointsSlice objects provided")

    # Create new document if none provided
    if dxf_doc is None:
        dxf_doc = ezdxf.new(setup=True)

    # Default color palette
    if color_palette is None:
        color_palette = [
            5,
            4,
            2,
            3,
            30,
            1,
            6,
            241,
        ]  # blue, cyan, yellow, green, orange, red, magenta, pink

    # Add each slice as a separate block
    for i, points_slice in enumerate(points_slices):
        color = color_palette[i % len(color_palette)]
        layer_name = f"{layer_prefix}{points_slice.name}"
        insert_position = (0.0, -i * spacing_offset, 0.0)

        add_points_slice_to_dxf(
            points_slice=points_slice,
            dxf_doc=dxf_doc,
            color=color,
            layer_name=layer_name,
            insert_position=insert_position,
            add_text_label=add_text_labels,
        )

    return dxf_doc


def save_multiple_points_slices_to_dxf(
    points_slices: list[PointsSlice],
    filepath: Union[str, Path],
    color_palette: Optional[list[int]] = None,
    layer_prefix: str = "slice_",
    spacing_offset: float = 50.0,
    add_text_labels: bool = True,
) -> None:
    """
    Save multiple PointsSlice objects to a new DXF file.

    Args:
        points_slices: List of PointsSlice objects to save
        filepath: Path where to save the DXF file
        color_palette: List of AutoCAD color indices to cycle through
        layer_prefix: Prefix for layer names
        spacing_offset: Y-offset between each slice when inserted
        add_text_labels: Whether to add text labels

    Raises:
        ValueError: If points_slices is empty
    """
    dxf_doc = add_multiple_points_slices_to_dxf(
        points_slices=points_slices,
        color_palette=color_palette,
        layer_prefix=layer_prefix,
        spacing_offset=spacing_offset,
        add_text_labels=add_text_labels,
    )

    dxf_doc.saveas(str(filepath))

# Point Slice Studio - Convert CSV point cloud data to DXF format
# Copyright (C) 2024 Kostas Patsis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
import ezdxf
from typing import Optional, List
from ps_core.points_slice import PointsSlice


@dataclass
class Block:
    points_slice: PointsSlice
    layer_name: Optional[str] = None
    block_name: Optional[str] = None
    insert_position: Optional[tuple[float, float, float]] = (0.0, 0.0, 0.0)
    # Reference point the label offset is applied to, in world coordinates.
    # Blocks sharing a reference point get their labels stacked in one column,
    # so labels stay next to the geometry they name.
    label_origin: Optional[tuple[float, float, float]] = None


class DXFDocument:
    def __init__(
        self,
        colors: List[int] = None,
        label_start_position: tuple[float, float] = (0.0, 0.0),
    ):
        """
        Initialize DXF document with optional color list and label position.

        Args:
            colors: List of AutoCAD color indices (0-256) to use in round-robin fashion.
                   If None, defaults to [1, 2, 3, 4, 5, 6] (red, yellow, green, cyan, blue, magenta)
            label_start_position: Offset (x, y) of the first label from a block's
                                label origin. Subsequent labels of the same origin
                                are placed below it.
        """
        self.blocks: List[Block] = []
        self.dxf_doc: ezdxf.document.Drawing = ezdxf.new(setup=True)
        self.colors = colors or [1, 2, 3, 4, 5, 6]  # Default colors
        self.color_index = 0
        self.label_start_position = label_start_position
        self.text_height = 0.5
        self.text_spacing = 0.7  # Space between labels
        # Next free label y per label column, keyed by the column's (x, y) origin
        self.next_label_y: dict[tuple[float, float], float] = {}

    def add_block(self, block: Block):
        self.blocks.append(block)

    def _next_label_position(self, block: Block) -> tuple[float, float, float]:
        """
        Reserve the next label position for a block's label column.

        The label is offset from the block's label origin, so every group of
        blocks sharing an origin (the point cloud, the rotated XZ view, the
        rotated YZ view) gets its own column of labels.

        Args:
            block: The block whose label is about to be placed

        Returns:
            Label position (x, y, z) in world coordinates
        """
        origin = block.label_origin or (0.0, 0.0, 0.0)
        column = (origin[0], origin[1])

        if column not in self.next_label_y:
            self.next_label_y[column] = origin[1] + self.label_start_position[1]

        label_y = self.next_label_y[column]
        self.next_label_y[column] -= self.text_spacing

        return (origin[0] + self.label_start_position[0], label_y, 0.0)

    def save(self, filename: str):
        """
        Save the DXF document to a file.

        Args:
            filename: Path and filename where to save the DXF file (e.g., "output.dxf")
        """
        self.dxf_doc.saveas(filename)

    def plot(self):
        """
        Insert all blocks in the list into the DXF document.
        """
        for block in self.blocks:
            # Validate that points_slice has points
            if not block.points_slice.points:
                continue

            # Set default names if not provided
            layer_name = block.layer_name or block.points_slice.name
            block_name = block.block_name or block.points_slice.name

            # Create the layer if it doesn't exist
            if layer_name not in self.dxf_doc.layers:
                # Get color in round-robin fashion only when creating a new layer
                color = self.colors[self.color_index % len(self.colors)]
                self.color_index += 1
                self.dxf_doc.layers.add(layer_name, color=color)

            # Create a new block definition
            dxf_block = self.dxf_doc.blocks.new(
                name=block_name, dxfattribs={"layer": layer_name}
            )

            # Add all points to the block
            for point in block.points_slice.points:
                location = (
                    round(point.x, 4),
                    round(point.y, 4),
                    round(point.z, 4),
                )
                dxf_block.add_point(location, dxfattribs={"layer": layer_name})

            # Insert the block into the modelspace
            modelspace = self.dxf_doc.modelspace()
            modelspace.add_blockref(
                block_name,
                insert=block.insert_position,
                dxfattribs={"layer": layer_name},
            )

            # Add the label to the modelspace rather than to the block
            # definition, so the block insert position does not drag it away
            # from the column it belongs to
            text_entity = modelspace.add_text(
                block.points_slice.name,
                dxfattribs={"height": self.text_height, "layer": layer_name},
            )
            text_entity.set_placement(self._next_label_position(block))

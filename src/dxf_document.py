from dataclasses import dataclass
import ezdxf
from typing import Optional, List
from points_slice import PointsSlice


@dataclass
class Block:
    points_slice: PointsSlice
    layer_name: Optional[str] = None
    block_name: Optional[str] = None
    insert_position: Optional[tuple[float, float, float]] = (0.0, 0.0, 0.0)


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
            label_start_position: Starting position (x, y) for the first label. Subsequent labels
                                will be placed below this position.
        """
        self.blocks: List[Block] = []
        self.dxf_doc: ezdxf.document.Drawing = ezdxf.new(setup=True)
        self.colors = colors or [1, 2, 3, 4, 5, 6]  # Default colors
        self.color_index = 0
        self.label_start_position = label_start_position
        self.current_label_y = label_start_position[1]
        self.text_height = 0.5
        self.text_spacing = 0.7  # Space between labels

    def add_block(self, block: Block):
        self.blocks.append(block)

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

            # Add label text
            label_text = block.points_slice.name
            label_position = (self.label_start_position[0], self.current_label_y, 0.0)

            text_entity = dxf_block.add_text(
                label_text, dxfattribs={"height": self.text_height, "layer": layer_name}
            )
            text_entity.set_placement(label_position)

            # Move to next label position
            self.current_label_y -= self.text_spacing

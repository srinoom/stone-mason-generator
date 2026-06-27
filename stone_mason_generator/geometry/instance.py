"""Instance Engine — instances stone prototypes on points and realizes them.

Refactored in Step 11: delegates mesh creation to a StonePrimitive
instead of creating a cube inline.

Pipeline stage (runs AFTER BondEngine):

    Points (shifted by bond offset)
      → StonePrimitive.build() → stone mesh
      → Instance on Points
      → Realize Instances
      → Output Geometry
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .primitive import StonePrimitive, CubePrimitive


class InstanceEngine:
    """Instances a StonePrimitive on points and realizes the result."""

    # No own sockets — primitive provides its own
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def __init__(self, primitive: StonePrimitive = None):
        self.primitive = primitive or CubePrimitive()

    @property
    def primitive_sockets(self) -> List[Tuple[str, str, str, object]]:
        """Sockets required by the stone primitive."""
        return self.primitive.SOCKETS

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the instancing sub-tree.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).
            prev_geometry: Previous geometry node (shifted points from BondEngine).

        Returns:
            Realize Instances node — final geometry output.
        """
        g = graph

        # --- stone mesh from primitive library ---
        stone_mesh = self.primitive.build(g, group_input)

        # --- instance stones on points ---
        inst = g.instance_on_points(location=(0, 0))
        g.link(prev_geometry.outputs[0],
               inst.inputs["Points"])
        g.link(stone_mesh.outputs["Mesh"],
               inst.inputs["Instance"])

        # --- realize ---
        realize = g.realize_instances(location=(300, 0))
        g.link(inst.outputs["Instances"],
               realize.inputs["Geometry"])

        return realize

"""Instance Engine -- places stone prototypes on points and realizes them.

Created in Step 8 architecture review.  Previously instancing and
realization lived inside ScatterEngine.  Now separated so that
BondEngine can shift point positions BEFORE stones are placed.

Pipeline stage (runs AFTER BondEngine):

    Points (shifted by bond offset)
      → Instance Mesh Cube on Points (stone prototype)
      → Realize Instances
      → Output Geometry
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class InstanceEngine:
    """Instances stone prototypes on points and realizes the result."""

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Stone Width",  "INPUT", "NodeSocketFloat", 0.50),
        ("Stone Height", "INPUT", "NodeSocketFloat", 0.25),
    ]

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

        # --- stone prototype (cube scaled to stone dimensions) ---
        combine_size = g.combine_xyz(location=(-200, -300))
        g.link(group_input.outputs["Stone Width"],
               combine_size.inputs["X"])
        g.link(group_input.outputs["Stone Height"],
               combine_size.inputs["Y"])
        g.link(group_input.outputs["Stone Width"],
               combine_size.inputs["Z"])

        stone = g.cube(location=(0, -300))
        g.link(combine_size.outputs["Vector"],
               stone.inputs["Size"])

        # --- instance stones on points ---
        inst = g.instance_on_points(location=(0, 0))
        g.link(prev_geometry.outputs[0],
               inst.inputs["Points"])
        g.link(stone.outputs["Mesh"],
               inst.inputs["Instance"])

        # --- realize ---
        realize = g.realize_instances(location=(300, 0))
        g.link(inst.outputs["Instances"],
               realize.inputs["Geometry"])

        return realize


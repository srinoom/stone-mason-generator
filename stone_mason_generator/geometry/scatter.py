"""Scatter Engine -- distributes stone instances on a mesh surface.

Pipeline:
    Input Geometry (with course attributes from CourseEngine)
      → Distribute Points on Faces (density-driven)
      → Instance Mesh Cube (stone prototype)
      → Realize Instances
      → Output Geometry

ScatterEngine is unchanged from Step 5. It does not know about courses
directly — face attributes from CourseEngine transfer to generated
points automatically by Blender's geometry-node attribute propagation.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class ScatterEngine:
    """Distributes stone instances across a mesh surface."""

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Density",      "INPUT", "NodeSocketFloat", 50.0),
        ("Seed",         "INPUT", "NodeSocketInt",   0),
        ("Stone Width",  "INPUT", "NodeSocketFloat", 0.50),
        ("Stone Height", "INPUT", "NodeSocketFloat", 0.25),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the scatter sub-tree.

        Args:
            graph: NodeGraph wrapper for the active node group.
            group_input: Group Input node (for parameter access).
            prev_geometry: Previous geometry output node to chain from.

        Returns:
            The final output node of this engine (Realize Instances).
        """
        g = graph

        # --- distribute points on faces ---
        distribute = g.distribute_points_on_faces(location=(-400, 0))
        distribute.distribute_method = 'RANDOM'  # type: ignore[assignment]

        g.link(prev_geometry.outputs["Geometry"],
               distribute.inputs["Mesh"])
        g.link(group_input.outputs["Density"],
               distribute.inputs["Density"])
        g.link(group_input.outputs["Seed"],
               distribute.inputs["Seed"])

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
        g.link(distribute.outputs["Points"],
               inst.inputs["Points"])
        g.link(stone.outputs["Mesh"],
               inst.inputs["Instance"])

        # --- realize ---
        realize = g.realize_instances(location=(300, 0))
        g.link(inst.outputs["Instances"],
               realize.inputs["Geometry"])

        return realize


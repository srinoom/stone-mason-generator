"""Scatter Engine -- distributes points on a mesh surface.

Refactored in Step 8 architecture review:
  - ScatterEngine now ONLY distributes points (no instance/realize)
  - InstanceEngine handles instancing and realization
  - This lets BondEngine shift point positions BEFORE stones are placed

Pipeline:
    Input Geometry (with course_index from CourseEngine)
      → Distribute Points on Faces (density-driven)
      → Output Points (course_index transfers via attribute interpolation)
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class ScatterEngine:
    """Distributes points across a mesh surface.

    Returns a Points geometry — does NOT instance or realize.
    Downstream engines (BondEngine, InstanceEngine) operate on
    these points.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Density", "INPUT", "NodeSocketFloat", 50.0),
        ("Seed",    "INPUT", "NodeSocketInt",   0),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the point-distribution sub-tree.

        Returns the Distribute Points node whose ``Points`` output
        carries course_index (transferred from mesh faces).
        """
        g = graph

        distribute = g.distribute_points_on_faces(location=(-400, 0))
        distribute.distribute_method = 'RANDOM'  # type: ignore[assignment]

        g.link(prev_geometry.outputs["Geometry"],
               distribute.inputs["Mesh"])
        g.link(group_input.outputs["Density"],
               distribute.inputs["Density"])
        g.link(group_input.outputs["Seed"],
               distribute.inputs["Seed"])

        return distribute


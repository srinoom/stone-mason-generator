"""Course Engine -- generates horizontal masonry courses.

Refactored in Step 10: reads v_coord (from ParameterizeEngine)
instead of world-space Z. CourseEngine no longer calls WallFrame
directly — the ParameterizeEngine stores v_coord as an attribute,
and CourseEngine reads it.

Pipeline stage (runs AFTER ParameterizeEngine):

    Geometry (with v_coord attribute)
      → read v_coord
      → v_coord / Course Height → Floor → course_index
      → store course_index (FLOAT, POINT)
      → course_index * Course Height → course_base_v
      → store course_base_v (FLOAT, POINT)
      → Output Geometry (with course attributes)
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class CourseEngine:
    """Divides a mesh into horizontal courses based on v_coord.

    v_coord is provided by ParameterizeEngine — CourseEngine never
    reads world coordinates.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Course Height", "INPUT", "NodeSocketFloat", 0.5),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the course-generation sub-tree from v_coord."""
        g = graph

        # --- read v_coord (stored by ParameterizeEngine) ---
        read_v = g.named_attribute(location=(-400, 0))
        read_v.data_type = 'FLOAT'
        read_v.inputs["Name"].default_value = "v_coord"

        # --- course_index = floor(v_coord / course_height) ---
        div = g.math('DIVIDE', location=(-250, 0))
        g.link(read_v.outputs["Attribute"], div.inputs[0])
        g.link(group_input.outputs["Course Height"], div.inputs[1])

        floor = g.math('FLOOR', location=(-150, 0))
        g.link(div.outputs[0], floor.inputs[0])

        # --- store course_index on POINT domain ---
        store_idx = g.store_named_attribute(location=(-50, 0))
        store_idx.data_type = 'FLOAT'
        store_idx.domain = 'POINT'
        store_idx.inputs["Name"].default_value = "course_index"
        g.link(prev_geometry.outputs["Geometry"], store_idx.inputs["Geometry"])
        g.link(floor.outputs[0], store_idx.inputs["Value"])

        # --- course_base_v = course_index * course_height ---
        mul = g.math('MULTIPLY', location=(50, -50))
        g.link(floor.outputs[0], mul.inputs[0])
        g.link(group_input.outputs["Course Height"], mul.inputs[1])

        # --- store course_base_v on POINT domain ---
        store_base = g.store_named_attribute(location=(150, 0))
        store_base.data_type = 'FLOAT'
        store_base.domain = 'POINT'
        store_base.inputs["Name"].default_value = "course_base_v"
        g.link(store_idx.outputs[0], store_base.inputs["Geometry"])
        g.link(mul.outputs[0], store_base.inputs["Value"])

        return store_base



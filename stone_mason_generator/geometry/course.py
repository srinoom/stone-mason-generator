"""Course Engine -- generates horizontal masonry courses.

Refactored in Step 7 to use a WallFrame for coordinate abstraction.
CourseEngine no longer reads world-space Z directly — it asks the
WallFrame for the wall-local vertical (V) coordinate.

This means the same CourseEngine works on flat, sloped, and curved
walls without modification — only the WallFrame implementation changes.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .wall_frame import WallFrame, ZUpFrame


class CourseEngine:
    """Divides a mesh into horizontal courses based on wall-local height.

    The vertical coordinate comes from a WallFrame, not from world Z.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Course Height", "INPUT", "NodeSocketFloat", 0.5),
    ]

    def __init__(self, frame: WallFrame = None):
        """Use *frame* for coordinate conversion, or Z-up by default."""
        self.frame = frame or ZUpFrame()

    @property
    def frame_sockets(self) -> List[Tuple[str, str, str, object]]:
        """Sockets required by the WallFrame implementation."""
        return self.frame.SOCKETS

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the course-generation sub-tree.

        Returns the final node whose ``Geometry`` output carries
        course attributes — ready for the next engine in the chain.
        """
        g = graph

        # --- wall-local height (V) from WallFrame ---
        v_node = self.frame.build_v(g, group_input, prev_geometry)

        # v_node is a SeparateXYZ node; its "Z" output is the height scalar.
        # This abstraction lets WallFrame swap Z-up for any other axis/frame.

        # --- course_index = floor(V / course_height) ---
        div = g.math('DIVIDE', location=(-250, 150))
        g.link(v_node.outputs["Z"], div.inputs[0])
        g.link(group_input.outputs["Course Height"], div.inputs[1])

        floor = g.math('FLOOR', location=(-150, 150))
        g.link(div.outputs[0], floor.inputs[0])

        # --- store course_index on POINT domain ---
        store_idx = g.store_named_attribute(location=(-50, 150))
        store_idx.data_type = 'FLOAT'
        store_idx.domain = 'POINT'
        store_idx.inputs["Name"].default_value = "course_index"
        g.link(prev_geometry.outputs[0], store_idx.inputs[0])
        g.link(floor.outputs[0], store_idx.inputs["Value"])

        # --- course_base_v = course_index * course_height ---
        mul = g.math('MULTIPLY', location=(50, 80))
        g.link(floor.outputs[0], mul.inputs[0])
        g.link(group_input.outputs["Course Height"], mul.inputs[1])

        # --- store course_base_v on POINT domain ---
        store_base = g.store_named_attribute(location=(150, 150))
        store_base.data_type = 'FLOAT'
        store_base.domain = 'POINT'
        store_base.inputs["Name"].default_value = "course_base_v"
        g.link(store_idx.outputs[0], store_base.inputs[0])
        g.link(mul.outputs[0], store_base.inputs["Value"])

        return store_base


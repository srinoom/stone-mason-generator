"""Course Engine -- generates horizontal masonry courses on a mesh.

Pipeline stage (runs BEFORE ScatterEngine):

    Input Mesh
      → Bounding Box (wall orientation detection)
      → Position → Separate XYZ → Z
      → Z / Course Height → Floor → course_index
      → Store course_index  (attribute, POINT domain)
      → course_index * Course Height → course_base_z
      → Store course_base_z (attribute, POINT domain)
      → Output Mesh (with course attributes)

Every vertex on the mesh receives a course_index and course_base_z.
When ScatterEngine distributes points on faces, the face attributes
transfer to the generated points, so every scattered point belongs
to a course.

Wall orientation: Z-axis is assumed as the vertical (height) direction,
which is the standard Blender convention.  The Bounding Box node is
wired so future steps can auto-detect the up axis from dimensions.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class CourseEngine:
    """Divides a mesh into horizontal courses based on Z-position.

    Exposes Course Height as an interface socket so the user can
    control course spacing from the panel.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Course Height", "INPUT", "NodeSocketFloat", 0.5),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the course-generation sub-tree.

        Returns the final node whose ``Geometry`` output carries
        course attributes — ready for the next engine in the chain.
        """
        g = graph

        # --- wall orientation: bounding box (for future auto-detect) ---
        # Wired but not yet used to drive the up axis.
        # Z-up is assumed for standard Blender walls.
        bbox = g.bounding_box(location=(-500, -400))
        g.link(prev_geometry.outputs[0], bbox.inputs[0])

        # --- course_index = floor(position.z / course_height) ---
        pos = g.position(location=(-450, 150))
        sep = g.separate_xyz(location=(-350, 150))
        g.link(pos.outputs[0], sep.inputs["Vector"])

        div = g.math('DIVIDE', location=(-250, 150))
        g.link(sep.outputs["Z"], div.inputs[0])
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

        # --- course_base_z = course_index * course_height ---
        mul = g.math('MULTIPLY', location=(50, 80))
        g.link(floor.outputs[0], mul.inputs[0])
        g.link(group_input.outputs["Course Height"], mul.inputs[1])

        # --- store course_base_z on POINT domain ---
        store_base = g.store_named_attribute(location=(150, 150))
        store_base.data_type = 'FLOAT'
        store_base.domain = 'POINT'
        store_base.inputs["Name"].default_value = "course_base_z"
        g.link(store_idx.outputs[0], store_base.inputs[0])
        g.link(mul.outputs[0], store_base.inputs["Value"])

        return store_base


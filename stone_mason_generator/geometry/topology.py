"""Surface Topology — boundary and adjacency detection.

Pipeline stage (runs AFTER ParameterizeEngine, BEFORE CourseEngine):

    Mesh (with u_coord, v_coord, n_coord)
      → detect top/bottom/left/right boundaries
      → store boundary attributes
      → Output Mesh (with topology attributes)

Topology attributes stored:
  - is_top_boundary    (BOOL, POINT) — near v_max
  - is_bottom_boundary (BOOL, POINT) — near v_min
  - is_left_boundary   (BOOL, POINT) — near u_min
  - is_right_boundary  (BOOL, POINT) — near u_max
  - is_corner          (BOOL, POINT) — boundary intersection

Future stages (openings, arches, curved-wall seams) will extend
this engine without modifying CourseEngine or LayoutStrategy.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .surface_context import SurfaceContext


class SurfaceTopology:
    """Detects wall boundaries and corners from surface coordinates.

    Uses the SurfaceContext bounds (u_min, u_max, v_min, v_max) to
    identify which vertices lie on the wall perimeter. These
    attributes let future engines leave gaps for openings, handle
    edges differently, or detect arch spring points.
    """

    # No extra interface sockets
    SOCKETS: List[Tuple[str, str, str, object]] = []

    # How close to a bound (in local units) counts as "boundary".
    # Stored as a socket so it can be tuned per-project.
    BOUNDARY_TOLERANCE = 0.001

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node,
              ctx: SurfaceContext) -> bpy.types.Node:
        """Store boundary/corner attributes on the mesh.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node.
            prev_geometry: Previous geometry node.
            ctx: SurfaceContext with bounds computed by ParameterizeEngine.

        Returns:
            Final Store Named Attribute node (geometry with topology attrs).
        """
        g = graph

        # --- read u_coord and v_coord ---
        read_u = g.named_attribute(location=(-200, 0))
        read_u.data_type = 'FLOAT'
        read_u.inputs["Name"].default_value = "u_coord"

        read_v = g.named_attribute(location=(-200, -100))
        read_v.data_type = 'FLOAT'
        read_v.inputs["Name"].default_value = "v_coord"

        # --- is_top_boundary: v_coord >= v_max - tolerance ---
        top_thresh = g.math('SUBTRACT', location=(-50, 150))
        g.link(ctx.v_max.outputs["Max"], top_thresh.inputs[0])
        top_thresh.inputs[1].default_value = self.BOUNDARY_TOLERANCE

        is_top = g.math('GREATER_THAN', location=(50, 150))
        g.link(read_v.outputs["Attribute"], is_top.inputs[0])
        g.link(top_thresh.outputs[0], is_top.inputs[1])

        store_top = g.store_named_attribute(location=(150, 150))
        store_top.data_type = 'FLOAT'
        store_top.domain = 'POINT'
        store_top.inputs["Name"].default_value = "is_top_boundary"
        g.link(prev_geometry.outputs["Geometry"],
               store_top.inputs["Geometry"])
        g.link(is_top.outputs[0], store_top.inputs["Value"])

        # --- is_bottom_boundary: v_coord <= v_min + tolerance ---
        bot_thresh = g.math('ADD', location=(-50, 50))
        g.link(ctx.v_min.outputs["Min"], bot_thresh.inputs[0])
        bot_thresh.inputs[1].default_value = self.BOUNDARY_TOLERANCE

        is_bot = g.math('LESS_THAN', location=(50, 50))
        g.link(read_v.outputs["Attribute"], is_bot.inputs[0])
        g.link(bot_thresh.outputs[0], is_bot.inputs[1])

        store_bot = g.store_named_attribute(location=(150, 50))
        store_bot.data_type = 'FLOAT'
        store_bot.domain = 'POINT'
        store_bot.inputs["Name"].default_value = "is_bottom_boundary"
        g.link(store_top.outputs[0], store_bot.inputs["Geometry"])
        g.link(is_bot.outputs[0], store_bot.inputs["Value"])

        # --- is_left_boundary: u_coord <= u_min + tolerance ---
        left_thresh = g.math('ADD', location=(-50, -50))
        g.link(ctx.u_min.outputs["Min"], left_thresh.inputs[0])
        left_thresh.inputs[1].default_value = self.BOUNDARY_TOLERANCE

        is_left = g.math('LESS_THAN', location=(50, -50))
        g.link(read_u.outputs["Attribute"], is_left.inputs[0])
        g.link(left_thresh.outputs[0], is_left.inputs[1])

        store_left = g.store_named_attribute(location=(150, -50))
        store_left.data_type = 'FLOAT'
        store_left.domain = 'POINT'
        store_left.inputs["Name"].default_value = "is_left_boundary"
        g.link(store_bot.outputs[0], store_left.inputs["Geometry"])
        g.link(is_left.outputs[0], store_left.inputs["Value"])

        # --- is_right_boundary: u_coord >= u_max - tolerance ---
        right_thresh = g.math('SUBTRACT', location=(-50, -150))
        g.link(ctx.u_max.outputs["Max"], right_thresh.inputs[0])
        right_thresh.inputs[1].default_value = self.BOUNDARY_TOLERANCE

        is_right = g.math('GREATER_THAN', location=(50, -150))
        g.link(read_u.outputs["Attribute"], is_right.inputs[0])
        g.link(right_thresh.outputs[0], is_right.inputs[1])

        store_right = g.store_named_attribute(location=(150, -150))
        store_right.data_type = 'FLOAT'
        store_right.domain = 'POINT'
        store_right.inputs["Name"].default_value = "is_right_boundary"
        g.link(store_left.outputs[0], store_right.inputs["Geometry"])
        g.link(is_right.outputs[0], store_right.inputs["Value"])

        # --- is_corner: (top OR bottom) AND (left OR right) ---
        # top + bottom
        tb = g.math('ADD', location=(300, 100))
        g.link(is_top.outputs[0], tb.inputs[0])
        g.link(is_bot.outputs[0], tb.inputs[1])

        # left + right
        lr = g.math('ADD', location=(300, 0))
        g.link(is_left.outputs[0], lr.inputs[0])
        g.link(is_right.outputs[0], lr.inputs[1])

        # tb * lr (both > 0 means corner)
        corner = g.math('MULTIPLY', location=(400, 50))
        g.link(tb.outputs[0], corner.inputs[0])
        g.link(lr.outputs[0], corner.inputs[1])

        store_corner = g.store_named_attribute(location=(500, 50))
        store_corner.data_type = 'FLOAT'
        store_corner.domain = 'POINT'
        store_corner.inputs["Name"].default_value = "is_corner"
        g.link(store_right.outputs[0], store_corner.inputs["Geometry"])
        g.link(corner.outputs[0], store_corner.inputs["Value"])

        return store_corner





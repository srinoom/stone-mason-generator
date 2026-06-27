"""Surface Parameterization Engine — converts world coordinates to wall-local UVN.

Pipeline stage (runs FIRST):

    Input Mesh
      → WallFrame.build_u / build_v / build_n
      → SurfaceContext.from_graph() stores u_coord, v_coord, n_coord
        and computes u_min, u_max, v_min, v_max, width, height
      → Output: mesh with UVN attributes + SurfaceContext for downstream

The SurfaceContext is passed through the Composer to CourseLayout
and future engines so they consume pre-computed bounds instead of
querying Attribute Statistics themselves.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .wall_frame import WallFrame, ZUpFrame
from .surface_context import SurfaceContext


class ParameterizeEngine:
    """Stores wall-local UVN coordinates and computes surface bounds.

    Produces a SurfaceContext that downstream engines consume.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = []

    def __init__(self, frame: WallFrame = None):
        self.frame = frame or ZUpFrame()

    @property
    def frame_sockets(self) -> List[Tuple[str, str, str, object]]:
        return self.frame.SOCKETS

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Store UVN attributes and compute bounds via SurfaceContext."""
        g = graph

        u_sep = self.frame.build_u(g, group_input, prev_geometry)
        v_sep = self.frame.build_v(g, group_input, prev_geometry)
        n_node = self.frame.build_n(g, group_input, prev_geometry)

        ctx = SurfaceContext.from_graph(
            g, group_input, prev_geometry, u_sep, v_sep, n_node
        )

        # Stash context on the graph so Composer can pass it downstream
        g.surface_context = ctx

        return ctx.geometry_out


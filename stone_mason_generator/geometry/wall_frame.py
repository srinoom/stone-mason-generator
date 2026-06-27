"""Wall Frame -- local surface coordinate system abstraction.

Provides wall-local coordinates (U, V, N) for every point on a mesh:
  - U: along the wall (horizontal run direction)
  - V: up the wall (vertical height direction)
  - N: normal to the wall surface (depth direction)

ParameterizeEngine calls these methods to store u_coord, v_coord,
n_coord as named attributes. All downstream engines read those
attributes instead of world coordinates.

Subclass WallFrame to support curved walls, sloped walls, fireplaces,
etc. — the downstream engines need no modification.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class WallFrame:
    """Abstract base: provides wall-local surface coordinates (U, V, N).

    Subclasses override build_u, build_v, build_n.
    """

    # Interface sockets this frame needs on the node group
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build_u(self, graph: NodeGraph,
                 group_input: bpy.types.Node,
                 geometry: bpy.types.Node) -> bpy.types.Node:
        """Return a SeparateXYZ node; U = outputs['X'] (along-wall)."""
        raise NotImplementedError

    def build_v(self, graph: NodeGraph,
                group_input: bpy.types.Node,
                geometry: bpy.types.Node) -> bpy.types.Node:
        """Return a SeparateXYZ node; V = outputs['Z'] (up-wall)."""
        raise NotImplementedError

    def build_n(self, graph: NodeGraph,
                group_input: bpy.types.Node,
                geometry: bpy.types.Node) -> bpy.types.Node:
        """Return an InputNormal node; N = outputs['Normal'] (surface normal)."""
        raise NotImplementedError


class ZUpFrame(WallFrame):
    """Z-up world-space frame — the simplest wall coordinate system.

    U = world X (along the wall)
    V = world Z (up the wall)
    N = surface normal (from geometry)

    This preserves the behaviour of all previous steps for flat,
    axis-aligned walls.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build_u(self, graph: NodeGraph,
                 group_input: bpy.types.Node,
                 geometry: bpy.types.Node) -> bpy.types.Node:
        pos = graph.position(location=(-500, 200))
        sep = graph.separate_xyz(location=(-400, 200))
        graph.link(pos.outputs[0], sep.inputs["Vector"])
        return sep  # outputs["X"] = U

    def build_v(self, graph: NodeGraph,
                group_input: bpy.types.Node,
                geometry: bpy.types.Node) -> bpy.types.Node:
        pos = graph.position(location=(-500, 150))
        sep = graph.separate_xyz(location=(-400, 150))
        graph.link(pos.outputs[0], sep.inputs["Vector"])
        return sep  # outputs["Z"] = V

    def build_n(self, graph: NodeGraph,
                group_input: bpy.types.Node,
                geometry: bpy.types.Node) -> bpy.types.Node:
        return graph.input_normal(location=(-400, 100))


class BoundingBoxFrame(WallFrame):
    """Auto-orient frame based on bounding-box dominant axis.

    Stub for future use — currently delegates to ZUpFrame.
    The interface is defined so ParameterizeEngine can already accept
    any WallFrame without knowing which concrete frame is in use.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build_u(self, graph: NodeGraph,
                 group_input: bpy.types.Node,
                 geometry: bpy.types.Node) -> bpy.types.Node:
        frame = ZUpFrame()
        return frame.build_u(graph, group_input, geometry)

    def build_v(self, graph: NodeGraph,
                 group_input: bpy.types.Node,
                 geometry: bpy.types.Node) -> bpy.types.Node:
        frame = ZUpFrame()
        return frame.build_v(graph, group_input, geometry)

    def build_n(self, graph: NodeGraph,
                 group_input: bpy.types.Node,
                 geometry: bpy.types.Node) -> bpy.types.Node:
        frame = ZUpFrame()
        return frame.build_n(graph, group_input, geometry)

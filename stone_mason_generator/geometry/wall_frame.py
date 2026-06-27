"""Wall Frame -- local coordinate system abstraction.

Separates "coordinate provider" from "course generation".

A WallFrame converts world-space positions into wall-local coordinates:
  - U: along the wall (horizontal run)
  - V: up the wall (vertical height)
  - N: normal to the wall surface (depth)

CourseEngine asks WallFrame for V (height) instead of reading world Z,
so the same CourseEngine works on flat, sloped, and curved walls
without modification.

This module provides the abstraction + a default Z-up implementation.
Future implementations (BoundingBoxFrame, CurveFrame, etc.) plug in
by subclassing WallFrame and overriding ``build_v``.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class WallFrame:
    """Abstract base: provides wall-local vertical (V) coordinate.

    Subclasses override :meth:`build_v` to extract a height scalar
    from a geometry.  The default implementation is Z-up (world space).
    """

    # Interface sockets this frame needs on the node group
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build_v(self, graph: NodeGraph,
                group_input: bpy.types.Node,
                geometry: bpy.types.Node) -> bpy.types.Node:
        """Return a node whose output 0 is a scalar: wall-local height.

        Default: world-space Z (simple axis-aligned wall).
        """
        pos = graph.position(location=(-450, 150))
        sep = graph.separate_xyz(location=(-350, 150))
        graph.link(pos.outputs[0], sep.inputs["Vector"])
        # sep.outputs["Z"] is the height scalar
        return sep


class ZUpFrame(WallFrame):
    """Z-up world-space frame — the simplest wall coordinate system.

    V = world Z.  Compatible with Step 6 behaviour.
    """

    # No extra sockets needed
    SOCKETS: List[Tuple[str, str, str, object]] = []


class BoundingBoxFrame(WallFrame):
    """Auto-orient frame based on bounding-box dominant axis.

    Detects the longest bounding-box dimension and treats the
    perpendicular vertical as "up".  Falls back to Z-up if the
    bounding box is ambiguous (e.g. a flat plane on the ground).

    This is a stub for future use — currently delegates to ZUpFrame.
    The interface is defined so CourseEngine can already accept
    any WallFrame without knowing which concrete frame is in use.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build_v(self, graph: NodeGraph,
                group_input: bpy.types.Node,
                geometry: bpy.types.Node) -> bpy.types.Node:
        # TODO: detect dominant axis from Bounding Box dimensions
        # For now, delegate to Z-up
        frame = ZUpFrame()
        return frame.build_v(graph, group_input, geometry)


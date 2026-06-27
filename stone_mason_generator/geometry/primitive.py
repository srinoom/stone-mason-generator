"""Stone Primitive Library — base mesh prototypes only.

Refactored in Step 12: primitives only define the base mesh.
Surface irregularities (noise, edge damage, etc.) are now handled
by the StoneModifier stack (see modifier.py).

Primitives:
  - CubePrimitive:        unit cube (backward compatible)
  - RectangularBlock:    box with separate width/height/depth
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class StonePrimitive:
    """Abstract base for stone mesh prototypes.

    Subclasses override :meth:`build` to produce a base mesh node.
    No surface modification happens here — that is the job of
    StoneModifier subclasses applied afterwards.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node) -> bpy.types.Node:
        """Return a node whose ``Mesh`` output is the base stone mesh.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).

        Returns:
            A node with a ``Mesh`` output socket.
        """
        raise NotImplementedError


class CubePrimitive(StonePrimitive):
    """Unit cube — backward compatible with Steps 9-10.

    Uses Stone Width and Stone Height from the interface.
    Depth defaults to Stone Width.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Stone Width",  "INPUT", "NodeSocketFloat", 0.50),
        ("Stone Height", "INPUT", "NodeSocketFloat", 0.25),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node) -> bpy.types.Node:
        g = graph

        combine = g.combine_xyz(location=(-200, -300))
        g.link(group_input.outputs["Stone Width"],  combine.inputs["X"])
        g.link(group_input.outputs["Stone Height"], combine.inputs["Y"])
        g.link(group_input.outputs["Stone Width"],  combine.inputs["Z"])

        cube = g.cube(location=(0, -300))
        g.link(combine.outputs["Vector"], cube.inputs["Size"])

        return cube


class RectangularBlock(StonePrimitive):
    """Rectangular block with independent width, height, and depth.

    Adds a Stone Depth parameter so stones can extend into the wall
    rather than being cubic.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Stone Width",  "INPUT", "NodeSocketFloat", 0.50),
        ("Stone Height", "INPUT", "NodeSocketFloat", 0.25),
        ("Stone Depth",  "INPUT", "NodeSocketFloat", 0.30),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node) -> bpy.types.Node:
        g = graph

        combine = g.combine_xyz(location=(-200, -300))
        g.link(group_input.outputs["Stone Width"],  combine.inputs["X"])
        g.link(group_input.outputs["Stone Height"], combine.inputs["Y"])
        g.link(group_input.outputs["Stone Depth"],  combine.inputs["Z"])

        cube = g.cube(location=(0, -300))
        g.link(combine.outputs["Vector"], cube.inputs["Size"])

        return cube

"""Stone Modifier Stack — surface irregularity pipeline.

Modifiers are applied sequentially to the base mesh produced by a
StonePrimitive. Each modifier takes a geometry node and returns a
geometry node, forming a stack:

    Primitive.build() → base mesh
      → Modifier[0].apply()
      → Modifier[1].apply()
      → ...
      → final mesh → InstanceEngine

Modifiers:
  - NoiseModifier: subdivide + displace vertices along normal via noise

Future modifiers (not yet implemented):
  - EdgeDamage, CornerBreak, SurfaceChipping, Bevel
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class StoneModifier:
    """Abstract base for stone surface modifiers.

    Subclasses override :meth:`apply` to transform the input mesh.

    A modifier may declare its own interface sockets via :attr:`SOCKETS`
    so the Composer can expose them in the node group interface.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node) -> bpy.types.Node:
        """Transform the input mesh and return the result node.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).
            mesh_node: Previous node in the stack (output is a Mesh).

        Returns:
            A node whose geometry output is the modified mesh.
        """
        raise NotImplementedError


class NoiseModifier(StoneModifier):
    """Subdivide mesh and displace vertices along normal using noise.

    Parameters:
      - Roughness: displacement amount (0 = no effect)
      - Noise Scale: frequency of the noise pattern
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Roughness",    "INPUT", "NodeSocketFloat", 0.05),
        ("Noise Scale",  "INPUT", "NodeSocketFloat", 5.0),
    ]

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node) -> bpy.types.Node:
        g = graph

        # --- subdivide for displacement resolution ---
        subd = g.node("GeometryNodeSubdivideMesh", location=(100, -300),
                       label="Subdivide")
        subd.inputs["Level"].default_value = 2
        g.link(mesh_node.outputs["Mesh"], subd.inputs["Mesh"])

        # --- noise texture ---
        noise = g.node("ShaderNodeTexNoise", location=(100, -450),
                       label="Displacement Noise")
        g.link(group_input.outputs["Noise Scale"],
               noise.inputs["Scale"])

        # --- roughness * noise → displacement scalar ---
        disp_amount = g.math('MULTIPLY', location=(250, -400))
        g.link(noise.outputs["Fac"], disp_amount.inputs[0])
        g.link(group_input.outputs["Roughness"], disp_amount.inputs[1])

        # --- normal × displacement → offset vector ---
        normal = g.input_normal(location=(200, -500))

        offset_vec = g.vector_math('SCALE', location=(350, -400))
        g.link(normal.outputs["Normal"], offset_vec.inputs[0])
        g.link(disp_amount.outputs[0], offset_vec.inputs["Scale"])

        # --- set position: offset along normal ---
        set_pos = g.set_position(location=(500, -300))
        g.link(subd.outputs["Mesh"], set_pos.inputs["Geometry"])
        g.link(offset_vec.outputs["Vector"], set_pos.inputs["Offset"])

        return set_pos

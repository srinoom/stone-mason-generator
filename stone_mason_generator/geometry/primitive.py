"""Stone Primitive Library — mesh prototypes for instancing.

Each primitive is a Geometry Nodes sub-tree that produces a mesh
to be instanced on layout points. InstanceEngine calls the active
primitive's :meth:`build` instead of creating a cube directly.

Primitives:
  - CubePrimitive:        unit cube (backward compatible)
  - RectangularBlock:    box with separate width/height/depth
  - RoughBlock:          box with subdivided faces + noise displacement

Future: Fieldstone, RiverRock, AshlarBlock, etc.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class StonePrimitive:
    """Abstract base for stone mesh prototypes.

    Subclasses override :meth:`build` to produce a mesh node whose
    ``Mesh`` output is ready for Instance-on-Points.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node) -> bpy.types.Node:
        """Return a node whose output is the stone mesh.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).

        Returns:
            A node with a ``Mesh`` output socket.
        """
        raise NotImplementedError


class CubePrimitive(StonePrimitive):
    """Unit cube — backward compatible with Step 9/10 behaviour.

    Uses Stone Width and Stone Height from the interface, same as the
    old InstanceEngine inline cube.  Depth defaults to Stone Width.
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


class RoughBlock(StonePrimitive):
    """Rough block — subdivided cube with noise displacement on vertices.

    Produces an irregular stone shape by:
      1. Creating a cube
      2. Subdividing it (Subdivision Surface node, simple mode)
      3. Displacing vertices along normal using a Noise texture

    Amount is controlled by Roughness parameter (0 = smooth block).
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Stone Width",  "INPUT", "NodeSocketFloat", 0.50),
        ("Stone Height", "INPUT", "NodeSocketFloat", 0.25),
        ("Stone Depth",  "INPUT", "NodeSocketFloat", 0.30),
        ("Roughness",    "INPUT", "NodeSocketFloat", 0.05),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node) -> bpy.types.Node:
        g = graph

        # --- base cube with dimensions ---
        combine = g.combine_xyz(location=(-300, -300))
        g.link(group_input.outputs["Stone Width"],  combine.inputs["X"])
        g.link(group_input.outputs["Stone Height"], combine.inputs["Y"])
        g.link(group_input.outputs["Stone Depth"],  combine.inputs["Z"])

        cube = g.cube(location=(-100, -300))
        g.link(combine.outputs["Vector"], cube.inputs["Size"])

        # --- subdivide for displacement resolution ---
        subd = g.node("GeometryNodeSubdivideMesh", location=(100, -300),
                       label="Subdivide for Roughness")
        subd.inputs["Level"].default_value = 2
        g.link(cube.outputs["Mesh"], subd.inputs["Mesh"])

        # --- noise texture for displacement ---
        noise = g.node("ShaderNodeTexNoise", location=(100, -450),
                       label="Roughness Noise")
        noise.inputs["Scale"].default_value = 5.0

        # --- scale noise by Roughness ---
        scale_noise = g.math('MULTIPLY', location=(250, -400))
        g.link(noise.outputs["Fac"], scale_noise.inputs[0])
        g.link(group_input.outputs["Roughness"], scale_noise.inputs[1])

        # --- set position: offset along normal by noise * roughness ---
        set_pos = g.set_position(location=(300, -300))
        set_pos.inputs["Offset"].default_value = (0, 0, 0)
        g.link(subd.outputs["Mesh"], set_pos.inputs["Geometry"])

        # We need to offset each vertex along its normal. In Geometry Nodes
        # the Set Position Offset socket takes a vector. We multiply the
        # noise scalar by the vertex normal (auto-available in the field
        # context) to get a directional offset.
        normal = g.input_normal(location=(200, -500))

        # noise_scalar * normal_vector → offset vector
        offset_vec = g.vector_math('SCALE', location=(350, -400))
        g.link(normal.outputs["Normal"], offset_vec.inputs[0])
        g.link(scale_noise.outputs[0], offset_vec.inputs["Scale"])

        g.link(offset_vec.outputs["Vector"], set_pos.inputs["Offset"])

        return set_pos

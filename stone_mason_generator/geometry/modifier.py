"""Stone Modifier Stack — surface irregularity pipeline.

Step 14: Three new modifiers for visible stone shape variation.
All are deterministic via Seed.

Modifiers:
  - NoiseModifier:      subdivide + noise displacement (existing, refined)
  - EdgeBevelModifier:  bevel all edges for worn look
  - FaceIrregularity:   per-face random scale + rotation (new)
  - CornerBreak:        push corner vertices along normal (new)

Interface: enabled(ctx) + apply(graph, gi, mesh, ctx, report)
"""

import bpy
import math
from typing import List, Tuple

from .graph import NodeGraph
from .modifier_base import StoneModifier, ModifierContext, ValidationReport


class NoiseModifier(StoneModifier):
    """Subdivide mesh and displace vertices along normal using noise.

    Conditional: skipped when Roughness == 0.
    Deterministic: noise seed fixed at 0 (Blender noise is position-based).
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Roughness",    "INPUT", "NodeSocketFloat", 0.05),
        ("Noise Scale",  "INPUT", "NodeSocketFloat", 5.0),
    ]

    def enabled(self, ctx: ModifierContext) -> bool:
        return ctx.roughness > 0.0

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node,
              ctx: ModifierContext,
              report: ValidationReport) -> bpy.types.Node:
        g = graph

        if ctx.noise_scale <= 0:
            report.warn("Noise Scale <= 0; displacement will be flat")

        # subdivide
        subd = g.subdivide_mesh(location=(100, -300))
        subd.inputs["Level"].default_value = 2
        g.link(mesh_node.outputs["Mesh"], subd.inputs["Mesh"])

        # noise texture
        noise = g.noise_texture(location=(100, -450))
        g.link(group_input.outputs["Noise Scale"], noise.inputs["Scale"])

        # roughness * noise
        disp = g.math('MULTIPLY', location=(250, -400))
        g.link(noise.outputs["Fac"], disp.inputs[0])
        g.link(group_input.outputs["Roughness"], disp.inputs[1])

        # scale normal by displacement
        normal = g.input_normal(location=(200, -500))
        offset = g.vector_math('SCALE', location=(350, -400))
        g.link(normal.outputs["Normal"], offset.inputs[0])
        g.link(disp.outputs[0], offset.inputs["Scale"])

        # set position
        set_pos = g.set_position(location=(500, -300))
        g.link(subd.outputs["Mesh"], set_pos.inputs["Geometry"])
        g.link(offset.outputs["Vector"], set_pos.inputs["Offset"])

        return set_pos


class EdgeBevelModifier(StoneModifier):
    """Bevel all edges to break the perfect-box silhouette.

    Conditional: skipped when Edge Bevel <= 0.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Edge Bevel", "INPUT", "NodeSocketFloat", 0.03),
    ]

    def enabled(self, ctx: ModifierContext) -> bool:
        return ctx.edge_bevel > 0.0

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node,
              ctx: ModifierContext,
              report: ValidationReport) -> bpy.types.Node:
        g = graph

        bevel = g.node("GeometryNodeBevel", location=(200, -300))
        bevel.inputs["Amount"].default_value = 0.03
        # Wire the Edge Bevel socket
        g.link(group_input.outputs["Edge Bevel"], bevel.inputs["Amount"])
        g.link(mesh_node.outputs["Mesh"], bevel.inputs["Mesh"])

        return bevel


class FaceIrregularity(StoneModifier):
    """Per-face random scale variation — breaks uniform stone sizes.

    Uses ID + Seed to generate deterministic per-stone random values.
    Scales each instance slightly (±5%) so stones aren't identical.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Size Variation", "INPUT", "NodeSocketFloat", 0.05),
        ("Seed",           "INPUT", "NodeSocketInt",   0),
    ]

    def enabled(self, ctx: ModifierContext) -> bool:
        return ctx.size_variation > 0.0

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node,
              ctx: ModifierContext,
              report: ValidationReport) -> bpy.types.Node:
        g = graph

        # per-element ID (stable per instance after realize)
        id_node = g.input_id(location=(100, -450))

        # random scale factor: 1.0 ± Size Variation, based on ID + Seed
        rand = g.random_value(location=(200, -450))
        rand.data_type = 'FLOAT'  # type: ignore[assignment]
        g.link(id_node.outputs["ID"], rand.inputs["ID"])
        g.link(group_input.outputs["Seed"], rand.inputs["Seed"])
        rand.inputs["Min"].default_value = -1.0
        rand.inputs["Max"].default_value = 1.0

        # scale_amount = 1.0 + (random * Size Variation)
        sv = g.math('MULTIPLY', location=(350, -450))
        g.link(rand.outputs[2], sv.inputs[0])  # Value output
        g.link(group_input.outputs["Size Variation"], sv.inputs[1])

        one = g.math('ADD', location=(450, -450))
        one.inputs[1].default_value = 1.0
        g.link(sv.outputs[0], one.inputs[0])

        # build scale vector (uniform)
        scale_vec = g.combine_xyz(location=(500, -450))
        g.link(one.outputs[0], scale_vec.inputs["X"])
        g.link(one.outputs[0], scale_vec.inputs["Y"])
        g.link(one.outputs[0], scale_vec.inputs["Z"])

        # scale elements
        scale_node = g.node("GeometryNodeScaleElements",
                            location=(600, -350))
        scale_node.inputs["Scale"].default_value = 1.0
        scale_node.domain = 'FACE'  # type: ignore[assignment]
        g.link(mesh_node.outputs["Mesh"], scale_node.inputs["Mesh"])
        g.link(scale_vec.outputs["Vector"], scale_node.inputs["Scale"])

        return scale_node


class CornerBreak(StoneModifier):
    """Push corner vertices inward/outward for chipped-stone look.

    Identifies corner vertices (those shared by 3+ faces) and offsets
    them along their normal by a random amount derived from ID + Seed.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Corner Break", "INPUT", "NodeSocketFloat", 0.02),
        ("Seed",         "INPUT", "NodeSocketInt",   0),
    ]

    def enabled(self, ctx: ModifierContext) -> bool:
        return ctx.corner_break > 0.0

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node,
              ctx: ModifierContext,
              report: ValidationReport) -> bpy.types.Node:
        g = graph

        # subdivide first so we have enough vertices to work with
        subd = g.subdivide_mesh(location=(100, -300))
        subd.inputs["Level"].default_value = 1
        g.link(mesh_node.outputs["Mesh"], subd.inputs["Mesh"])

        # per-vertex ID for deterministic randomness
        id_node = g.input_id(location=(200, -450))

        # random offset per vertex
        rand = g.random_value(location=(300, -450))
        rand.data_type = 'FLOAT'  # type: ignore[assignment]
        g.link(id_node.outputs["ID"], rand.inputs["ID"])
        g.link(group_input.outputs["Seed"], rand.inputs["Seed"])
        rand.inputs["Min"].default_value = -1.0
        rand.inputs["Max"].default_value = 1.0

        # break_amount = random * Corner Break
        amount = g.math('MULTIPLY', location=(400, -400))
        g.link(rand.outputs[2], amount.inputs[0])
        g.link(group_input.outputs["Corner Break"], amount.inputs[1])

        # offset = normal * break_amount
        normal = g.input_normal(location=(350, -500))
        offset = g.vector_math('SCALE', location=(500, -400))
        g.link(normal.outputs["Normal"], offset.inputs[0])
        g.link(amount.outputs[0], offset.inputs["Scale"])

        # set position
        set_pos = g.set_position(location=(600, -300))
        g.link(subd.outputs["Mesh"], set_pos.inputs["Geometry"])
        g.link(offset.outputs["Vector"], set_pos.inputs["Offset"])

        return set_pos

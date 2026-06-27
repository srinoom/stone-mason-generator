"""Stone Modifier Stack — surface irregularity pipeline.

Refactored in Step 13:
  - Common interface: enabled(ctx) + apply(...)
  - Conditional generation: if enabled() returns False, the modifier's
    nodes are not created — no wasted Geometry Nodes.
  - Validation: apply() receives a ValidationReport to collect warnings.

Modifiers:
  - NoiseModifier: subdivide + displace vertices along normal via noise

Future modifiers:
  - EdgeDamage, CornerBreak, SurfaceChipping, Bevel
"""

import bpy
from typing import List, Tuple, Optional

from .graph import NodeGraph


class ModifierContext:
    """Read-only context passed to StoneModifier.enabled() and apply().

    Carries the current property values so modifiers can decide whether
    they should generate nodes without reading the Scene directly.
    """

    def __init__(self, props):
        self.props = props
        # Convenience accessors
        self.roughness = getattr(props, 'roughness', 0.0)
        self.noise_scale = getattr(props, 'noise_scale', 5.0)
        self.stone_width = getattr(props, 'stone_width', 0.5)
        self.stone_height = getattr(props, 'stone_height', 0.25)
        self.stone_depth = getattr(props, 'stone_depth', 0.3)
        self.joint_width = getattr(props, 'joint_width', 0.02)
        self.course_height = getattr(props, 'course_height', 0.5)
        self.bond_offset = getattr(props, 'bond_offset', 0.25)


class ValidationReport:
    """Collects validation warnings from engines and modifiers."""

    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            lines.extend(f"  - {e}" for e in self.errors)
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            lines.extend(f"  - {w}" for w in self.warnings)
        return "\n".join(lines) if lines else "OK"


class StoneModifier:
    """Abstract base for stone surface modifiers.

    Subclasses override:
      - :meth:`enabled` — return False to skip node generation entirely
      - :meth:`apply`    — transform the mesh, return result node
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def enabled(self, ctx: ModifierContext) -> bool:
        """Return True if this modifier should generate nodes.

        Default: always enabled. Override for conditional generation.
        """
        return True

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node,
              ctx: ModifierContext,
              report: ValidationReport) -> bpy.types.Node:
        """Transform the input mesh and return the result node.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).
            mesh_node: Previous node in the stack (output is a Mesh).
            ctx: ModifierContext with current property values.
            report: ValidationReport to log warnings.

        Returns:
            A node whose geometry output is the modified mesh.
        """
        raise NotImplementedError


class NoiseModifier(StoneModifier):
    """Subdivide mesh and displace vertices along normal using noise.

    Conditional generation: if Roughness <= 0, no nodes are created.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Roughness",    "INPUT", "NodeSocketFloat", 0.05),
        ("Noise Scale",  "INPUT", "NodeSocketFloat", 5.0),
    ]

    def enabled(self, ctx: ModifierContext) -> bool:
        """Skip node generation when Roughness is zero."""
        return ctx.roughness > 0.0

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node,
              ctx: ModifierContext,
              report: ValidationReport) -> bpy.types.Node:
        g = graph

        # --- validate ---
        if ctx.noise_scale <= 0:
            report.warn("Noise Scale is <= 0; noise will be flat. "
                        "Consider using a positive value.")

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

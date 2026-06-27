"""Instance Engine — instances stone prototypes on points and realizes.

Refactored in Step 13:
  - Modifier stack uses enabled(ctx) for conditional generation
  - If a modifier returns False from enabled(), its nodes are skipped
  - ValidationReport collected from modifiers, surfaced to operator

Pipeline stage (runs AFTER BondEngine):

    Points (shifted by bond offset)
      → StonePrimitive.build() → base mesh
      → for mod in modifiers:
          if mod.enabled(ctx): mod.apply() → modified mesh
      → Instance on Points
      → [Realize Instances]  (optional, configurable)
      → Output Geometry
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .primitive import StonePrimitive, CubePrimitive
from .modifier import StoneModifier, ModifierContext, ValidationReport


class InstanceEngine:
    """Instances a StonePrimitive (with conditional modifier stack) on points.

    Attributes:
        primitive: The base mesh prototype.
        modifiers: Ordered list of StoneModifier instances.
        realize:   If True, realize instances into real geometry.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = []

    def __init__(self, primitive: StonePrimitive = None,
                 modifiers: List[StoneModifier] = None,
                 realize: bool = True):
        self.primitive = primitive or CubePrimitive()
        self.modifiers = modifiers or []
        self.realize = realize

    @property
    def primitive_sockets(self) -> List[Tuple[str, str, str, object]]:
        """Sockets from the primitive + all modifiers (unconditional).

        Sockets are always declared so the interface is stable
        regardless of which modifiers are enabled at build time.
        """
        sockets = list(self.primitive.SOCKETS)
        for mod in self.modifiers:
            sockets.extend(mod.SOCKETS)
        return sockets

    def active_modifier_sockets(self, ctx: ModifierContext) -> List[Tuple]:
        """Sockets only from enabled modifiers — for future optimization."""
        sockets = list(self.primitive.SOCKETS)
        for mod in self.modifiers:
            if mod.enabled(ctx):
                sockets.extend(mod.SOCKETS)
        return sockets

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node,
              ctx: ModifierContext = None,
              report: ValidationReport = None) -> bpy.types.Node:
        """Build the instancing sub-tree.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).
            prev_geometry: Previous geometry node (shifted points from BondEngine).
            ctx: ModifierContext (if None, all modifiers run unconditionally).
            report: ValidationReport (if None, warnings are silently skipped).

        Returns:
            Instance-on-Points node (if realize=False) or
            Realize Instances node (if realize=True).
        """
        g = graph

        # --- base mesh from primitive ---
        mesh = self.primitive.build(g, group_input)

        # --- apply modifier stack (conditional) ---
        for mod in self.modifiers:
            if ctx is not None and not mod.enabled(ctx):
                continue
            if ctx is not None and report is not None:
                mesh = mod.apply(g, group_input, mesh, ctx, report)
            else:
                # Backward compatible path: no ctx/report
                mesh = mod.apply(g, group_input, mesh, ctx, report)

        # --- instance stones on points ---
        inst = g.instance_on_points(location=(0, 0))
        g.link(prev_geometry.outputs["Geometry"],
               inst.inputs["Points"])
        g.link(mesh.outputs["Mesh"],
               inst.inputs["Instance"])

        # --- optional realize ---
        if self.realize:
            realize = g.realize_instances(location=(300, 0))
            g.link(inst.outputs["Instances"],
                   realize.inputs["Geometry"])
            return realize

        return inst  # output socket is "Instances" — still Geometry type



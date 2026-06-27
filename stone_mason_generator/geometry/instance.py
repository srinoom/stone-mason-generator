"""Instance Engine — instances stone prototypes on points and realizes.

Refactored in Step 12:
  - Delegates mesh creation to StonePrimitive
  - Applies StoneModifier stack before instancing
  - Configurable output: instances or realized geometry

Pipeline stage (runs AFTER BondEngine):

    Points (shifted by bond offset)
      → StonePrimitive.build() → base mesh
      → StoneModifier[0].apply() → modified mesh
      → ...
      → Instance on Points
      → [Realize Instances]  (optional, configurable)
      → Output Geometry
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .primitive import StonePrimitive, CubePrimitive
from .modifier import StoneModifier, NoiseModifier


class InstanceEngine:
    """Instances a StonePrimitive (with modifier stack) on points.

    Attributes:
        primitive: The base mesh prototype.
        modifiers: Ordered list of StoneModifier instances.
        realize:   If True, realize instances into real geometry.
                   If False, leave as instances (lighter in viewport).
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
        """Sockets from the primitive + all modifiers."""
        sockets = list(self.primitive.SOCKETS)
        for mod in self.modifiers:
            sockets.extend(mod.SOCKETS)
        return sockets

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the instancing sub-tree.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).
            prev_geometry: Previous geometry node (shifted points from BondEngine).

        Returns:
            Instance-on-Points node (if realize=False) or
            Realize Instances node (if realize=True).
        """
        g = graph

        # --- base mesh from primitive ---
        mesh = self.primitive.build(g, group_input)

        # --- apply modifier stack ---
        for mod in self.modifiers:
            mesh = mod.apply(g, group_input, mesh)

        # --- instance stones on points ---
        inst = g.instance_on_points(location=(0, 0))
        g.link(prev_geometry.outputs[0],
               inst.inputs["Points"])
        g.link(mesh.outputs["Mesh"],
               inst.inputs["Instance"])

        # --- optional realize ---
        if self.realize:
            realize = g.realize_instances(location=(300, 0))
            g.link(inst.outputs["Instances"],
                   realize.inputs["Geometry"])
            return realize

        return inst

"""Node-group and modifier lifecycle management.

Single entry point for operators: :meth:`NodeGroupManager.apply`.
Handles node-group creation/reuse, interface setup, and modifier wiring.
"""

import bpy

from .graph import NodeGraph
from .scatter import ScatterEngine


class NodeGroupManager:
    """Create or reuse the scatter-engine node group and apply it as a modifier."""

    GROUP_NAME = ScatterEngine.GROUP_NAME

    @classmethod
    def get_or_create_group(cls) -> bpy.types.NodeTree:
        """Return the SMG node group, creating it if necessary."""
        group = bpy.data.node_groups.get(cls.GROUP_NAME)

        if group is None:
            group = bpy.data.node_groups.new(
                cls.GROUP_NAME,
                "GeometryNodeTree",
            )

        engine = ScatterEngine(group)
        engine.build()
        return group

    @classmethod
    def apply(cls, obj: bpy.types.Object, props) -> bpy.types.Modifier:
        """Add (or refresh) the scatter modifier on *obj*.

        ``props`` is a :class:`StoneProperties` instance; its fields are
        pushed into the modifier socket defaults.
        """
        group = cls.get_or_create_group()

        modifier = obj.modifiers.get(cls.GROUP_NAME)
        if modifier is None:
            modifier = obj.modifiers.new(cls.GROUP_NAME, "NODES")
        modifier.node_group = group

        # Push property values → modifier socket defaults
        cls._sync_props(modifier, props)

        return modifier

    # -- private -----------------------------------------------------------

    @staticmethod
    def _sync_props(modifier: bpy.types.Modifier, props) -> None:
        """Copy StoneProperties fields into the modifier's input sockets."""
        mapping = {
            "Density":      props.density,
            "Seed":         props.seed,
            "Stone Width":  props.stone_width,
            "Stone Height": props.stone_height,
        }
        # Modifier socket identifiers follow the interface socket names
        # for simple names (no spaces replaced in 4.x/5.x).
        for name, value in mapping.items():
            try:
                modifier[f"{name.replace(' ', '_')}_"] = value
            except KeyError:
                # identifier fallback -- try direct name
                try:
                    modifier[name] = value
                except KeyError:
                    pass


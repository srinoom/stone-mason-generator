"""Node-group and modifier lifecycle management.

Builder only manages node groups and modifiers.
It delegates node-tree construction to the Composer.
"""

import bpy

from .nodes import default_composer


class NodeGroupManager:
    """Create or reuse the SMG node group and apply it as a modifier."""

    GROUP_NAME = "SMG_StoneGenerator"

    @classmethod
    def get_or_create_group(cls) -> bpy.types.NodeTree:
        """Return the SMG node group, creating and building it if necessary."""
        group = bpy.data.node_groups.get(cls.GROUP_NAME)

        if group is None:
            group = bpy.data.node_groups.new(
                cls.GROUP_NAME,
                "GeometryNodeTree",
            )

        composer = default_composer()
        composer.build_group(group)
        return group

    @classmethod
    def apply(cls, obj: bpy.types.Object, props) -> bpy.types.Modifier:
        """Add (or refresh) the scatter modifier on *obj*.

        ``props`` is a :class:`StoneProperties instance; its fields are
        pushed into the modifier socket inputs.
        """
        group = cls.get_or_create_group()

        modifier = obj.modifiers.get(cls.GROUP_NAME)
        if modifier is None:
            modifier = obj.modifiers.new(cls.GROUP_NAME, "NODES")
        modifier.node_group = group

        cls._sync_props(modifier, props)

        return modifier

    # -- private -----------------------------------------------------------

    @staticmethod
    def _sync_props(modifier: bpy.types.Modifier, props) -> None:
        """Copy StoneProperties fields into the modifier's input sockets.

        Modifier socket identifiers use the interface socket name with
        spaces replaced by underscores and a trailing underscore
        (Blender 4.x/5.x convention).
        """
        mapping = {
            "Density":       props.density,
            "Seed":          props.seed,
            "Stone_Width":   props.stone_width,
            "Stone_Height":  props.stone_height,
            "Course_Height": props.course_height,
        }
        for identifier, value in mapping.items():
            try:
                modifier[identifier + "_"] = value
            except KeyError:
                pass


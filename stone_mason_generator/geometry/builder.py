"""Node-group and modifier lifecycle management.

Builder only manages node groups and modifiers.
It delegates node-tree construction to the Composer.

Step 13: parameter validation + conditional modifier generation.
"""

import bpy

from .nodes import default_composer
from .modifier import ModifierContext, ValidationReport


class NodeGroupManager:
    """Create or reuse the SMG node group and apply it as a modifier."""

    GROUP_NAME = "SMG_StoneGenerator"

    @classmethod
    def get_or_create_group(cls, ctx: ModifierContext = None,
                            report: ValidationReport = None) -> bpy.types.NodeTree:
        group = bpy.data.node_groups.get(cls.GROUP_NAME)

        if group is None:
            group = bpy.data.node_groups.new(
                cls.GROUP_NAME,
                "GeometryNodeTree",
            )

        composer = default_composer()
        composer.build_group(group, ctx, report)
        return group

    @classmethod
    def apply(cls, obj: bpy.types.Object, props) -> bpy.types.Modifier:
        """Add (or refresh) the scatter modifier on *obj*.

        Validates parameters, creates ModifierContext, builds the node
        group with conditional modifiers, and syncs properties.
        """
        # --- validate ---
        report = ValidationReport()
        cls._validate(props, report)

        if not report.ok:
            # Errors are fatal — do not build a broken node tree
            return None

        # --- build context ---
        ctx = ModifierContext(props)

        # --- build node group ---
        group = cls.get_or_create_group(ctx, report)

        modifier = obj.modifiers.get(cls.GROUP_NAME)
        if modifier is None:
            modifier = obj.modifiers.new(cls.GROUP_NAME, "NODES")
        modifier.node_group = group

        cls._sync_props(modifier, props)

        return modifier

    # -- private -----------------------------------------------------------

    @staticmethod
    def _validate(props, report: ValidationReport) -> None:
        """Validate parameter combinations before building the node tree."""

        if props.stone_width <= 0:
            report.error("Stone Width must be > 0")
        if props.stone_height <= 0:
            report.error("Stone Height must be > 0")
        if props.stone_depth <= 0:
            report.error("Stone Depth must be > 0")
        if props.joint_width < 0:
            report.error("Joint Width must be >= 0")
        if props.course_height <= 0:
            report.error("Course Height must be > 0")
        if props.bond_offset < 0:
            report.error("Bond Offset must be >= 0")
        if props.roughness < 0:
            report.error("Roughness must be >= 0")
        if props.noise_scale <= 0:
            report.warn("Noise Scale <= 0 may produce flat displacement")

        # logical combinations
        if props.joint_width >= props.stone_width:
            report.warn("Joint Width >= Stone Width: very few or zero "
                        "stones per course")

    @staticmethod
    def _sync_props(modifier: bpy.types.Modifier, props) -> None:
        """Copy StoneProperties fields into modifier socket inputs."""
        mapping = {
            "Stone_Width":   props.stone_width,
            "Stone_Height":  props.stone_height,
            "Stone_Depth":   props.stone_depth,
            "Roughness":     props.roughness,
            "Noise_Scale":   props.noise_scale,
            "Joint_Width":   props.joint_width,
            "Course_Height": props.course_height,
            "Bond_Offset":   props.bond_offset,
            "Seed":          props.seed,
            "Density":       props.density,
        }
        for identifier, value in mapping.items():
            try:
                modifier[identifier + "_"] = value
            except KeyError:
                pass

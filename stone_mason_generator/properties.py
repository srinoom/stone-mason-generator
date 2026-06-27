"""Stone Mason Generator -- scene-level properties."""

import bpy


class StoneProperties(bpy.types.PropertyGroup):

    seed: bpy.props.IntProperty(
        name="Seed",
        default=1,
        min=0,
        max=999999,
    )

    density: bpy.props.FloatProperty(
        name="Density",
        description="Point density (random scatter only)",
        default=50.0,
        min=0.0,
        max=500.0,
    )

    # --- layout ---
    stone_width: bpy.props.FloatProperty(
        name="Stone Width",
        default=0.50,
        min=0.01,
        max=5.0,
    )

    joint_width: bpy.props.FloatProperty(
        name="Joint Width",
        description="Gap between adjacent stones in a course",
        default=0.02,
        min=0.0,
        max=1.0,
    )

    course_height: bpy.props.FloatProperty(
        name="Course Height",
        description="Height of each masonry course (row)",
        default=0.50,
        min=0.05,
        max=5.0,
    )

    bond_offset: bpy.props.FloatProperty(
        name="Bond Offset",
        description="Horizontal stagger for odd courses",
        default=0.25,
        min=0.0,
        max=2.5,
    )

    # --- primitive ---
    stone_height: bpy.props.FloatProperty(
        name="Stone Height",
        default=0.25,
        min=0.01,
        max=5.0,
    )

    stone_depth: bpy.props.FloatProperty(
        name="Stone Depth",
        description="How deep the stone extends into the wall",
        default=0.30,
        min=0.01,
        max=5.0,
    )

    # --- modifiers ---
    roughness: bpy.props.FloatProperty(
        name="Roughness",
        description="Surface noise displacement (0 = smooth)",
        default=0.05,
        min=0.0,
        max=0.5,
    )

    noise_scale: bpy.props.FloatProperty(
        name="Noise Scale",
        description="Frequency of surface displacement noise",
        default=5.0,
        min=0.1,
        max=50.0,
    )

    edge_bevel: bpy.props.FloatProperty(
        name="Edge Bevel",
        description="Bevel all edges for worn look (0 = sharp)",
        default=0.03,
        min=0.0,
        max=0.2,
    )

    size_variation: bpy.props.FloatProperty(
        name="Size Variation",
        description="Per-stone random size ± (0 = uniform)",
        default=0.05,
        min=0.0,
        max=0.3,
    )

    corner_break: bpy.props.FloatProperty(
        name="Corner Break",
        description="Random corner displacement for chipped look (0 = sharp)",
        default=0.02,
        min=0.0,
        max=0.2,
    )


classes = (
    StoneProperties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.stone_generator = bpy.props.PointerProperty(
        type=StoneProperties
    )


def unregister():
    del bpy.types.Scene.stone_generator

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

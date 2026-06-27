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

    roughness: bpy.props.FloatProperty(
        name="Roughness",
        description="Vertex displacement amount for rough stones (0 = smooth)",
        default=0.05,
        min=0.0,
        max=0.5,
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

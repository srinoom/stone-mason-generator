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
        description="Point density on the surface",
        default=40.0,
        min=0.0,
        max=500.0,
    )

    stone_width: bpy.props.FloatProperty(
        name="Stone Width",
        default=0.50,
        min=0.01,
        max=5.0,
    )

    stone_height: bpy.props.FloatProperty(
        name="Stone Height",
        default=0.25,
        min=0.01,
        max=5.0,
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


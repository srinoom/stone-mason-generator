import bpy


class StoneProperties(bpy.types.PropertyGroup):

    seed: bpy.props.IntProperty(
        name="Seed",
        default=1,
        min=0,
        max=999999,
    )

    stone_count: bpy.props.IntProperty(
        name="Stone Count",
        default=40,
        min=2,
        max=500,
    )

    width_scale: bpy.props.FloatProperty(
        name="Width",
        default=1.0,
        min=0.1,
        max=5.0,
    )

    height_scale: bpy.props.FloatProperty(
        name="Height",
        default=1.0,
        min=0.1,
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
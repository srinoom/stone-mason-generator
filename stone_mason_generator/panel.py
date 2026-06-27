"""Stone Mason Generator -- UI panel."""

import bpy


class VIEW3D_PT_stone_generator(bpy.types.Panel):

    bl_space_type = "VIEW3D"
    bl_region_type = "UI"
    bl_category = "Stone"
    bl_label = "Stone Mason Generator"

    def draw(self, context):
        layout = self.layout
        props = context.scene.stone_generator

        box = layout.box()
        box.label(text="Courses", icon='LINENUMBERS_ON')
        box.prop(props, "course_height")

        box = layout.box()
        box.label(text="Bond Pattern", icon='MOD_ARRAY')
        box.prop(props, "bond_offset")

        box = layout.box()
        box.label(text="Scatter", icon='OUTLINER_OB_GROUP_INSTANCE')
        box.prop(props, "seed")
        box.prop(props, "density")
        box.prop(props, "stone_width")
        box.prop(props, "stone_height")

        layout.separator()
        layout.operator("stone.generate", icon="MOD_REMESH")


classes = (
    VIEW3D_PT_stone_generator,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

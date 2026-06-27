"""Stone Mason Generator -- operators."""

import bpy

from .geometry.builder import NodeGroupManager


class STONE_OT_generate(bpy.types.Operator):
    """Apply the Stone Mason scatter engine to the active mesh."""

    bl_idname = "stone.generate"
    bl_label = "Generate Stone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh")
            return {'CANCELLED'}

        props = context.scene.stone_generator
        NodeGroupManager.apply(obj, props)

        self.report({'INFO'}, "Stone Generator applied")
        return {'FINISHED'}


classes = (
    STONE_OT_generate,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


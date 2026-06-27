import bpy
from .geometry.builder import add_modifier


class STONE_OT_generate(bpy.types.Operator):

    bl_idname = "stone.generate"
    bl_label = "Generate TEST"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        obj = context.active_object

        if obj is None:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh")
            return {'CANCELLED'}

        add_modifier(obj)

        self.report(
            {'INFO'},
            "Stone Generator Added"
        )

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
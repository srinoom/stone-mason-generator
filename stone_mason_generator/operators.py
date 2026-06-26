import bpy


class STONE_OT_generate(bpy.types.Operator):

    bl_idname = "stone.generate"

    bl_label = "Generate"

    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        props = context.scene.stone_generator

        self.report(
            {'INFO'},
            f"Seed {props.seed} | Stones {props.stone_count}"
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
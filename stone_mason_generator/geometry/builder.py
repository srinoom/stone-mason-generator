import bpy

from .nodes import build_basic_nodes

NODE_GROUP_NAME = "SMG_StoneGenerator"


def get_or_create_node_group():

    group = bpy.data.node_groups.get(NODE_GROUP_NAME)

    if group is None:

        print("[SMG] Create Node Group")

        group = bpy.data.node_groups.new(
            NODE_GROUP_NAME,
            "GeometryNodeTree"
        )

        group.interface.new_socket(
            name="Geometry",
            in_out='INPUT',
            socket_type="NodeSocketGeometry"
        )

        group.interface.new_socket(
            name="Geometry",
            in_out='OUTPUT',
            socket_type="NodeSocketGeometry"
        )

    print("[SMG] Build Node Tree")

    build_basic_nodes(group)

    return group


def add_modifier(obj):

    modifier = obj.modifiers.get(NODE_GROUP_NAME)

    if modifier is None:

        print("[SMG] Create Modifier")

        modifier = obj.modifiers.new(
            NODE_GROUP_NAME,
            "NODES"
        )

    modifier.node_group = get_or_create_node_group()

    print("[SMG] Modifier Assigned")

    return modifier
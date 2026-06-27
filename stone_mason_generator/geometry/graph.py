"""Low-level Geometry Node tree builder API.

Thin wrapper around Blender's bpy node-group API.
No business logic -- higher-level engines compose these primitives.
"""

import bpy
from typing import Optional


class NodeGraph:
    """Wrapper around a Geometry Node group for clean node/link creation."""

    def __init__(self, group: bpy.types.NodeTree):
        self.group = group
        self.nodes = group.nodes
        self.links = group.links

    # -- core operations ---------------------------------------------------

    def clear(self) -> None:
        self.nodes.clear()

    def new(self, node_type: str, location: tuple = (0, 0),
            label: Optional[str] = None) -> bpy.types.Node:
        node = self.nodes.new(node_type)
        node.location = location
        if label:
            node.label = label
        return node

    def link(self, out_socket: bpy.types.NodeSocket,
             in_socket: bpy.types.NodeSocket) -> None:
        self.links.new(out_socket, in_socket)

    # -- convenience factories --------------------------------------------

    def group_input(self, location: tuple = (-800, 0)) -> bpy.types.Node:
        return self.new("NodeGroupInput", location)

    def group_output(self, location: tuple = (800, 0)) -> bpy.types.Node:
        return self.new("NodeGroupOutput", location)

    def realize_instances(self, location: tuple = (300, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeRealizeInstances", location)

    def cube(self, location: tuple = (0, -300)) -> bpy.types.Node:
        return self.new("GeometryNodeMeshCube", location)

    def instance_on_points(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeInstanceOnPoints", location)

    def combine_xyz(self, location: tuple = (-200, -300)) -> bpy.types.Node:
        return self.new("ShaderNodeCombineXYZ", location)

    def separate_xyz(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("ShaderNodeSeparateXYZ", location)

    def position(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeInputPosition", location)

    def input_normal(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeInputNormal", location)

    def input_id(self, location: tuple = (0, 0)) -> bpy.types.Node:
        """Read the stable per-element ID (integer)."""
        return self.new("GeometryNodeInputID", location)

    def math(self, operation: str = 'ADD',
             location: tuple = (0, 0)) -> bpy.types.Node:
        n = self.new("ShaderNodeMath", location)
        n.operation = operation
        return n

    def vector_math(self, operation: str = 'ADD',
                    location: tuple = (0, 0)) -> bpy.types.Node:
        n = self.new("ShaderNodeVectorMath", location)
        n.operation = operation
        return n

    def store_named_attribute(self,
                              location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeStoreNamedAttribute", location)

    def named_attribute(self,
                        location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeInputNamedAttribute", location)

    def attribute_statistic(self,
                            location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeAttributeStatistic", location)

    def bounding_box(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeBoundBox", location)

    def set_position(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeSetPosition", location)

    def mesh_grid(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeMeshGrid", location)

    def mesh_to_points(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeMeshToPoints", location)

    def transform_geometry(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeTransform", location)

    def float_to_int(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("FunctionNodeFloatToInt", location)

    def noise_texture(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("ShaderNodeTexNoise", location)

    def random_value(self, location: tuple = (0, 0)) -> bpy.types.Node:
        """Random Value node — set data_type property after creation."""
        return self.new("FunctionNodeRandomValue", location)

    def subdivide_mesh(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeSubdivideMesh", location)

    # -- generic node with params -----------------------------------------

    def node(self, node_type: str, location: tuple = (0, 0),
             label: Optional[str] = None,
             params: Optional[dict] = None) -> bpy.types.Node:
        n = self.new(node_type, location, label=label)
        if params:
            for key, val in params.items():
                n.inputs[key].default_value = val
        return n

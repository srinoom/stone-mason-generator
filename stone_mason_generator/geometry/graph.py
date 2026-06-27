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
        """Read surface normal from current geometry context."""
        return self.new("GeometryNodeInputNormal", location)

    def math(self, operation: str = 'ADD',
             location: tuple = (0, 0)) -> bpy.types.Node:
        """Create a Math node (scalar) with the given operation."""
        n = self.new("ShaderNodeMath", location)
        n.operation = operation
        return n

    def vector_math(self, operation: str = 'ADD',
                    location: tuple = (0, 0)) -> bpy.types.Node:
        """Create a Vector Math node with the given operation."""
        n = self.new("ShaderNodeVectorMath", location)
        n.operation = operation
        return n

    def store_named_attribute(self,
                              location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeStoreNamedAttribute", location)

    def named_attribute(self,
                        location: tuple = (0, 0)) -> bpy.types.Node:
        """Read a named attribute from the current geometry context."""
        return self.new("GeometryNodeInputNamedAttribute", location)

    def attribute_statistic(self,
                            location: tuple = (0, 0)) -> bpy.types.Node:
        """Compute statistics (min, max, mean, etc.) of a named attribute."""
        return self.new("GeometryNodeAttributeStatistic", location)

    def bounding_box(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeBoundBox", location)

    def set_position(self, location: tuple = (0, 0)) -> bpy.types.Node:
        """Modify position of geometry elements via offset or absolute."""
        return self.new("GeometryNodeSetPosition", location)

    def mesh_grid(self, location: tuple = (0, 0)) -> bpy.types.Node:
        """Create a Mesh Grid primitive (XY plane, centered at origin)."""
        return self.new("GeometryNodeMeshGrid", location)

    def mesh_to_points(self, location: tuple = (0, 0)) -> bpy.types.Node:
        """Convert mesh vertices/edges/faces to point cloud."""
        return self.new("GeometryNodeMeshToPoints", location)

    def transform_geometry(self, location: tuple = (0, 0)) -> bpy.types.Node:
        """Transform geometry (translation, rotation, scale)."""
        return self.new("GeometryNodeTransform", location)

    def float_to_int(self, location: tuple = (0, 0)) -> bpy.types.Node:
        """Convert float to integer with configurable rounding."""
        return self.new("FunctionNodeFloatToInt", location)

    # -- generic node with params -----------------------------------------

    def node(self, node_type: str, location: tuple = (0, 0),
             label: Optional[str] = None,
             params: Optional[dict] = None) -> bpy.types.Node:
        """Create a node and set input default values from *params*."""
        n = self.new(node_type, location, label=label)
        if params:
            for key, val in params.items():
                n.inputs[key].default_value = val
        return n


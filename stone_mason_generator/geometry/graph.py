"""Low-level Geometry Node tree builder API.

This module provides a thin wrapper around Blender's bpy node-group API,
giving every node-creation call a clean, consistent signature.
No business logic lives here -- higher-level engines (scatter.py, etc.)
compose these primitives into useful node trees.
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
        """Remove every node in the group."""
        self.nodes.clear()

    def new(self, node_type: str, location: tuple = (0, 0),
            label: Optional[str] = None) -> bpy.types.Node:
        """Create a node of *node_type* at *location*."""
        node = self.nodes.new(node_type)
        node.location = location
        if label:
            node.label = label
        return node

    def link(self, out_socket: bpy.types.NodeSocket,
             in_socket: bpy.types.NodeSocket) -> None:
        """Connect *out_socket* to *in_socket*."""
        self.links.new(out_socket, in_socket)

    def link_chain(self, *pairs) -> None:
        """Link multiple (out_socket, in_socket) pairs in one call."""
        for out_sock, in_sock in pairs:
            self.link(out_sock, in_sock)

    # -- convenience factories --------------------------------------------

    def group_input(self, location: tuple = (-800, 0)) -> bpy.types.Node:
        return self.new("NodeGroupInput", location)

    def group_output(self, location: tuple = (800, 0)) -> bpy.types.Node:
        return self.new("NodeGroupOutput", location)

    def transform(self, location: tuple = (-400, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeTransform", location)

    def mesh_to_points(self, location: tuple = (0, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeMeshToPoints", location)

    def instance_on_points(self, location: tuple = (300, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeInstanceOnPoints", location)

    def realize_instances(self, location: tuple = (600, 0)) -> bpy.types.Node:
        return self.new("GeometryNodeRealizeInstances", location)

    def cube(self, location: tuple = (300, -300)) -> bpy.types.Node:
        return self.new("GeometryNodeMeshCube", location)

    # -- generic node with params -----------------------------------------

    def node(self, node_type: str, location: tuple = (0, 0),
             label: Optional[str] = None,
             params: Optional[dict] = None) -> bpy.types.Node:
        """Create a node and set input default values from *params* dict.

        ``params`` maps socket names (str) or indices (int) to values.
        """
        n = self.new(node_type, location, label=label)
        if params:
            for key, val in params.items():
                n.inputs[key].default_value = val
        return n


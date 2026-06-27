import bpy
print("GRAPH FILE =", __file__)

class NodeGraph:

    def __init__(self, group):

        self.group = group
        self.nodes = group.nodes
        self.links = group.links

    # ---------------------------------

    def clear(self):

        self.nodes.clear()

    # ---------------------------------

    def new(self, node_type, location=(0, 0)):

        print(f"[SMG] Create {node_type}")
        node = self.nodes.new(node_type)
        node.location = location
        return node

    # ---------------------------------

    def link(self, output_socket, input_socket):
        
        print(
        f"[SMG] Link : {output_socket.name} -> {input_socket.name}"
    )

        self.links.new(output_socket, input_socket)

    # ---------------------------------

    def input(self):

        return self.new(
            "NodeGroupInput",
            (-500, 0)
        )

    # ---------------------------------

    def output(self):

        return self.new(
            "NodeGroupOutput",
            (500, 0)
        )

    # ---------------------------------

    def transform(self):

        return self.new(
            "GeometryNodeTransform",
            (0, 0)
        )
    
    # ---------------------------------

    def mesh_to_points(self):

        return self.new(
            "GeometryNodeMeshToPoints",
            (250, 0),
        )

    # ---------------------------------

    def instance_on_points(self):

        return self.new(
            "GeometryNodeInstanceOnPoints",
            (550, 0),
        )

    # ---------------------------------

    def realize_instances(self):

        return self.new(
            "GeometryNodeRealizeInstances",
            (850, 0),
        )

    # ---------------------------------

    def cube(self):

        return self.new(
            "GeometryNodeMeshCube",
            (250, -250),
        )
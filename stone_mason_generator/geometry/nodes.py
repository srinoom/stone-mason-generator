import math


def build_basic_nodes(group):
    """
    Rebuild the entire node tree.
    """

    nodes = group.nodes
    links = group.links

    # Clear existing nodes
    nodes.clear()

    # Create nodes
    group_input = nodes.new("NodeGroupInput")
    transform = nodes.new("GeometryNodeTransform")
    group_output = nodes.new("NodeGroupOutput")

    group_input.location = (-400, 0)
    transform.location = (0, 0)
    group_output.location = (350, 0)

    # Rotate 10 degrees on Z
    transform.inputs["Rotation"].default_value = (
        0.0,
        0.0,
        math.radians(10)
    )

    # Link nodes
    links.new(
        group_input.outputs["Geometry"],
        transform.inputs["Geometry"]
    )

    links.new(
        transform.outputs["Geometry"],
        group_output.inputs["Geometry"]
    )

    print("[SMG] Node tree rebuilt.")
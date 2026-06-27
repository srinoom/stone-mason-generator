def build_basic_nodes(group):
    import math
    print("NODES FILE =", __file__)

    print("STEP 1")

    graph = NodeGraph(group)

    print("STEP 2")

    graph.clear()

    print("STEP 3")

    group_input = graph.input()

    transform = graph.transform()

    mesh_to_points = graph.mesh_to_points()

    cube = graph.cube()

    instance = graph.instance_on_points()

    realize = graph.realize_instances()

    group_output = graph.output()

    print("STEP 4")

    transform.inputs["Rotation"].default_value = (
        0,
        0,
        math.radians(10)
    )

    print("STEP 5")

    graph.link(
        group_input.outputs["Geometry"],
        transform.inputs["Geometry"],
    )

    graph.link(
        transform.outputs["Geometry"],
        mesh_to_points.inputs["Mesh"],
    )

    graph.link(
        mesh_to_points.outputs["Points"],
        instance.inputs["Points"],
    )

    graph.link(
        cube.outputs["Mesh"],
        instance.inputs["Instance"],
    )

    graph.link(
        instance.outputs["Instances"],
        realize.inputs["Geometry"],
    )

    graph.link(
        realize.outputs["Geometry"],
        group_output.inputs["Geometry"],
    )

    print("STEP 6")
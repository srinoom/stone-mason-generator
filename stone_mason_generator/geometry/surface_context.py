"""Surface Context — abstraction for wall-local UVN coordinates and bounds.

SurfaceContext wraps the node-tree sub-graph that ParameterizeEngine
produces. It exposes:

  Scalar attributes (stored as Named Attributes — must cross stages):
    - u_coord, v_coord   (FLOAT, POINT)
    - course_index       (FLOAT, POINT)
    - course_base_v      (FLOAT, POINT)

  Surface bounds (internal — exposed as node references, not stored):
    - u_min, u_max       (Attribute Statistic → min/max of u_coord)
    - v_min, v_max       (Attribute Statistic → min/max of v_coord)
    - width              (u_max - u_min)
    - height             (v_max - v_min)

  Normal (stored as Named Attribute — needed for stone orientation):
    - n_coord            (FLOAT_VECTOR, POINT)

Bounds are computed once by ParameterizeEngine and passed to
CourseLayout as a SurfaceContext object.
"""

import bpy
from typing import Optional

from .graph import NodeGraph


class SurfaceContext:
    """Holds node references for surface coordinates and bounds."""

    def __init__(self):
        self.geometry_out: Optional[bpy.types.Node] = None

        # Bound nodes (Attribute Statistic nodes)
        self.u_min: Optional[bpy.types.Node] = None
        self.u_max: Optional[bpy.types.Node] = None
        self.v_min: Optional[bpy.types.Node] = None
        self.v_max: Optional[bpy.types.Node] = None

        # Derived dimensions (Math node outputs)
        self.width: Optional[bpy.types.Node] = None
        self.height: Optional[bpy.types.Node] = None

    @classmethod
    def from_graph(cls, graph: NodeGraph,
                   group_input: bpy.types.Node,
                   geometry: bpy.types.Node,
                   u_sep: bpy.types.Node,
                   v_sep: bpy.types.Node,
                   n_node: bpy.types.Node) -> "SurfaceContext":
        ctx = cls()
        g = graph

        # --- store u_coord ---
        store_u = g.store_named_attribute(location=(-200, 150))
        store_u.data_type = 'FLOAT'
        store_u.domain = 'POINT'
        store_u.inputs["Name"].default_value = "u_coord"
        g.link(geometry.outputs[0], store_u.inputs["Geometry"])
        g.link(u_sep.outputs["X"], store_u.inputs["Value"])

        # --- store v_coord ---
        store_v = g.store_named_attribute(location=(-100, 50))
        store_v.data_type = 'FLOAT'
        store_v.domain = 'POINT'
        store_v.inputs["Name"].default_value = "v_coord"
        g.link(store_u.outputs[0], store_v.inputs["Geometry"])
        g.link(v_sep.outputs["Z"], store_v.inputs["Value"])

        # --- store n_coord ---
        store_n = g.store_named_attribute(location=(0, -50))
        store_n.data_type = 'FLOAT_VECTOR'
        store_n.domain = 'POINT'
        store_n.inputs["Name"].default_value = "n_coord"
        g.link(store_v.outputs[0], store_n.inputs["Geometry"])
        g.link(n_node.outputs["Normal"], store_n.inputs["Value"])

        ctx.geometry_out = store_n

        # --- read u_coord back as a field for Attribute Statistic ---
        read_u = g.named_attribute(location=(50, 150))
        read_u.data_type = 'FLOAT'
        read_u.inputs["Name"].default_value = "u_coord"

        # --- Attribute Statistic: u_coord min/max ---
        stat_u = g.attribute_statistic(location=(150, 150))
        stat_u.data_type = 'FLOAT'
        stat_u.domain = 'POINT'
        g.link(store_n.outputs[0], stat_u.inputs[0])    # Geometry
        g.link(read_u.outputs["Attribute"], stat_u.inputs[1])  # Field (Selection)
        # In Blender 5.x, Attribute Statistic has: Geometry, Selection, Attribute
        # The "Attribute" input is a field — feed it the NamedAttribute reader

        ctx.u_min = stat_u  # outputs["Min"]
        ctx.u_max = stat_u  # outputs["Max"]

        # --- read v_coord back as a field for Attribute Statistic ---
        read_v = g.named_attribute(location=(50, 50))
        read_v.data_type = 'FLOAT'
        read_v.inputs["Name"].default_value = "v_coord"

        # --- Attribute Statistic: v_coord min/max ---
        stat_v = g.attribute_statistic(location=(150, 50))
        stat_v.data_type = 'FLOAT'
        stat_v.domain = 'POINT'
        g.link(store_n.outputs[0], stat_v.inputs[0])    # Geometry
        g.link(read_v.outputs["Attribute"], stat_v.inputs[1])  # Field

        ctx.v_min = stat_v
        ctx.v_max = stat_v

        # --- derived: width = u_max - u_min ---
        width = g.math('SUBTRACT', location=(250, 150))
        g.link(stat_u.outputs["Max"], width.inputs[0])
        g.link(stat_u.outputs["Min"], width.inputs[1])
        ctx.width = width

        # --- derived: height = v_max - v_min ---
        height = g.math('SUBTRACT', location=(250, 50))
        g.link(stat_v.outputs["Max"], height.inputs[0])
        g.link(stat_v.outputs["Min"], height.inputs[1])
        ctx.height = height

        return ctx


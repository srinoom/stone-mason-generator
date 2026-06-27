"""Scatter Engine -- the procedural stone-distribution foundation.

Pipeline:
    Input Mesh
      → Mesh-to-Points (surface sample)
      → Instance-on-Points (stone prototypes)
      → Realize Instances
      → Output Mesh

This is Step 4 of the Stone Mason Generator roadmap.
The scatter engine is the base layer; later steps add course generation,
stone segmentation, shape variation, and physics relaxation on top.
"""

import bpy
from typing import Optional

from .graph import NodeGraph


class ScatterEngine:
    """Builds a Geometry Node tree that scatters stone cubes on a mesh surface.

    The group exposes four input sockets -- **Density**, **Seed**,
    **Stone Width**, **Stone Height** -- so the operator / UI can
    drive the scatter without rebuilding the tree.
    """

    GROUP_NAME = "SMG_ScatterEngine"

    # Interface sockets: (name, in_out, socket_type, default_value)
    SOCKETS = [
        ("Geometry",      "INPUT",  "NodeSocketGeometry", None),
        ("Density",       "INPUT",  "NodeSocketFloat",    40.0),
        ("Seed",          "INPUT",  "NodeSocketInt",      0),
        ("Stone Width",   "INPUT",  "NodeSocketFloat",    0.50),
        ("Stone Height",  "INPUT",  "NodeSocketFloat",    0.25),
        ("Geometry",      "OUTPUT", "NodeSocketGeometry", None),
    ]

    def __init__(self, group: bpy.types.NodeTree):
        self.group = group
        self.graph = NodeGraph(group)

    # -- public API --------------------------------------------------------

    def build(self) -> bpy.types.NodeTree:
        """Clear the group and rebuild the entire scatter node tree."""
        self._ensure_interface()
        self.graph.clear()
        self._layout()
        return self.group

    # -- private -----------------------------------------------------------

    def _ensure_interface(self) -> None:
        """Create group interface sockets if they don't already exist."""
        existing = {s.name for s in self.group.interface.items
                    if s.item_type == 'SOCKET'}

        for name, in_out, sock_type, default in self.SOCKETS:
            if name in existing:
                continue
            sock = self.group.interface.new_socket(
                name=name,
                in_out=in_out,
                socket_type=sock_type,
            )
            if default is not None:
                sock.default_value = default

    def _layout(self) -> None:
        g = self.graph

        gi = g.group_input()

        # --- surface → points ---
        mtp = g.node(
            "GeometryNodeMeshToPoints",
            location=(0, 0),
            label="Surface to Points",
        )
        mtp.inputs["Mode"].default_value = 'VERTICES'  # type: ignore[assignment]

        # TODO Step 5: replace Mesh-to-Points with a proper UV-grid / course
        #   generator that lays out points in rows (courses) instead of
        #   raw vertices.  This is the layer Course Generator will plug into.

        # --- stone prototype ---
        stone = g.cube(location=(350, -200))

        # --- instance ---
        inst = g.instance_on_points(location=(350, 0))

        # --- realize ---
        realize = g.realize_instances(location=(600, 0))

        go = g.group_output()

        # --- links ---
        # geometry flow
        g.link(gi.outputs["Geometry"], mtp.inputs["Mesh"])
        g.link(mtp.outputs["Points"], inst.inputs["Points"])
        g.link(stone.outputs["Mesh"], inst.inputs["Instance"])
        g.link(inst.outputs["Instances"], realize.inputs["Geometry"])
        g.link(realize.outputs["Geometry"], go.inputs["Geometry"])

        # param wiring (density, seed, size → node inputs)
        g.link(gi.outputs["Density"], mtp.inputs["Radius"])
        g.link(gi.outputs["Stone Width"],
               stone.inputs["Size"])  # vector auto-expand on cube
        g.link(gi.outputs["Seed"], inst.inputs["Pick Index"])  # placeholder


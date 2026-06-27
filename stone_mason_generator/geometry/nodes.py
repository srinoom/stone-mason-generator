"""Composition layer -- orchestrates engine build order and interface.

Pipeline (Step 14):
    1. ParameterizeEngine
    2. SurfaceTopology
    3. CourseEngine
    4. CourseLayout
    5. RunningBond
    6. InstanceEngine -- RectangularBlock + 4 modifier stack, realize
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .surface_context import SurfaceContext
from .parameterize import ParameterizeEngine
from .topology import SurfaceTopology
from .course import CourseEngine
from .layout import CourseLayout, LayoutStrategy
from .bond import RunningBond
from .instance import InstanceEngine
from .primitive import RectangularBlock
from .modifier_base import ModifierContext, ValidationReport
from .modifier import (NoiseModifier, EdgeBevelModifier,
                       FaceIrregularity, CornerBreak)


class Composer:
    """Orchestrates the full node-graph pipeline from registered engines."""

    GROUP_NAME = "SMG_StoneGenerator"

    BASE_SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Geometry", "INPUT",  "NodeSocketGeometry", None),
        ("Geometry", "OUTPUT", "NodeSocketGeometry", None),
    ]

    def __init__(self):
        self._engines = []

    def register_engine(self, engine) -> None:
        self._engines.append(engine)

    def all_sockets(self) -> List[Tuple[str, str, str, object]]:
        sockets = list(self.BASE_SOCKETS)
        for engine in self._engines:
            sockets.extend(engine.SOCKETS)
            frame_sockets = getattr(engine, 'frame_sockets', [])
            sockets.extend(frame_sockets)
            primitive_sockets = getattr(engine, 'primitive_sockets', [])
            sockets.extend(primitive_sockets)
        return sockets

    def create_fresh_group(self) -> bpy.types.NodeTree:
        """Delete any existing group and create a brand new one.

        This avoids all Blender interface API iteration issues —
        we never query or modify an existing interface.
        """
        # Remove existing group entirely
        existing = bpy.data.node_groups.get(self.GROUP_NAME)
        if existing is not None:
            bpy.data.node_groups.remove(existing)

        group = bpy.data.node_groups.new(self.GROUP_NAME, "GeometryNodeTree")

        # Create interface sockets on the fresh group
        for name, in_out, sock_type, default in self.all_sockets():
            sock = group.interface.new_socket(
                name=name,
                in_out=in_out,
                socket_type=sock_type,
            )
            if default is not None:
                sock.default_value = default

        return group

    def build_pipeline(self, group: bpy.types.NodeTree,
                       ctx: ModifierContext = None,
                       report: ValidationReport = None) -> None:
        """Build the node tree inside an already-interface'd group."""
        graph = NodeGraph(group)
        graph.clear()

        gi = graph.group_input(location=(-800, 0))

        prev = gi
        surface_ctx = None

        for engine in self._engines:
            if isinstance(engine, ParameterizeEngine):
                prev = engine.build(graph, gi, prev)
                surface_ctx = getattr(graph, 'surface_context', None)
            elif isinstance(engine, SurfaceTopology):
                prev = engine.build(graph, gi, prev, surface_ctx)
            elif isinstance(engine, LayoutStrategy):
                prev = engine.build(graph, gi, prev, surface_ctx)
            elif isinstance(engine, InstanceEngine):
                prev = engine.build(graph, gi, prev, ctx, report)
            else:
                prev = engine.build(graph, gi, prev)

        go = graph.group_output(location=(800, 0))
        graph.link(prev.outputs["Geometry"],
                   go.inputs["Geometry"])

    def build_group(self, group: bpy.types.NodeTree,
                    ctx: ModifierContext = None,
                    report: ValidationReport = None) -> None:
        """Legacy entry — builds pipeline into existing group.
        Use create_fresh_group() + build_pipeline() for clean rebuild.
        """
        self.build_pipeline(group, ctx, report)


def default_composer() -> Composer:
    """Return a Composer pre-loaded with the full pipeline."""
    c = Composer()
    c.register_engine(ParameterizeEngine())
    c.register_engine(SurfaceTopology())
    c.register_engine(CourseEngine())
    c.register_engine(CourseLayout())
    c.register_engine(RunningBond())
    c.register_engine(InstanceEngine(
        primitive=RectangularBlock(),
        modifiers=[
            EdgeBevelModifier(),
            FaceIrregularity(),
            NoiseModifier(),
            CornerBreak(),
        ],
        realize=True,
    ))
    return c


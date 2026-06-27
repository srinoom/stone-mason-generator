"""Composition layer -- orchestrates engine build order and interface.

Pipeline (Step 14):
    1. ParameterizeEngine
    2. SurfaceTopology
    3. CourseEngine
    4. CourseLayout
    5. RunningBond
    6. InstanceEngine -- RectangularBlock + 4 modifier stack, realize

Modifiers applied (in order):
    EdgeBevel → FaceIrregularity → NoiseModifier → CornerBreak
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

    def build_group(self, group: bpy.types.NodeTree,
                    ctx: ModifierContext = None,
                    report: ValidationReport = None) -> None:
        self._ensure_interface(group)

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

    def _ensure_interface(self, group: bpy.types.NodeTree) -> None:
        # Clear all existing interface items, then recreate fresh.
        # This avoids API differences between Blender versions for
        # iterating interface items (items vs items_tree vs items_tree()).
        try:
            group.interface.clear()
        except Exception:
            pass

        for name, in_out, sock_type, default in self.all_sockets():
            try:
                sock = group.interface.new_socket(
                    name=name,
                    in_out=in_out,
                    socket_type=sock_type,
                )
                if default is not None:
                    sock.default_value = default
            except Exception:
                pass


def default_composer() -> Composer:
    """Return a Composer pre-loaded with the full pipeline.

    Modifier stack order:
        1. EdgeBevel     — bevel edges (needs original mesh)
        2. FaceIrregularity — per-face random scale variation
        3. NoiseModifier — surface roughness displacement
        4. CornerBreak   — chipped corners
    """
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




"""Composition layer -- orchestrates engine build order and interface.

The Composer is the single place that knows:
  - which engines exist
  - what order they run in
  - which interface sockets the group needs

Engines declare socket requirements via ``SOCKETS`` and expose a
``build(graph, group_input, prev_geometry) -> node`` method.

Pipeline:
    1. CourseEngine  -- assign course_index using WallFrame
    2. BondPattern   -- stagger courses with horizontal offset
    3. ScatterEngine -- distribute stones on faces (inherits courses + bond)

Builder never imports engines directly -- it calls Composer.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .course import CourseEngine
from .bond import RunningBond
from .scatter import ScatterEngine


class Composer:
    """Orchestrates the full node-graph pipeline from registered engines."""

    GROUP_NAME = "SMG_StoneGenerator"

    # Fixed interface sockets that every pipeline needs
    BASE_SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Geometry", "INPUT",  "NodeSocketGeometry", None),
        ("Geometry", "OUTPUT", "NodeSocketGeometry", None),
    ]

    def __init__(self):
        self._engines = []

    def register_engine(self, engine) -> None:
        """Register a pipeline stage."""
        self._engines.append(engine)

    # -- interface management ---------------------------------------------

    def all_sockets(self) -> List[Tuple[str, str, str, object]]:
        """Return the complete socket list: base + engine + frame sockets."""
        sockets = list(self.BASE_SOCKETS)
        for engine in self._engines:
            sockets.extend(engine.SOCKETS)
            frame_sockets = getattr(engine, 'frame_sockets', [])
            sockets.extend(frame_sockets)
        return sockets

    # -- build -------------------------------------------------------------

    def build_group(self, group: bpy.types.NodeTree) -> None:
        """Ensure interface sockets exist, clear nodes, run the pipeline."""
        self._ensure_interface(group)

        graph = NodeGraph(group)
        graph.clear()

        gi = graph.group_input(location=(-800, 0))

        # Chain engines: each takes previous geometry, returns new geometry
        prev = gi  # start from group input
        for engine in self._engines:
            prev = engine.build(graph, gi, prev)

        # Final output
        go = graph.group_output(location=(800, 0))
        graph.link(prev.outputs["Geometry"],
                   go.inputs["Geometry"])

    # -- private -----------------------------------------------------------

    def _ensure_interface(self, group: bpy.types.NodeTree) -> None:
        """Create interface sockets that don't yet exist."""
        existing = {s.name for s in group.interface.items
                    if s.item_type == 'SOCKET'}

        for name, in_out, sock_type, default in self.all_sockets():
            if name in existing:
                continue
            sock = group.interface.new_socket(
                name=name,
                in_out=in_out,
                socket_type=sock_type,
            )
            if default is not None:
                sock.default_value = default


def default_composer() -> Composer:
    """Return a Composer pre-loaded with the current pipeline engines.

    Pipeline order:
        1. CourseEngine   -- assign course_index (ZUpFrame)
        2. RunningBond    -- stagger odd courses by Bond Offset
        3. ScatterEngine  -- distribute stones (inherits courses + bond)
    """
    c = Composer()
    c.register_engine(CourseEngine())       # defaults to ZUpFrame
    c.register_engine(RunningBond())        # defaults to 50% stagger
    c.register_engine(ScatterEngine())
    return c


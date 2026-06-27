"""Bond Pattern Engine -- staggers stone positions along wall run (U axis).

Refactored in Step 8 architecture review:
  - Bond now operates on SCATTERED POINTS, not on the source mesh
  - Reads course_index from points (transferred from mesh via
    Blender attribute interpolation)
  - Shifts point positions along X (U axis) using Set Position
  - Does NOT touch the source mesh geometry
  - bond_offset attribute is no longer stored (computed + applied
    in one pass, no downstream consumer needs it)

Pipeline stage (runs AFTER ScatterEngine, BEFORE InstanceEngine):

    Points (with course_index attribute)
      → read course_index
      → calc offset per bond strategy
      → Set Position (shift along X)
      → Output Points (shifted)

Bond styles are subclasses of BondPattern.  Each overrides
:meth:`calc_offset` to compute a horizontal offset from course_index.
CourseEngine is never modified.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class BondPattern:
    """Abstract base for bond (stagger) patterns.

    Subclasses override :meth:`calc_offset` to build the node sub-tree
    that computes a horizontal offset scalar from course_index.
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Bond Offset", "INPUT", "NodeSocketFloat", 0.25),
    ]

    def calc_offset(self, graph: NodeGraph,
                    group_input: bpy.types.Node,
                    course_index_node: bpy.types.Node) -> bpy.types.Node:
        """Return a Math node whose output 0 is the per-point offset.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node (for parameter access).
            course_index_node: Named Attribute node reading "course_index".

        Override in subclasses to implement different bond styles.
        """
        raise NotImplementedError

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the bond-pattern sub-tree on scattered points.

        Reads course_index from points, computes horizontal offset,
        shifts point positions along X (U axis), returns shifted points.
        """
        g = graph

        # --- read course_index from points ---
        read_idx = g.named_attribute(location=(-400, 0))
        read_idx.data_type = 'FLOAT'
        read_idx.inputs["Name"].default_value = "course_index"

        # --- compute offset via subclass strategy ---
        offset_node = self.calc_offset(g, group_input, read_idx)

        # --- build offset vector (X = offset, Y = 0, Z = 0) ---
        combine = g.combine_xyz(location=(100, 0))
        g.link(offset_node.outputs[0], combine.inputs["X"])

        # --- set position: shift points along X ---
        set_pos = g.set_position(location=(200, 0))
        g.link(prev_geometry.outputs["Points"],
               set_pos.inputs[0])  # Geometry input
        g.link(combine.outputs["Vector"],
               set_pos.inputs["Offset"])  # Vector offset

        return set_pos


class RunningBond(BondPattern):
    """Running bond: stagger odd courses by Bond Offset.

    offset = (course_index % 2) * bond_offset

    Even courses: no shift.  Odd courses: shifted by Bond Offset.
    """

    def calc_offset(self, graph: NodeGraph,
                    group_input: bpy.types.Node,
                    course_index_node: bpy.types.Node) -> bpy.types.Node:
        g = graph

        # --- course_index % 2 → 0 (even) or 1 (odd) ---
        modulo = g.math('MODULO', location=(-200, 0))
        modulo.inputs[1].default_value = 2.0
        g.link(course_index_node.outputs["Attribute"], modulo.inputs[0])

        # --- offset = mod_result * bond_offset ---
        mul = g.math('MULTIPLY', location=(0, 0))
        g.link(modulo.outputs[0], mul.inputs[0])
        g.link(group_input.outputs["Bond Offset"], mul.inputs[1])

        return mul



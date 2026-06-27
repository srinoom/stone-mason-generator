"""Bond Pattern Engine -- generates staggered masonry offsets.

Pipeline stage (runs AFTER CourseEngine, BEFORE ScatterEngine):

    Geometry (with course_index attribute)
      → read course_index
      → compute horizontal offset (subclass strategy)
      → Set Position (shift along X / wall-run axis)
      → store bond_offset attribute
      → Output Geometry (shifted)

Bond styles are implemented as subclasses of BondPattern.
Each subclass overrides :meth:`calc_offset` to produce a different
horizontal offset pattern. CourseEngine is never modified.

Current implementation: RunningBond (50% offset on odd courses).
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
        """Return a node whose output 0 is the per-vertex offset scalar.

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
        """Build the bond-pattern sub-tree.

        Reads course_index (set by CourseEngine), computes horizontal
        offset, shifts geometry along X (wall run direction), and
        stores the offset as an attribute for downstream engines.
        """
        g = graph

        # --- read course_index from geometry ---
        read_idx = g.named_attribute(location=(-400, 0))
        read_idx.data_type = 'FLOAT'
        read_idx.inputs["Name"].default_value = "course_index"

        # --- compute offset via subclass strategy ---
        offset_node = self.calc_offset(g, group_input, read_idx)

        # --- build offset vector (X, 0, 0) via Combine XYZ ---
        combine_offset = g.combine_xyz(location=(50, 100))
        g.link(offset_node.outputs[0], combine_offset.inputs["X"])
        # Y and Z default to 0 — no vertical shift

        # --- set position: add offset vector to current position ---
        set_pos = g.set_position(location=(200, 0))
        g.link(prev_geometry.outputs[0], set_pos.inputs["Geometry"])
        g.link(combine_offset.outputs[0], set_pos.inputs["Offset"])

        # --- store bond_offset attribute ---
        store_offset = g.store_named_attribute(location=(350, 0))
        store_offset.data_type = 'FLOAT'
        store_offset.domain = 'POINT'
        store_offset.inputs["Name"].default_value = "bond_offset"
        g.link(set_pos.outputs[0], store_offset.inputs["Geometry"])
        g.link(offset_node.outputs[0], store_offset.inputs["Value"])

        return store_offset


class RunningBond(BondPattern):
    """Running bond: 50% offset on odd courses.

    offset = (course_index % 2) * bond_offset

    This is the classic brick-laying stagger pattern.
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


"""Stone Modifier base classes — shared interface for all modifiers.

Extracted in Step 14 so modifier.py contains only implementations.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class ModifierContext:
    """Read-only snapshot of current property values for modifier decisions."""

    def __init__(self, props):
        self.props = props
        self.roughness = getattr(props, 'roughness', 0.0)
        self.noise_scale = getattr(props, 'noise_scale', 5.0)
        self.stone_width = getattr(props, 'stone_width', 0.5)
        self.stone_height = getattr(props, 'stone_height', 0.25)
        self.stone_depth = getattr(props, 'stone_depth', 0.3)
        self.joint_width = getattr(props, 'joint_width', 0.02)
        self.course_height = getattr(props, 'course_height', 0.5)
        self.bond_offset = getattr(props, 'bond_offset', 0.25)
        self.size_variation = getattr(props, 'size_variation', 0.05)
        self.edge_bevel = getattr(props, 'edge_bevel', 0.03)
        self.corner_break = getattr(props, 'corner_break', 0.02)
        self.seed = getattr(props, 'seed', 0)


class ValidationReport:
    """Collects validation warnings and errors."""

    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            lines.extend(f"  - {e}" for e in self.errors)
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            lines.extend(f"  - {w}" for w in self.warnings)
        return "\n".join(lines) if lines else "OK"


class StoneModifier:
    """Abstract base for stone surface modifiers.

    Subclasses override:
      - :meth:`enabled` — return False to skip node generation
      - :meth:`apply`    — transform mesh, return result node
    """

    SOCKETS: List[Tuple[str, str, str, object]] = []

    def enabled(self, ctx: ModifierContext) -> bool:
        return True

    def apply(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              mesh_node: bpy.types.Node,
              ctx: ModifierContext,
              report: ValidationReport) -> bpy.types.Node:
        raise NotImplementedError

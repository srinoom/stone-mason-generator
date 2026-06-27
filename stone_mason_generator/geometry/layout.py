"""Layout Engine — deterministic point generation for masonry.

Replaces random "Distribute Points on Faces" with a layout-based
point generator. Points are placed in a deterministic grid pattern
derived from stone/joint dimensions and SurfaceContext bounds.

Pipeline stage (runs AFTER CourseEngine, BEFORE BondEngine):

    Geometry (with course_index, v_coord, u_coord)
      → SurfaceContext provides width, height bounds
      → Mesh Grid (rows = courses, cols = stones per course)
      → Mesh-to-Points (extract vertices as point cloud)
      → course_index recomputed from grid row position
      → Output Points

Layout strategies are subclasses of LayoutStrategy.
Each overrides :meth:`build` to produce a different point layout.
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph
from .surface_context import SurfaceContext


class LayoutStrategy:
    """Abstract base for point layout strategies.

    Subclasses override :meth:`build` to produce a point cloud.

    Every layout must:
      - Output a Points geometry
      - Store ``course_index`` as a FLOAT attribute (POINT domain)
      - Accept geometry from the previous pipeline stage
    """

    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node,
              ctx: SurfaceContext = None) -> bpy.types.Node:
        raise NotImplementedError


class CourseLayout(LayoutStrategy):
    """Grid layout aligned to masonry courses.

    Uses SurfaceContext.width and .height (derived from u_coord/v_coord
    attribute statistics) instead of Bounding Box. This decouples layout
    from world-space dimensions and enables curved/sloped walls once
    a non-ZUp WallFrame is implemented.

    Parameters (via interface sockets):
      - Stone Width:   width of a single stone
      - Joint Width:   gap between adjacent stones in a course
      - Course Height: height of each course (row)
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Stone Width",   "INPUT", "NodeSocketFloat", 0.50),
        ("Joint Width",   "INPUT", "NodeSocketFloat", 0.02),
        ("Course Height", "INPUT", "NodeSocketFloat", 0.50),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node,
              ctx: SurfaceContext = None) -> bpy.types.Node:
        """Build the course-aligned grid layout from SurfaceContext bounds."""
        g = graph

        # --- stone_unit = Stone Width + Joint Width ---
        stone_unit = g.math('ADD', location=(-500, -100))
        g.link(group_input.outputs["Stone Width"], stone_unit.inputs[0])
        g.link(group_input.outputs["Joint Width"], stone_unit.inputs[1])

        # --- columns = wall_width / stone_unit ---
        col_count = g.math('DIVIDE', location=(-400, -100))
        g.link(ctx.width.outputs[0], col_count.inputs[0])
        g.link(stone_unit.outputs[0], col_count.inputs[1])

        # --- rows = wall_height / course_height ---
        row_count = g.math('DIVIDE', location=(-400, 100))
        g.link(ctx.height.outputs[0], row_count.inputs[0])
        g.link(group_input.outputs["Course Height"], row_count.inputs[1])

        # --- float→int conversion ---
        col_int = g.float_to_int(location=(-300, -100))
        col_int.rounding_mode = 'FLOOR'  # type: ignore[assignment]
        g.link(col_count.outputs[0], col_int.inputs["Float"])

        row_int = g.float_to_int(location=(-300, 100))
        row_int.rounding_mode = 'FLOOR'  # type: ignore[assignment]
        g.link(row_count.outputs[0], row_int.inputs["Float"])

        # --- grid physical size ---
        size_x = g.math('MULTIPLY', location=(-250, -200))
        g.link(col_int.outputs[0], size_x.inputs[0])
        g.link(stone_unit.outputs[0], size_x.inputs[1])

        size_y = g.math('MULTIPLY', location=(-250, 200))
        g.link(row_int.outputs[0], size_y.inputs[0])
        g.link(group_input.outputs["Course Height"], size_y.inputs[1])

        # --- create Mesh Grid ---
        grid = g.mesh_grid(location=(0, 0))
        g.link(size_x.outputs[0], grid.inputs["Size X"])
        g.link(size_y.outputs[0], grid.inputs["Size Y"])
        g.link(col_int.outputs[0], grid.inputs["Vertices X"])
        g.link(row_int.outputs[0], grid.inputs["Vertices Y"])

        # --- rotate XY → XZ (90° around X) ---
        transform = g.transform_geometry(location=(150, 0))
        transform.inputs["Rotation"].default_value = (1.5707963, 0, 0)
        g.link(grid.outputs["Mesh"], transform.inputs[0])

        # --- mesh vertices → points ---
        mtp = g.mesh_to_points(location=(300, 0))
        mtp.mode = 'VERTICES'  # type: ignore[assignment]
        g.link(transform.outputs["Geometry"], mtp.inputs["Mesh"])

        # --- course_index from position.z ---
        pos = g.position(location=(300, 250))
        sep_pos = g.separate_xyz(location=(400, 250))
        g.link(pos.outputs[0], sep_pos.inputs["Vector"])

        div_z = g.math('DIVIDE', location=(500, 250))
        g.link(sep_pos.outputs["Z"], div_z.inputs[0])
        g.link(group_input.outputs["Course Height"], div_z.inputs[1])

        floor_z = g.math('FLOOR', location=(600, 250))
        g.link(div_z.outputs[0], floor_z.inputs[0])

        # --- store course_index on points ---
        store_idx = g.store_named_attribute(location=(450, 0))
        store_idx.data_type = 'FLOAT'
        store_idx.domain = 'POINT'
        store_idx.inputs["Name"].default_value = "course_index"
        g.link(mtp.outputs["Points"], store_idx.inputs["Geometry"])
        g.link(floor_z.outputs[0], store_idx.inputs["Value"])

        return store_idx


class RandomScatter(LayoutStrategy):
    """Random scatter fallback — preserves old Distribute Points behavior."""

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Density", "INPUT", "NodeSocketFloat", 50.0),
        ("Seed",    "INPUT", "NodeSocketInt",   0),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node,
              ctx: SurfaceContext = None) -> bpy.types.Node:
        g = graph

        distribute = g.distribute_points_on_faces(location=(-400, 0))
        distribute.distribute_method = 'RANDOM'  # type: ignore[assignment]

        g.link(prev_geometry.outputs[0],
               distribute.inputs["Mesh"])
        g.link(group_input.outputs["Density"],
               distribute.inputs["Density"])
        g.link(group_input.outputs["Seed"],
               distribute.inputs["Seed"])

        return distribute



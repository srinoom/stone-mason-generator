"""Layout Engine -- deterministic point generation for masonry.

Replaces random "Distribute Points on Faces" with a layout-based
point generator.  Points are placed in a deterministic grid pattern
derived from stone and joint dimensions.

Pipeline stage (runs AFTER CourseEngine, BEFORE BondEngine):

    Geometry (with course_index)
      → Bounding Box (wall dimensions)
      → Mesh Grid (rows = courses, cols = stones per course)
      → Mesh-to-Points (extract vertices as point cloud)
      → Store course_index from row number
      → Output Points

Layout strategies are subclasses of LayoutStrategy.
Each overrides :meth:`build` to produce a different point layout.
CourseEngine is never modified.

Current implementation: CourseLayout (grid aligned to courses).
"""

import bpy
from typing import List, Tuple

from .graph import NodeGraph


class LayoutStrategy:
    """Abstract base for point layout strategies.

    Subclasses override :meth:`build` to produce a point cloud whose
    positions encode the stone placement pattern.

    Every layout must:
      - Output a Points geometry
      - Store ``course_index`` as a FLOAT attribute (POINT domain)
      - Accept geometry from the previous pipeline stage (the mesh
        with course attributes already set by CourseEngine)
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = []

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the layout sub-tree.

        Args:
            graph: NodeGraph wrapper.
            group_input: Group Input node.
            prev_geometry: Previous geometry (mesh with course_index).

        Returns:
            A node whose geometry output is a Points cloud with
            course_index attribute.
        """
        raise NotImplementedError


class CourseLayout(LayoutStrategy):
    """Grid layout aligned to masonry courses.

    Generates a Mesh Grid sized to the wall bounding box, where:
      - Rows correspond to courses (row count = wall_height / course_height)
      - Columns correspond to stone slots (col count = wall_width / stone_unit)

    The grid is then converted to points, and each point receives a
    ``course_index`` derived from its row number.

    Parameters (via interface sockets):
      - Stone Width:  width of a single stone
      - Joint Width:  gap between adjacent stones in a course
      - Course Height: height of each course (row)
    """

    # (name, in_out, socket_type, default_value)
    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Stone Width",   "INPUT", "NodeSocketFloat", 0.50),
        ("Joint Width",   "INPUT", "NodeSocketFloat", 0.02),
        ("Course Height", "INPUT", "NodeSocketFloat", 0.50),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
        """Build the course-aligned grid layout."""
        g = graph

        # --- wall dimensions from bounding box ---
        bbox = g.bounding_box(location=(-700, 0))
        g.link(prev_geometry.outputs[0], bbox.inputs[0])

        # Bounding box outputs: Bounding Box (geometry) + Dimensions (vector)
        # We need width (X) and height (Z) of the wall.
        sep_dim = g.separate_xyz(location=(-600, 0))
        g.link(bbox.outputs["Dimensions"], sep_dim.inputs["Vector"])

        # --- stone unit = Stone Width + Joint Width ---
        stone_unit = g.math('ADD', location=(-500, -100))
        g.link(group_input.outputs["Stone Width"], stone_unit.inputs[0])
        g.link(group_input.outputs["Joint Width"], stone_unit.inputs[1])

        # --- number of columns (stones per course) = wall_width / stone_unit ---
        col_count = g.math('DIVIDE', location=(-400, -100))
        g.link(sep_dim.outputs["X"], col_count.inputs[0])  # wall width
        g.link(stone_unit.outputs[0], col_count.inputs[1])

        # --- number of rows (courses) = wall_height / course_height ---
        row_count = g.math('DIVIDE', location=(-400, 100))
        g.link(sep_dim.outputs["Z"], row_count.inputs[0])  # wall height
        g.link(group_input.outputs["Course Height"], row_count.inputs[1])

        # --- float→int conversion for grid size inputs ---
        col_int = g.float_to_int(location=(-300, -100))
        col_int.rounding_mode = 'FLOOR'  # type: ignore[assignment]
        g.link(col_count.outputs[0], col_int.inputs["Float"])

        row_int = g.float_to_int(location=(-300, 100))
        row_int.rounding_mode = 'FLOOR'  # type: ignore[assignment]
        g.link(row_count.outputs[0], row_int.inputs["Float"])

        # --- create Mesh Grid ---
        # Mesh Grid creates a grid in the XY plane centered at origin.
        # Size X = number of columns, Size Y = number of rows (will be
        # rotated to align Y→Z for vertical courses).
        grid = g.mesh_grid(location=(-150, 0))
        g.link(col_int.outputs[0], grid.inputs["Size X"])
        g.link(row_int.outputs[0], grid.inputs["Size Y"])
        # Vertices X/Y control the actual subdivision count.
        # For a grid of N×M vertices, Size X/Y = N-1 and M-1 but
        # Blender's Mesh Grid uses Size as the vertex count directly
        # when "Vertices X/Y" is set.  We set Vertices to the integer
        # counts so each vertex = one stone slot.
        grid.inputs["Vertices X"].default_value = 2  # min 2; will be overridden
        grid.inputs["Vertices Y"].default_value = 2

        # Actually, Mesh Grid in Blender 4.x/5.x works as:
        #   Size X/Y = physical size of the grid
        #   Vertices X/Y = number of vertices along each axis
        # We want vertex spacing = stone_unit along X, course_height along Z.
        # So: Size X = col_int * stone_unit, Size Y = row_int * course_height
        # Vertices X = col_int, Vertices Y = row_int

        # Recalculate grid physical size
        size_x = g.math('MULTIPLY', location=(-250, -200))
        g.link(col_int.outputs[0], size_x.inputs[0])
        g.link(stone_unit.outputs[0], size_x.inputs[1])

        size_y = g.math('MULTIPLY', location=(-250, 200))
        g.link(row_int.outputs[0], size_y.inputs[0])
        g.link(group_input.outputs["Course Height"], size_y.inputs[1])

        grid2 = g.mesh_grid(location=(0, 0))
        g.link(size_x.outputs[0], grid2.inputs["Size X"])
        g.link(size_y.outputs[0], grid2.inputs["Size Y"])
        g.link(col_int.outputs[0], grid2.inputs["Vertices X"])
        g.link(row_int.outputs[0], grid2.inputs["Vertices Y"])

        # --- rotate grid from XY to XZ plane (Y→Z, 90° around X) ---
        transform = g.transform_geometry(location=(150, 0))
        transform.inputs["Rotation"].default_value = (1.5707963, 0, 0)  # 90° X

        g.link(grid2.outputs["Mesh"], transform.inputs[0])

        # --- convert mesh vertices to points ---
        mtp = g.mesh_to_points(location=(300, 0))
        mtp.inputs["Mode"].default_value = 'VERTICES'  # type: ignore[assignment]
        g.link(transform.outputs["Geometry"], mtp.inputs["Mesh"])

        # --- compute course_index from point position ---
        # course_index = floor(position.z / course_height)
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
        g.link(mtp.outputs["Points"], store_idx.inputs[0])
        g.link(floor_z.outputs[0], store_idx.inputs["Value"])

        return store_idx


class RandomScatter(LayoutStrategy):
    """Random scatter fallback — preserves old behavior.

    Uses Distribute Points on Faces.  Provided as a strategy option
    so users can switch between deterministic and random layouts.
    """

    SOCKETS: List[Tuple[str, str, str, object]] = [
        ("Density", "INPUT", "NodeSocketFloat", 50.0),
        ("Seed",    "INPUT", "NodeSocketInt",   0),
    ]

    def build(self, graph: NodeGraph,
              group_input: bpy.types.Node,
              prev_geometry: bpy.types.Node) -> bpy.types.Node:
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


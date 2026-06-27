"""Stone Mason Generator -- main add-on module.

Step 7: WallFrame abstraction — CourseEngine no longer tied to world Z.
"""

bl_info = {
    "name": "Stone Mason Generator",
    "author": "Boy + ChatGPT",
    "version": (0, 8, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Stone",
    "description": "Generate procedural stone masonry from meshes.",
    "category": "Object",
}

from . import properties
from . import operators
from . import panel
from .geometry import builder
from .geometry import graph
from .geometry import wall_frame
from .geometry import course
from .geometry import scatter
from .geometry import nodes

modules = (
    graph,
    wall_frame,
    course,
    scatter,
    nodes,
    builder,
    properties,
    operators,
    panel,
)


def register():
    properties.register()
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()


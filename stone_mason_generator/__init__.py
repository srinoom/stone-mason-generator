"""Stone Mason Generator -- main add-on module.

Step 4: Graph API refactor + Scatter Engine base layer.
"""

bl_info = {
    "name": "Stone Mason Generator",
    "author": "Boy + ChatGPT",
    "version": (0, 5, 0),
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
from .geometry import scatter

modules = (
    graph,
    scatter,
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


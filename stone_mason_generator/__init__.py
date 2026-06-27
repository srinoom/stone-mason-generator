"""Stone Mason Generator -- main add-on module.

Step 13: Conditional modifiers + validation + robustness.
"""

bl_info = {
    "name": "Stone Mason Generator",
    "author": "Boy + ChatGPT",
    "version": (1, 4, 0),
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
from .geometry import surface_context
from .geometry import parameterize
from .geometry import topology
from .geometry import course
from .geometry import layout
from .geometry import scatter
from .geometry import bond
from .geometry import primitive
from .geometry import modifier
from .geometry import instance
from .geometry import nodes

modules = (
    graph,
    wall_frame,
    surface_context,
    parameterize,
    topology,
    course,
    layout,
    scatter,
    bond,
    primitive,
    modifier,
    instance,
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

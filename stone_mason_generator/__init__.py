bl_info = {
    "name": "Stone Mason Generator",
    "author": "Boy + ChatGPT",
    "version": (0, 1, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Stone",
    "description": "Generate procedural stacked stone from meshes.",
    "category": "Object",
}

import importlib

from . import properties
from . import operators
from . import panel
from .geometry import builder
from .geometry import nodes
from .geometry import graph

modules = (
    graph,
    nodes,
    builder,
    properties,
    operators,
    panel,
)


def register():

    for m in modules:
        importlib.reload(m)

    properties.register()
    operators.register()
    panel.register()


def unregister():

    panel.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
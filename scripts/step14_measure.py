"""Step 14 measurement script.

Run in Blender:  Scripting tab → Open → Run Script
Outputs node count, vertex count, instance count, generation time.

Usage:
    1. Create a Plane mesh (e.g. 4m × 3m)
    2. Select the plane
    3. Run this script
"""

import bpy
import time

# --- Before: count nodes in existing group (if any) ---
group_name = "SMG_StoneGenerator"
existing = bpy.data.node_groups.get(group_name)
before_nodes = len(existing.nodes) if existing else 0

# --- Generate ---
t0 = time.perf_counter()
bpy.ops.stone.generate()
t1 = time.perf_counter()

gen_time = t1 - t0

# --- After: count nodes ---
group = bpy.data.node_groups.get(group_name)
after_nodes = len(group.nodes) if group else 0

# --- Count instances / vertices ---
obj = bpy.context.active_object
eval_obj = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = eval_obj.to_mesh()

vert_count = len(mesh.vertices)
poly_count = len(mesh.polygons)

eval_obj.to_mesh_clear()

# --- Report ---
print("=" * 50)
print("STEP 14 — STONE SHAPE GENERATOR METRICS")
print("=" * 50)
print(f"Generation Time:  {gen_time:.3f}s")
print(f"Nodes Before:     {before_nodes}")
print(f"Nodes After:      {after_nodes}")
print(f"Delta Nodes:      +{after_nodes - before_nodes}")
print(f"Vertices:         {vert_count}")
print(f"Polygons:         {poly_count}")
print(f"Active Modifiers: {[m.name for m in obj.modifiers]}")
print("=" * 50)

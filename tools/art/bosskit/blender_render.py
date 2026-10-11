"""Blender 3.6 (run with --background --python): renders world-space boxes from bbmodel.Model.render_json.

Usage: blender -b --factory-startup --python blender_render.py -- job.json
job.json: {"boxes": [...], "out": dir, "views": [{"name", "mode": silhouette|clay|flat, "camera": ortho_front|...}]}
Blockbench (x, y, z) maps to Blender (x, -z, y) / 16: one Blender unit is one block, the model faces +Y.
"""
import json
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
job = json.load(open(args[0], encoding="utf-8"))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def to_blender(p):
    return Vector((p[0] / 16, -p[2] / 16, p[1] / 16))


# corner order from bbmodel.Cube.corners: x outer, y middle, z inner -> index = xi*4 + yi*2 + zi
QUADS = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
materials = {}


def material(color):
    key = tuple(round(c, 3) for c in color)
    if key not in materials:
        m = bpy.data.materials.new("m%d" % len(materials))
        m.diffuse_color = (*color, 1)
        materials[key] = m
    return materials[key]


verts, faces, face_mats = [], [], []
mat_list = []
for b in job["boxes"]:
    base = len(verts)
    verts += [to_blender(p) for p in b["corners"]]
    m = material(b["color"])
    if m not in mat_list:
        mat_list.append(m)
    for q in QUADS:
        faces.append(tuple(base + i for i in q))
        face_mats.append(mat_list.index(m))
mesh = bpy.data.meshes.new("boss")
mesh.from_pydata(verts, [], faces)
mesh.update()
obj = bpy.data.objects.new("boss", mesh)
scene.collection.objects.link(obj)
for m in mat_list:
    obj.data.materials.append(m)
for poly, mi in zip(mesh.polygons, face_mats):
    poly.material_index = mi
# outward normals regardless of corner winding
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")

lo = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
center = (lo + hi) / 2
size = hi - lo

# a player for scale (Steve proportions, 1.8 blocks tall), standing beside the model
PLAYER = [((-4, 0, -2), (0, 12, 2)), ((0, 0, -2), (4, 12, 2)), ((-4, 12, -2), (4, 24, 2)),
          ((-8, 12, -2), (-4, 24, 2)), ((4, 12, -2), (8, 24, 2)), ((-4, 24, -4), (4, 32, 4))]
player_obj = None
if job.get("player", True):
    pv, pf = [], []
    px, py = lo.x * 0.62, hi.y + 1.2
    for f, t in PLAYER:
        base = len(pv)
        for xi in (f[0], t[0]):
            for yi in (f[1], t[1]):
                for zi in (f[2], t[2]):
                    pv.append(Vector((px + xi * 1.8 / 32, py - zi * 1.8 / 32, yi * 1.8 / 32)))
        pf += [tuple(base + i for i in q) for q in QUADS]
    pm = bpy.data.meshes.new("player")
    pm.from_pydata(pv, [], pf)
    pm.update()
    player_obj = bpy.data.objects.new("player", pm)
    scene.collection.objects.link(player_obj)
    player_obj.data.materials.append(material((0.42, 0.55, 0.72)))

# ground plane for clay renders
bpy.ops.mesh.primitive_plane_add(size=200, location=(center.x, center.y, -0.001))
ground = bpy.context.active_object
ground.color = (*job.get("ground", (0.36, 0.35, 0.33)), 1)
ground.data.materials.append(material(tuple(job.get("ground", (0.36, 0.35, 0.33)))))

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
world = bpy.data.worlds.new("w")
scene.world = world
scene.render.resolution_x, scene.render.resolution_y = job.get("res", (900, 700))
aspect = scene.render.resolution_x / scene.render.resolution_y
scene.render.film_transparent = False
shading = scene.display.shading
scene.display_settings.display_device = "sRGB"
scene.view_settings.view_transform = "Standard"


def look_at(location, target):
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()


span = max(size.x + 3.5, size.y, size.z) * 1.15
for v in job["views"]:
    kind = v["camera"]
    ground.hide_render = v["mode"] == "silhouette"
    if player_obj:
        player_obj.hide_render = not v.get("player", True)
    if kind.startswith("ortho"):
        cam_data.type = "ORTHO"
        mid = Vector((center.x, center.y, (lo.z + hi.z) / 2))
        d = 60
        if kind == "ortho_front":
            look_at(mid + Vector((0, d, 0)), mid)
            cam_data.ortho_scale = max(size.x, size.z * aspect) * 1.18
        elif kind == "ortho_side":
            mid = Vector((center.x, center.y + 0.6, (lo.z + hi.z) / 2))
            look_at(mid + Vector((d, 0, 0)), mid)
            cam_data.ortho_scale = max(size.y + 1.5, size.z * aspect) * 1.18
        elif kind == "ortho_back":
            look_at(mid + Vector((0, -d, 0)), mid)
            cam_data.ortho_scale = max(size.x, size.z * aspect) * 1.18
        elif kind == "ortho_top":
            look_at(center + Vector((0, 0.0001, d)), center)
            cam_data.ortho_scale = max(size.x, size.y * aspect) * 1.18
    else:
        cam_data.type = "PERSP"
        cam_data.lens = v.get("lens", 32)
        yaw = math.radians(v.get("yaw", 35))
        dist = v.get("dist", span * 1.5)
        height = v.get("height", 1.62)
        tz = v.get("target_z", (lo.z + hi.z) / 2)
        loc = center + Vector((math.sin(yaw) * dist, math.cos(yaw) * dist, 0))
        loc.z = height
        look_at(loc, Vector((center.x, center.y, tz)))
    if v["mode"] == "silhouette":
        shading.light = "FLAT"
        shading.color_type = "OBJECT"
        obj.color = (0.03, 0.03, 0.04, 1)
        shading.show_object_outline = False
        shading.show_cavity = False
        shading.show_shadows = False
        shading.background_type = "VIEWPORT"
        world.color = (0.93, 0.92, 0.89)
        if player_obj:
            player_obj.color = (0.35, 0.5, 0.75, 1)
    else:
        shading.light = "STUDIO"
        shading.studio_light = v.get("studio", "basic.sl")
        shading.color_type = "MATERIAL" if v["mode"] == "flat" else "OBJECT"
        obj.color = (0.78, 0.76, 0.72, 1)
        if player_obj:
            player_obj.color = (0.42, 0.55, 0.72, 1)
        shading.show_cavity = True
        shading.cavity_type = "WORLD"
        shading.show_shadows = True
        shading.shadow_intensity = 0.45
        shading.show_object_outline = False
        shading.background_type = "VIEWPORT"
        world.color = tuple(job.get("sky", (0.16, 0.15, 0.19)))
    # optional see-through, so markers inside the model (pivots) show
    shading.show_xray = bool(v.get("xray"))
    shading.xray_alpha = v.get("xray", 1.0) or 1.0
    scene.display.light_direction = (-0.45, 0.35, 0.82)
    scene.render.filepath = f"{job['out']}/{v['name']}.png"
    bpy.ops.render.render(write_still=True)
print("RENDER_DONE", json.dumps({"size_blocks": [round(size.x, 2), round(size.y, 2), round(size.z, 2)]}))

"""Render a cuboid .bbmodel's actual per-face UVs and PNG atlas in Blender 3.6.

Usage: blender -b --factory-startup --python blender_texture_render.py -- job.json
"""
import json
import math
import sys

import bpy
from mathutils import Vector

job = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


FACE_UV = {
    "north": (0, -1, 1, -1), "south": (0, 1, 1, -1),
    "east": (2, -1, 1, -1), "west": (2, 1, 1, -1),
    "up": (0, 1, 2, 1), "down": (0, 1, 2, -1),
}


def to_blender(point):
    return Vector((point[0] / 16, -point[2] / 16, point[1] / 16))


QUADS = {
    "west": (0, 1, 3, 2), "east": (4, 6, 7, 5),
    "down": (0, 4, 5, 1), "up": (2, 3, 7, 6),
    "north": (0, 2, 6, 4), "south": (1, 5, 7, 3),
}

image = bpy.data.images.load(job["texture"], check_existing=True)
image.colorspace_settings.name = "sRGB"


def texture_material(name, emissive):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    if emissive:
        shader = nodes.new("ShaderNodeEmission")
        shader.inputs["Strength"].default_value = 1.2
        mat.node_tree.links.new(tex.outputs["Color"], shader.inputs["Color"])
    else:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Roughness"].default_value = 0.96
        shader.inputs["Metallic"].default_value = 0.05
        mat.node_tree.links.new(tex.outputs["Color"], shader.inputs["Base Color"])
        mat.node_tree.links.new(tex.outputs["Alpha"], shader.inputs["Alpha"])   # hair cards: cut-out texels
        mat.blend_method = "CLIP"
        mat.shadow_method = "CLIP"
    mat.node_tree.links.new(shader.outputs[0], output.inputs["Surface"])
    return mat


normal_mat = texture_material("Volley atlas - matte", False)
glow_mat = texture_material("Volley atlas - emissive", True)
verts, faces, face_mats, uv_faces = [], [], [], []
for cube in job["boxes"]:
    start = len(verts)
    verts += [to_blender(p) for p in cube["corners"]]
    lo, hi = cube["from"], cube["to"]
    local = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    for face_name, indices in QUADS.items():
        faces.append(tuple(start + i for i in indices))
        face_mats.append(1 if cube["glow"] else 0)
        u0, v0, u1, v1 = cube["uv"][face_name]["uv"]
        # Minecraft's face orientation (bosskit.bbmodel.FACE_UV), so the preview matches the game
        axis_u, sign_u, axis_v, sign_v = FACE_UV[face_name]
        this_uv = []
        for idx in indices:
            p = local[idx]
            du = (p[axis_u] - lo[axis_u]) / max(1e-9, hi[axis_u] - lo[axis_u])
            dv = (p[axis_v] - lo[axis_v]) / max(1e-9, hi[axis_v] - lo[axis_v])
            du = du if sign_u > 0 else 1 - du
            dv = dv if sign_v > 0 else 1 - dv
            this_uv.append(((u0 + du * (u1 - u0)) / image.size[0], 1 - (v0 + dv * (v1 - v0)) / image.size[1]))
        uv_faces.append(this_uv)

mesh = bpy.data.meshes.new("volley-textured-cuboids")
mesh.from_pydata(verts, [], faces)
mesh.update()
obj = bpy.data.objects.new("Volley - textured model geometry", mesh)
scene.collection.objects.link(obj)
mesh.materials.append(normal_mat)
mesh.materials.append(glow_mat)
uv_layer = mesh.uv_layers.new(name="UVMap")
for polygon, mat_idx, uv_coords in zip(mesh.polygons, face_mats, uv_faces):
    polygon.material_index = mat_idx
    for loop_idx, uv in zip(polygon.loop_indices, uv_coords):
        uv_layer.data[loop_idx].uv = uv

def plain_material(name, color, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = .92
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


ground_mat = plain_material("dark stone floor", (.16, .15, .18))
player_mat = plain_material("player scale - blue", (.22, .39, .62))
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.015))
ground = bpy.context.object
ground.name = "floor"
ground.data.materials.append(ground_mat)

# Simple 1.8-block figure for scale in the hero view.
player_bits = [((-4, 0, -2), (0, 12, 2)), ((0, 0, -2), (4, 12, 2)),
               ((-4, 12, -2), (4, 24, 2)), ((-8, 12, -2), (-4, 24, 2)),
               ((4, 12, -2), (8, 24, 2)), ((-4, 24, -4), (4, 32, 4))]
players = []
PLAYER_AT = job.get("player_at", (3.4, 1.2))   # where the scale figure stands, in blocks
for lower, upper in player_bits:
    center = [(lower[i] + upper[i]) / 2 * 1.8 / 32 for i in range(3)]
    size = [(upper[i] - lower[i]) * 1.8 / 32 for i in range(3)]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(PLAYER_AT[0] + center[0], PLAYER_AT[1] - center[2], center[1]))
    player = bpy.context.object
    player.name = "scale-player"
    player.dimensions = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    player.data.materials.append(player_mat)
    players.append(player)

world = bpy.data.worlds.new("dim studio")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (.10, .09, .13, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = .7


def area_light(name, location, power, size):
    data = bpy.data.lights.new(name, "AREA")
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = location
    data.energy = power
    data.shape = "DISK"
    data.size = size
    light.rotation_euler = (Vector((0, 0, 2.0)) - light.location).to_track_quat("-Z", "Y").to_euler()


area_light("warm front key", (-5, 6, 8), 1050, 7)
area_light("cool rim", (5, -5, 7), 650, 6)
area_light("front fill", (4, 8, 4), 480, 7)
camera_data = bpy.data.cameras.new("camera")
camera = bpy.data.objects.new("camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.use_gtao = True
scene.eevee.gtao_distance = 3
scene.eevee.gtao_factor = 1.1
scene.eevee.taa_render_samples = 96
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.camera.data.type = "ORTHO"


def render(name, location, target, scale, show_player, res=(1200, 900)):
    scene.render.resolution_x, scene.render.resolution_y = res
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.ortho_scale = scale
    for player in players:
        player.hide_render = not show_player
    scene.render.filepath = f"{job['out']}/{name}.png"
    bpy.ops.render.render(write_still=True)


# a job may name its own views: {"name", "location", "target", "scale", "player"} in Blender coordinates (blocks, Z up)
for v in job.get("views", [
        {"name": "textured_hero", "location": (6.5, 8.5, 6.8), "target": (0, .3, 2.0), "scale": 8.5, "player": True},
        {"name": "textured_front", "location": (0, 10, 3.4), "target": (0, 0, 2.15), "scale": 7.5, "player": False},
        {"name": "textured_player_eye", "location": (-3.4, 7.2, 1.62), "target": (0, 0, 2.25), "scale": 7.5,
         "player": False}]):
    render(v["name"], v["location"], v["target"], v["scale"], v["player"], tuple(v.get("res", (1200, 900))))
print("TEXTURED_RENDER_DONE")

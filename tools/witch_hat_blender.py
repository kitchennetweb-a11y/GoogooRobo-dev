# Googoo's Halloween witch hat: purple, bent tip, wide brim, orange band, gold buckle. Y-up in the game, brim centre at the origin, 1.0 across the brim.
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python tools/witch_hat_blender.py -- models/witch_hat.glb [preview.png]
import bpy, bmesh, math, sys
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)

def lin(h):
    c = [((h >> s) & 255) / 255 for s in (16, 8, 0)]
    return [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c] + [1]
def mat(name, hexcol, rough, metal=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(hexcol); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m
PURPLE, ORANGE, GOLD = mat('hat_purple', 0x6a3fb5, .55), mat('hat_band', 0xf07a1a, .5), mat('hat_buckle', 0xf2c230, .3, .8)

def obj(name, bm, m):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o

SEG = 48
def ring(bm, r, z, off=(0, 0)):
    return [bm.verts.new((off[0] + r * math.cos(a), off[1] + r * math.sin(a), z)) for a in (math.tau * i / SEG for i in range(SEG))]
def bridge(bm, a, b):
    for i in range(SEG): bm.faces.new((a[i], a[(i + 1) % SEG], b[(i + 1) % SEG], b[i]))

# brim: a soft disc, slightly curled up at the edge, with thickness
bm = bmesh.new()
prof = [(.18, .0), (.36, -.005), (.46, .01), (.5, .035), (.49, .045), (.45, .025), (.36, .02), (.18, .03)]
rings = [ring(bm, r, z) for r, z in prof]
for a, b in zip(rings, rings[1:]): bridge(bm, a, b)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); obj('brim', bm, PURPLE)

# cone: radius shrinks with height, the top third bends over to the side
bm = bmesh.new(); N = 24; rings = []
for i in range(N + 1):
    t = i / N; r = .2 * (1 - t) ** 1.15 + .004; h = .78 * t
    bend = max(0, t - .5) / .5; dx = .26 * bend ** 2; dz = -.12 * bend ** 3
    rings.append(ring(bm, r, .02 + h + dz, (dx, 0)))
for a, b in zip(rings, rings[1:]): bridge(bm, a, b)
tip = bm.verts.new((rings[-1][0].co.x - .004, 0, rings[-1][0].co.z + .01))
for i in range(SEG): bm.faces.new((rings[-1][i], rings[-1][(i + 1) % SEG], tip))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); obj('cone', bm, PURPLE)

# orange band round the base of the cone
bm = bmesh.new(); rr = [ring(bm, r, z) for r, z in ((.205, .03), (.212, .045), (.2, .1), (.188, .118))]
for a, b in zip(rr, rr[1:]): bridge(bm, a, b)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); obj('band', bm, ORANGE)

# gold buckle on the front (-Y in Blender = +z in the game): a square frame
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
bmesh.ops.scale(bm, vec=(.085, .02, .075), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, -.206, .074), verts=bm.verts)
o = obj('buckle', bm, GOLD)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
bmesh.ops.scale(bm, vec=(.045, .03, .038), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, -.212, .074), verts=bm.verts)
hole = obj('hole', bm, ORANGE)

bpy.ops.export_scene.gltf(filepath=args[0], export_format='GLB', export_apply=True, export_yup=True)
print('exported', args[0])
if len(args) > 1:
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 700; sc.render.filepath = args[1]
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .5, .55, 1)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.location = (.6, -2.2, .7); cam.rotation_euler = (math.radians(80), 0, math.radians(15))
    L = bpy.data.objects.new('l', bpy.data.lights.new('l', 'SUN')); L.data.energy = 4; L.rotation_euler = (.6, .3, .4); bpy.context.collection.objects.link(L)
    bpy.ops.render.render(write_still=True)

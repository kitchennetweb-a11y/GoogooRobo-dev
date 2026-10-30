# Clean rebuild of the Tripo launch rocket (proportions measured from the Tripo mesh, 2026-10-29): crisp bevelled parts,
# glossy plastic-coat materials, a bulged black glass window. 3.6 tall, y-up in the game (Blender Z-up here), front = -Y in Blender = +z in three.js.
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python tools/rocket_blender.py -- models/space_rocket.glb [preview.png]
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]
bpy.ops.wm.read_factory_settings(use_empty=True)

def lin(h):  # sRGB hex -> linear rgba
    c = [((h >> s) & 255) / 255 for s in (16, 8, 0)]
    return [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c] + [1]

def mat(name, hexcol, rough, coat=0., metal=0., emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(hexcol); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .15
    if emit: b.inputs['Emission Color'].default_value = lin(emit); b.inputs['Emission Strength'].default_value = 1.
    return m

WHITE = mat('rocket_white', 0xeeeae2, .32, coat=.6, metal=.1)
ORANGE = mat('rocket_orange', 0xd2501a, .36, coat=.5, metal=.05)
DARK = mat('rocket_throat', 0x2a1408, .7)
GLASS = mat('rocket_glass', 0x07080c, .05, coat=1.)
GLINT = mat('rocket_glint', 0xffffff, .5, emit=0xffffff)

def obj(name, bm, m, smooth=True, angle=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = smooth
    if angle is not None:
        bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle)); o.select_set(False)
    return o

def lathe(name, prof, m, seg=64):  # prof: [(radius, height)] bottom to top
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, y)) for r, y in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=seg, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(name, bm, m, angle=40)

def spline(pts, n=10):  # Catmull-Rom through pts (defined before use below)
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (Vector(P[j]) for j in (i - 1, i, i + 1, i + 2))
        for k in range(n):
            t = k / n; out.append(tuple(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    return out + [pts[-1]]

# body (measured radius per height, smoothed), closed underneath
BODY = [(.6, .55), (.69, .65), (.74, .8), (.772, 1.05), (.81, 1.4), (.832, 1.65), (.822, 1.9), (.79, 2.2), (.738, 2.5), (.66, 2.82), (.55, 3.05), (.42, 3.26), (.27, 3.45), (.12, 3.57), (0, 3.6)]
bp = spline(BODY, 8)
def r_at(y):
    for (r0, y0), (r1, y1) in zip(bp, bp[1:]):
        if y1 >= y: return r0 + (r1 - r0) * (y - y0) / ((y1 - y0) or 1)
    return 0
lathe('body', [(0, .5), (.4, .5), (.56, .53)] + bp, WHITE)
# orange bands: proud by .025 with square shoulders
def band(name, y0, y1, o=.025):
    p = [(r_at(y0) - .01, y0)] + [(r_at(y0 + (y1 - y0) * i / 10) + o, y0 + (y1 - y0) * i / 10) for i in range(11)] + [(r_at(y1) - .01, y1)]
    return lathe(name, p, ORANGE)
band('band_top', 2.72, 2.92); band('band_low', .64, .86)
# bell nozzle and its dark throat
lathe('nozzle', [(.2, .32), (.34, .2), (.4, .1), (.43, .06), (.38, .06), (.33, .14), (.27, .32), (.3, .45), (.42, .52)], ORANGE)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=.36)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, .09)); obj('throat', bm, DARK)
# four fins (measured outline: from the body at 1.3 high, out to 1.12 at 0.6, standing on the floor), bevelled crisp edges
FIN = spline([(.62, 1.32), (.95, 1.12), (1.07, .9), (1.12, .6), (1.1, .3), (1.05, 0)], 6) + spline([(.84, 0), (.8, .25), (.66, .45), (.5, .55)], 6)  # smooth outer and inner edges, flat foot
for i, a in enumerate((0, 90, 180, 270)):
    bm = bmesh.new(); t = .15
    top = [bm.verts.new((x, -t / 2, y)) for x, y in FIN]; bot = [bm.verts.new((x, t / 2, y)) for x, y in FIN]
    bm.faces.new(top); bm.faces.new(bot[::-1])
    for j in range(len(FIN)): bm.faces.new((top[j], top[(j + 1) % len(FIN)], bot[(j + 1) % len(FIN)], bot[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if e.calc_face_angle(0) > .5], offset=.025, segments=2, affect='EDGES', profile=.5)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(a - 90), 3, 'Z'))
    obj(f'fin{i}', bm, ORANGE, angle=35)
# porthole on the front (-Y): orange ring, bulged black glass, a small highlight
WY, R = 1.83, .33; wr = r_at(WY); z0 = wr - .02; capR = .48; ha = math.asin(R / capR)
bm = bmesh.new(); bmesh.ops.create_circle(bm, segments=8, radius=1)  # placeholder so bm is valid
bm.free()
def torus(name, R0, r0, m, arc=math.tau, seg=72, sides=20):
    bm = bmesh.new()
    rings = []
    for i in range(seg + (0 if arc == math.tau else 1)):
        u = arc * i / seg; c, s = math.cos(u), math.sin(u)
        rings.append([bm.verts.new(((R0 + r0 * math.cos(v)) * c, (R0 + r0 * math.cos(v)) * s, r0 * math.sin(v))) for v in (math.tau * k / sides for k in range(sides))])
    n = len(rings) if arc == math.tau else len(rings) - 1
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % len(rings)]
        for k in range(sides): bm.faces.new((a[k], b[k], b[(k + 1) % sides], a[(k + 1) % sides]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(name, bm, m)
ring = torus('window_ring', R + .02, .06, ORANGE, seg=48, sides=14); ring.rotation_euler = (math.pi / 2, 0, 0); ring.location = (0, -z0, WY)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=capR)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < capR * math.cos(ha) - 1e-4], context='VERTS')
glass = obj('window_glass', bm, GLASS); glass.rotation_euler = (math.pi / 2, 0, 0); glass.location = (0, -(z0 - capR * math.cos(ha)), WY)
gl = torus('window_glint', R * .6, .016, GLINT, arc=math.pi * .42, seg=16, sides=8); gl.rotation_euler = (math.pi / 2, -math.pi * .55, 0)  # highlight at the top left
gl.location = (0, -(z0 + (capR - capR * math.cos(ha)) * .8), WY)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_apply=True, export_yup=True)
print('exported', OUT)
if len(args) > 1:  # quick EEVEE preview
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 900; sc.render.filepath = args[1]
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.25, .27, .32, 1)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.location = (2.6, -6.8, 2.6); cam.rotation_euler = (math.radians(84), 0, math.radians(21))
    for loc, e in (((4, -5, 7), 900), ((-5, -3, 3), 300)):
        L = bpy.data.objects.new('l', bpy.data.lights.new('l', 'POINT')); L.data.energy = e; L.location = loc; bpy.context.collection.objects.link(L)
    bpy.ops.render.render(write_still=True)

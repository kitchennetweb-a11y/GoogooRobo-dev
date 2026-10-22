"""Build the preview screen + bezel variants into a NEW file and render the comparison set.
run: blender -b googoo_tripo_rig.blend --python build.py   (source file is never saved; result saved as a copy)"""
import sys, os, math, json, bpy, numpy as np, mathutils
SCR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SCR)
import studio
from mathutils.bvhtree import BVHTree
V = mathutils.Vector
OUT = r"C:\Users\ahmma\Downloads\Pash 3D\screen_preview"
BLEND = r"C:\Users\ahmma\Downloads\Pash 3D\screen_preview.blend"
os.makedirs(OUT, exist_ok=True)
P = json.load(open(os.path.join(SCR, "params.json")))

# ---------------------------------------------------------------- dimensions (metres, armature/world space; front = -Y)
ZC = P["zc"]
A_O, B_O, R_O = P["a_o"], P["b_o"], P["r_o"]          # bezel outer edge (front view half sizes)
W = P["w"]                                             # bezel front-face width
A_I, B_I, R_I = A_O - W, B_O - W, R_O - W              # bezel inner edge = visible screen
OV = P["ov"]                                           # screen tucks this far under the bezel lip
A_P, B_P, R_P = A_I + OV, B_I + OV, R_I + OV           # screen panel
BULGE = P["bulge"]; LIP = P["lip"]; RB = P["rb"]; BURY = P["bury"]; GAP = P["gap"]

arm = bpy.data.objects['Googoo_tripo_rig']; old = bpy.data.objects['Googoo_face_screen']
arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
bo = bpy.data.objects['Googoo_body'].evaluated_get(dg); bme = bo.to_mesh(); bme.calc_loop_triangles()
bverts = [bo.matrix_world @ v.co for v in bme.vertices]
bvh = BVHTree.FromPolygons(bverts, [tuple(t.vertices) for t in bme.loop_triangles])
def head_y(x, z):
    h = bvh.ray_cast(V((x, -1.0, z)), V((0, 1, 0)))
    return h[0].y if h[0] else None

# ---------------------------------------------------------------- screen panel: rounded-rect quad grid, CRT bulge, planar UV
def axis(half, R, n_c, n_m):
    m = half - R
    return list(np.linspace(-half, -m, n_c + 1)) + list(np.linspace(-m, m, n_m + 1)[1:-1]) + list(np.linspace(m, half, n_c + 1))
def to_rr(X, Z):
    mx, mz = A_P - R_P, B_P - R_P
    ax, az = abs(X), abs(Z)
    if ax > mx and az > mz:   # square corner cell -> quarter disc (elliptical grid mapping)
        s, t = (ax - mx) / R_P, (az - mz) / R_P
        ax, az = mx + R_P * s * math.sqrt(1 - t * t / 2), mz + R_P * t * math.sqrt(1 - s * s / 2)
    return math.copysign(ax, X), math.copysign(az, Z)
gx = axis(A_P, R_P, P.get("pc", 14), P.get("pmx", 40)); gz = axis(B_P, R_P, P.get("pc", 14), P.get("pmz", 20))
pts = [[to_rr(X, Z) for X in gx] for Z in gz]
bul = lambda x, z: BULGE * max(0, 1 - (x / A_P) ** 2) * max(0, 1 - (z / B_P) ** 2)
# edge-plane depth so the bulged panel clears the head everywhere by GAP
need = [head_y(x, z + ZC) - GAP + bul(x, z) for row in pts for (x, z) in row if head_y(x, z + ZC) is not None]
Y_E = min(need); Y_F = Y_E - LIP
print("Y_E", Y_E, "Y_F", Y_F)
nx = len(gx); verts = []; uvs = []
for row in pts:
    for (x, z) in row:
        verts.append((x, Y_E - bul(x, z), z + ZC)); uvs.append(((x + A_P) / (2 * A_P), (z + B_P) / (2 * B_P)))
faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(len(gz) - 1) for i in range(nx - 1)]

def mkobj(name, verts, faces, uvs=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if uvs:
        uvl = me.uv_layers.new(name="UVMap")
        for p in me.polygons:
            for li, vi in zip(p.loop_indices, p.vertices): uvl.data[li].uv = uvs[vi]
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    for c in old.users_collection: c.objects.link(o)
    o.parent = arm; o.matrix_parent_inverse = arm.matrix_world.inverted(); o.matrix_world = mathutils.Matrix.Identity(4)
    vg = o.vertex_groups.new(name='mixamorig:Head'); vg.add(list(range(len(verts))), 1.0, 'REPLACE')
    md = o.modifiers.new("Armature", 'ARMATURE'); md.object = arm
    return o
panel = mkobj("Googoo_screen_panel", verts, faces, uvs)
if panel.data.polygons[len(faces) // 2].normal.y > 0: panel.data.flip_normals()

# ---------------------------------------------------------------- bezel: profile swept along the inner rounded rect, outer wall buried in the head
cx, cz = A_I - R_I, B_I - R_I
path = []  # (centre_x, centre_z, nx, nz): point = centre + n*(R_I + d)
def straight(c0, c1, n, k):
    for t in np.linspace(0, 1, k + 1)[:-1]: path.append((c0[0] + (c1[0] - c0[0]) * t, c0[1] + (c1[1] - c0[1]) * t, n[0], n[1]))
def arc(c, a0, k):
    for t in np.linspace(0, 1, k + 1)[:-1]:
        a = math.radians(a0 + 90 * t); path.append((c[0], c[1], math.cos(a), math.sin(a)))
NA = P.get("na", 28)
straight((cx, -cz), (cx, cz), (1, 0), 14); arc((cx, cz), 0, NA)
straight((cx, cz), (-cx, cz), (0, 1), 32); arc((-cx, cz), 90, NA)
straight((-cx, cz), (-cx, -cz), (-1, 0), 14); arc((-cx, -cz), 180, NA)
straight((-cx, -cz), (cx, -cz), (0, -1), 32); arc((cx, -cz), 270, NA)
SEG = 6; e = 0.0003
prof = [(0, Y_E + 0.003), (0, Y_F + RB + e)]
prof += [(RB - RB * math.cos(math.radians(90 * k / SEG)), Y_F + RB - RB * math.sin(math.radians(90 * k / SEG))) for k in range(SEG + 1)]
prof += [(RB + e, Y_F), (W / 2, Y_F), (W - RB - e, Y_F)]
prof += [(W - RB + RB * math.sin(math.radians(90 * k / SEG)), Y_F + RB - RB * math.cos(math.radians(90 * k / SEG))) for k in range(SEG + 1)]
prof += [(W, Y_F + RB + e), (W, "mid"), (W, "back")]
bv = []; depth = []
for (ccx, ccz, nnx, nnz) in path:
    ox, oz = ccx + nnx * (R_I + W), ccz + nnz * (R_I + W)
    hy = head_y(ox, oz + ZC); yb = (hy if hy is not None else -0.08) + BURY
    depth.append(yb - BURY - Y_F)
    for d, y in prof:
        if y == "back": y = yb
        elif y == "mid": y = (Y_F + RB + e + yb) / 2
        bv.append((ccx + nnx * (R_I + d), y, ccz + nnz * (R_I + d) + ZC))
NP, NR = len(path), len(prof)
bf = [(k * NR + r, k * NR + r + 1, ((k + 1) % NP) * NR + r + 1, ((k + 1) % NP) * NR + r) for k in range(NP) for r in range(NR - 1)]
bez = mkobj("Googoo_screen_bezel", bv, bf)
fi = NR // 2   # a front-face quad on the first path sample
if bez.data.polygons[fi].normal.y > 0: bez.data.flip_normals()
print("bezel wall depth (front face -> head) min/max", round(min(depth), 4), round(max(depth), 4))

# ---------------------------------------------------------------- materials
img_tex = bpy.data.images['GooGoo-Robo_Tripo-rig_basecolor']
px = np.array(img_tex.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
R, G, B = px[:, 0], px[:, 1], px[:, 2]
cream = np.median(px[(R > .80) & (G > .72) & (B > .55) & (R - B > .08) & (R - B < .25)], 0)
navy = np.median(px[(B > .30) & (B - R > .22) & (G < B - .10) & (G < .5)], 0)
s2l = lambda c: [((v + .055) / 1.055) ** 2.4 if v > .04045 else v / 12.92 for v in c]
print("cream sRGB", (cream * 255).round(), "navy sRGB", (navy * 255).round())
def pbsdf(name, col, rough, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.05
    return m, b
def screen_mat(name, image):
    m, b = pbsdf(name, (0.003, 0.003, 0.004), 0.35, coat=1.0)
    b.inputs['Specular IOR Level'].default_value = 0.0   # the clear coat alone carries the glass reflection (stays black, not grey)
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = image; t.extension = 'EXTEND'
    m.node_tree.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.0
    return m
# new screen texture: front-view neutral composite cropped to the panel's front bbox (the drawing spans the old sheet's front bbox)
comp = bpy.data.images.load(os.path.join(SCR, "neutral_front.png")); cw, chh = comp.size
a = np.array(comp.pixels[:], dtype=np.float32).reshape(chh, cw, 4)   # row 0 = bottom
X0, X1, Z0, Z1 = P["draw_bbox"]; ppm = cw / (X1 - X0)
c0 = int(round((-A_P - X0) * ppm)); c1 = int(round((A_P - X0) * ppm))
r0 = int(round((ZC - B_P - Z0) * ppm)); r1 = int(round((ZC + B_P - Z0) * ppm))
pad = max(0, -r0, -c0, r1 - chh, c1 - cw)
ap = np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode='edge')[r0 + pad:r1 + pad, c0 + pad:c1 + pad]
crop = bpy.data.images.new("screen_neutral_front", ap.shape[1], ap.shape[0]); crop.pixels = ap.ravel(); crop.pack()
print("crop px", ap.shape, "pad", pad)
panel.data.materials.append(screen_mat("Screen_new", crop))
onscr = bpy.data.images.load(r"C:\Users\ahmma\Downloads\Pash 3D\face_kit\expressions_on_screen\neutral.png"); onscr.pack()
old.data.materials[0] = screen_mat("FaceScreen_preview", onscr)   # preview file only
head_rough = bpy.data.materials['tripo_mat_59f3fa7a-56bc-4308-9c3f-3852209d140a'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value
VARIANTS = {"cream": (s2l(cream), head_rough), "blue": (s2l(navy), 0.4), "grey": (s2l((0.23, 0.235, 0.25)), 0.45)}
bez.data.materials.append(None)
bezels = {}
for i, (k, (col, rough)) in enumerate(VARIANTS.items()):
    o = bez if i == 0 else bez.copy()   # linked duplicates share one mesh, material per object
    if i: [c.objects.link(o) for c in bez.users_collection]
    o.name = f"Googoo_screen_bezel_{k}"; o.material_slots[0].link = 'OBJECT'
    o.material_slots[0].material = pbsdf(f"Bezel_{k}", col, rough)[0]; bezels[k] = o

tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
print("POLY panel quads", len(panel.data.polygons), "tris", tris(panel), "| bezel quads", len(bez.data.polygons), "tris", tris(bez))
json.dump({"Y_E": Y_E, "Y_F": Y_F, "panel": [2 * A_P, 2 * B_P, R_P], "visible": [2 * A_I, 2 * B_I, R_I], "outer": [2 * A_O, 2 * B_O, R_O],
           "wall_depth": [min(depth), max(depth)], "panel_quads": len(panel.data.polygons), "bezel_quads": len(bez.data.polygons),
           "panel_verts": len(panel.data.vertices), "bezel_verts": len(bez.data.vertices), "head_rough": head_rough,
           "cream": (cream * 255).round().tolist(), "navy": (navy * 255).round().tolist()}, open(os.path.join(SCR, "built.json"), "w"), indent=1)

# ---------------------------------------------------------------- scene, cameras, save, render
sc = studio.setup(1600)
tgt = V((0, -0.1, 0.82))
def orbit(t, yaw, pitch, dist=2.0):
    y, p = math.radians(yaw), math.radians(pitch)
    return t + dist * V((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
corner = V((-(A_O - R_O) - (R_O - W / 2) * .7071, Y_F, ZC + (B_O - R_O) + (R_O - W / 2) * .7071))
edge = V((0, Y_F, ZC + B_O - W / 2))
cams = {"front": studio.cam("cam_front", (0, -2.0, 0.815), (0, 0, 0.815), lens=150),
        "34": studio.cam("cam_34", orbit(tgt, 35, 10), tgt, lens=150),
        "corner": studio.cam("cam_corner", orbit(corner, -22, 14), corner, lens=600),
        "edge": studio.cam("cam_edge", orbit(edge, 8, 16), edge, lens=600)}
arm.data.pose_position = 'POSE'
for o in bezels.values(): o.hide_render = o.hide_viewport = o.name != "Googoo_screen_bezel_cream"
old.hide_render = old.hide_viewport = True
sc.camera = cams["front"]
bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True)   # copy: writes the new file only
arm.data.pose_position = 'REST'
rows = {"current": None, "cream": "cream", "blue": "blue", "grey": "grey"}
only = os.environ.get("ONLY"); views = os.environ.get("VIEWS")
for row, var in rows.items():
    if only and row not in only.split(","): continue
    old.hide_render = var is not None; panel.hide_render = var is None
    for k, o in bezels.items(): o.hide_render = k != var
    for cn, c in cams.items():
        if views and cn not in views.split(","): continue
        studio.render(c, os.path.join(OUT, f"{row}_{cn}.png"))
if os.environ.get("POSECHECK"):   # skinning check: rotate the head bone, new parts must follow like the old sheet
    arm.data.pose_position = 'POSE'; pb = arm.pose.bones['mixamorig:Head']; pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (math.radians(15), math.radians(25), math.radians(10))
    old.hide_render = True; panel.hide_render = False
    for k, o in bezels.items(): o.hide_render = k != "cream"
    studio.render(cams["34"], os.path.join(SCR, "posecheck.png"))

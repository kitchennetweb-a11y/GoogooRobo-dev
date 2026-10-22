"""googoo_anims.blend (Googoo + 19 cleaned clips) -> googoo_anims_v2.blend / googoo_anims_v2.glb / googoo_v2_unity.fbx with the v2 screen:
body = Googoo_body_v2 from screen_preview_v2.blend (made by v2/build_v2.py: rounded opening, 1.5 mm lip, wall back to the LCD, cream-painted texture copy),
its lip ring thinned along the rim to about a third (profile rows kept = same silhouette and edge; the rest of the body untouched),
LCD = "Googoo_face_screen" (100% head; the game draws the face on it), the old face-screen sheet removed. Same armature, weights checked.
run: blender -b "Downloads/Pash 3D/googoo_anims.blend" --python tools/screen_v2/make_anims_v2.py   (sources are never saved; LIP_TOL env = rim tolerance, m)"""
import bpy, os, json, math, numpy as np, mathutils
from collections import defaultdict

P3D = "C:/Users/ahmma/Downloads/Pash 3D/"
SRC_V2 = P3D + "screen_preview_v2.blend"
OUT_BLEND, OUT_GLB, OUT_FBX = P3D + "googoo_anims_v2.blend", P3D + "googoo_anims_v2.glb", P3D + "googoo_v2_unity.fbx"
FBX_TEX = P3D + "googoo_v2_unity_basecolor.png"
LIP_TOL, LIP_ANG, LIP_SPAN = float(os.environ.get("LIP_TOL", "0.000025")), math.radians(3), 24  # rim: 0.025 mm off the old rows (corner arcs stay round, kinks < 3 deg)
HERE = os.path.dirname(os.path.abspath(__file__))
info = {}
arm = bpy.data.objects["Googoo_tripo_rig"]; body0 = bpy.data.objects["Googoo_body"]; face0 = bpy.data.objects["Googoo_face_screen"]
assert bpy.data.filepath.replace("\\", "/").endswith("Pash 3D/googoo_anims.blend")
CLIPS = sorted(a.name for a in bpy.data.actions); assert len(CLIPS) == 19, CLIPS

# ---------------------------------------------------------------- 1. v2 meshes (+ the preview's rig, only to compare rest poses)
with bpy.data.libraries.load(SRC_V2, link=False) as (src, dst):
    dst.meshes = ["Googoo_body_v2", "Googoo_screen_lcd"]; dst.objects = ["Googoo_tripo_rig"]
mb, ml = dst.meshes; parm = dst.objects[0]
d = max((parm.data.bones[b.name].matrix_local - b.matrix_local).to_quaternion().angle + (parm.data.bones[b.name].head_local - b.head_local).length for b in arm.data.bones)
dm = max(abs(x - y) for r1, r2 in zip(parm.matrix_world, arm.matrix_world) for x, y in zip(r1, r2))
info["rig_rest_diff"] = d + dm; print("rest pose difference preview rig vs anims rig:", d, dm); assert d + dm < 1e-5
pdata = parm.data; bpy.data.objects.remove(parm); bpy.data.armatures.remove(pdata)
for a in [a for a in bpy.data.actions if a.name not in CLIPS]: bpy.data.actions.remove(a)
# the v2 body keeps the old vertices: same rest positions as this file's body
kd = mathutils.kdtree.KDTree(len(body0.data.vertices))
for v in body0.data.vertices: kd.insert(v.co, v.index)
kd.balance()
far = [v.co for v in mb.vertices if abs(v.co.x) > 0.2 or abs(v.co.z - 0.815) > 0.15]
info["body_vert_diff"] = max(kd.find(c)[2] for c in far); print("v2 body vs old body (outside the face):", info["body_vert_diff"], len(far)); assert info["body_vert_diff"] < 1e-6


# ---------------------------------------------------------------- 2. lip ring: fewer points along the rim (rows 1..7), the top row (welded to the body) untouched
def reduce_lip(me):
    nP, nL = len(me.polygons), len(me.loops)
    size = np.zeros(nP, int); me.polygons.foreach_get("loop_total", size)
    start = np.zeros(nP, int); me.polygons.foreach_get("loop_start", start)
    lv = np.zeros(nL, int); me.loops.foreach_get("vertex_index", lv)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    uv = np.zeros(nL * 2); me.uv_layers["UVMap"].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    cn = np.zeros(nL * 3); me.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3)
    q0 = nP
    while size[q0 - 1] == 4: q0 -= 1
    assert (size[:q0] == 3).all() and q0 < nP  # build_v2 appends the lip quads after the triangles
    LF = np.array([lv[start[p]:start[p] + 4] for p in range(q0, nP)])
    other = set(lv[:start[q0]].tolist())
    ecount, adj = defaultdict(int), defaultdict(set)
    for f in LF:
        for k in range(4):
            a, b = int(f[k]), int(f[(k + 1) % 4]); ecount[(min(a, b), max(a, b))] += 1; adj[a].add(b); adj[b].add(a)
    badj = defaultdict(list)
    for (a, b), c in ecount.items():
        if c == 1: badj[a].append(b); badj[b].append(a)
    assert all(len(n) == 2 for n in badj.values())
    loops, seen = [], set()
    for s in badj:
        if s in seen: continue
        cyc, prev, cur = [s], s, badj[s][0]; seen.add(s)
        while cur != s: cyc.append(cur); seen.add(cur); prev, cur = cur, [n for n in badj[cur] if n != prev][0]
        loops.append(cyc)
    assert len(loops) == 2, len(loops)
    top = max(loops, key=lambda c: len(set(c) & other)); NR = len(top)
    row = {v: 0 for v in top}; fr = top
    while fr:
        nx = []
        for v in fr:
            for n in adj[v]:
                if n not in row: row[n] = row[v] + 1; nx.append(n)
        fr = nx
    NROW = max(row.values()) + 1
    G = np.zeros((NR, NROW), int); G[:, 0] = top
    for j in range(1, NROW):
        for i in range(NR):
            c = [n for n in adj[G[i, j - 1]] if row[n] == j]; assert len(c) == 1; G[i, j] = c[0]
    ij = {int(G[i, j]): (i, j) for i in range(NR) for j in range(NROW)}
    assert len(ij) == len(row) == NR * NROW
    # per segment s (ring s -> s+1): uv / normal at both ends per row; the winding of the original quads
    UV = np.zeros((NR, 2, 2)); NN = np.zeros((NR, 2, NROW, 3)); fwd = set()
    for p in range(q0, nP):
        L = range(start[p], start[p] + 4); c = [ij[int(lv[l])] for l in L]
        ri = {i for i, _ in c}; s = max(ri) if (max(ri) - min(ri)) > 1 else min(ri)  # wrap-around segment NR-1 -> 0
        for l, (i, j) in zip(L, c):
            e = 0 if i == s else 1; UV[s, e] = uv[l]; NN[s, e, j] = cn[l]
        k = [n for n in range(4) if c[n][0] == s and c[n][1] == min(jj for _, jj in c)][0]
        fwd.add(c[(k + 1) % 4] == (s, c[k][1] + 1))
    assert len(fwd) == 1; fwd = fwd.pop()
    P = co[G]                                                            # (NR, NROW, 3)
    jump = np.array([np.abs(UV[(i - 1) % NR, 1] - UV[i, 0]).max() for i in range(NR)]); print("uv jumps (texture px)", np.sort(jump)[-12:] * 2048)
    seam = jump > 2e-3  # > 4 texels: a real UV seam (smaller = extrapolated lift at the ring points)
    cosA = math.cos(LIP_ANG)
    KR = list(range(0, NROW - 1, 2)) + [NROW - 1]  # profile rows kept: bevel 6 -> 3 segments (<= 0.06 mm off the round), the wall as it was

    def ok(a, b):  # can rows 1.. skip every ring point strictly between a and b (indices unwrapped)?
        for ii in range(a + 1, b):
            i = ii % NR
            if seam[i]: return False
            for j in KR[1:]:
                A, Bp, X = P[a % NR, j], P[b % NR, j], P[i, j]; D = Bp - A
                t = np.clip((X - A) @ D / (D @ D), 0, 1)
                if np.linalg.norm(A + t * D - X) > LIP_TOL: return False
                n = (1 - t) * NN[a % NR, 0, j] + t * NN[(b - 1) % NR, 1, j]; n /= np.linalg.norm(n)
                if n @ NN[i, 0, j] < cosA: return False
        return True
    s0 = next((i for i in range(NR) if seam[i]), 0)
    S, a = [s0], s0
    while True:
        b = a + 1
        while b + 1 - a <= LIP_SPAN and b + 1 <= s0 + NR and ok(a, b + 1): b += 1
        if b >= s0 + NR: break
        S.append(b); a = b
    spans = [(S[k], S[k + 1] if k + 1 < len(S) else s0 + NR) for k in range(len(S))]
    # new lip faces: (verts, uvs, normals) in the original quads' winding
    faces = []
    m = lambda i: i % NR
    def put(cs):  # cs = [(vertex, uv, normal)] in the forward winding
        faces.append(cs if fwd else cs[::-1])
    for a, b in spans:
        left = lambda j: (int(G[m(a), j]), UV[m(a), 0], NN[m(a), 0, j]); right = lambda j: (int(G[m(b), j]), UV[m(b - 1), 1], NN[m(b - 1), 1, j])
        for j0, j1 in zip(KR[1:-1], KR[2:]): put([left(j0), left(j1), right(j1), right(j0)])
        h = a + (b - a + 1) // 2
        for i in range(a, b):  # zipper: every top point kept, fanned to the next row's two ends
            X = left(KR[1]) if i < h else right(KR[1])
            put([(int(G[m(i + 1), 0]), UV[m(i), 1], NN[m(i), 1, 0]), (int(G[m(i), 0]), UV[m(i), 0], NN[m(i), 0, 0]), X])
        top_h = (int(G[m(h), 0]), UV[m(h - 1), 1], NN[m(h - 1), 1, 0]) if h == b else (int(G[m(h), 0]), UV[m(h), 0], NN[m(h), 0, 0])
        put([top_h, left(KR[1]), right(KR[1])])
    # rebuild the mesh: the body's triangles as they were + the new lip faces; unused ring points dropped
    old_f = [lv[start[p]:start[p] + 3].tolist() for p in range(q0)]
    used = sorted({v for f in old_f for v in f} | {c[0] for f in faces for c in f}); vmap = {v: k for k, v in enumerate(used)}
    m3 = bpy.data.meshes.new("Googoo_body_v2")
    m3.from_pydata(co[used].tolist(), [], [[vmap[v] for v in f] for f in old_f] + [[vmap[c[0]] for c in f] for f in faces]); m3.update()
    nl = start[q0]
    cuv = np.vstack([uv[:nl], np.array([c[1] for f in faces for c in f])]); cnn = np.vstack([cn[:nl], np.array([c[2] for f in faces for c in f])])
    m3.uv_layers.new(name="UVMap").data.foreach_set("uv", cuv.ravel())
    for p in m3.polygons: p.use_smooth = True
    m3.normals_split_custom_set([tuple(n / np.linalg.norm(n)) for n in cnn])
    m3.materials.append(me.materials[0])
    lip_new = sorted(vmap[v] for v in G[:, 0].tolist() + [int(G[m(a), j]) for a, _ in spans for j in KR[1:]])
    tri = lambda mm: sum(len(p.vertices) - 2 for p in mm.polygons)
    info.update(lip_ring_points=NR, lip_rows=NROW, lip_rows_kept=KR, lip_kept=len(S), lip_tris_old=2 * (nP - q0), lip_tris_new=sum(len(f) - 2 for f in faces),
                body_tris_v2=tri(me), body_tris_new=tri(m3), lip_seams=int(sum(seam)), lip_fwd=fwd)
    print("lip:", {k: v for k, v in info.items() if k.startswith(("lip", "body_tris"))})
    return m3, used, lip_new


m3, used, lip_idx = reduce_lip(mb)
# vertex weights from the v2 mesh (its old vertices kept the body's weights; every new one is 100% head)
names = [g.name for g in bpy.data.objects.new("_tmp", mb).vertex_groups]; bpy.data.objects.remove(bpy.data.objects["_tmp"])
W = [[(names[g.group], g.weight) for g in mb.vertices[v].groups] for v in used]


def new_obj(name, me, like):
    o = bpy.data.objects.new(name, me)
    for c in like.users_collection: c.objects.link(o)
    o.parent = arm; o.matrix_parent_inverse = like.matrix_parent_inverse.copy(); o.matrix_world = like.matrix_world.copy()
    lm = like.modifiers["Armature"] if "Armature" in like.modifiers else [m for m in like.modifiers if m.type == "ARMATURE"][0]
    mo = o.modifiers.new("Armature", "ARMATURE"); mo.object = arm
    for k in ("use_vertex_groups", "use_bone_envelopes", "use_deform_preserve_volume", "use_multi_modifier"): setattr(mo, k, getattr(lm, k))
    return o


# swap: old body + old face sheet out (their meshes, the old material and texture too)
oldmat = body0.data.materials[0]; oldimg = [n.image for n in oldmat.node_tree.nodes if n.type == "TEX_IMAGE"]
facemat = face0.data.materials[0]
lcd_mats = list(ml.materials)
body0.name, face0.name = "_old_body", "_old_face"  # free the names (the game finds "Googoo_face_screen")
body = new_obj("Googoo_body", m3, body0); lcd = new_obj("Googoo_face_screen", ml, body0)
assert body.name == "Googoo_body" and lcd.name == "Googoo_face_screen"
vg ={nm: body.vertex_groups.new(name=nm) for nm in names}
by = defaultdict(list)
for k, ws in enumerate(W):
    for nm, w in ws: by[(nm, round(w, 7))].append(k)
for (nm, w), ids in by.items(): vg[nm].add(ids, w, "REPLACE")
assert [g.name for g in lcd.vertex_groups] == ["mixamorig:Head"], [g.name for g in lcd.vertex_groups]
ml.materials.clear(); ml.materials.append(facemat)  # plain, as the old sheet: the game / Unity draw the face
for o in (body0, face0):
    me = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
bpy.data.meshes.remove(mb); m3.name = "Googoo_body_v2"
for mt in lcd_mats:
    ims = [n.image for n in mt.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]; bpy.data.materials.remove(mt)
    for im in ims:
        if im.users == 0: bpy.data.images.remove(im)
bpy.data.materials.remove(oldmat)
for im in oldimg:
    if im and im.users == 0: bpy.data.images.remove(im)
body.data.materials[0].name = "Googoo_body_v2"

# ---------------------------------------------------------------- 3. skin weights: every vertex sums to 1; lip ring, opening rim and LCD 100% head
def wcheck(o, must_head=()):
    gi = {g.index: g.name for g in o.vertex_groups}; bad, worst, nohead = 0, 0.0, 0
    for v in o.data.vertices:
        s = sum(g.weight for g in v.groups); worst = max(worst, abs(s - 1)); bad += abs(s - 1) > 1e-4
    for k in must_head:
        gs = [(gi[g.group], g.weight) for g in o.data.vertices[k].groups if g.weight > 1e-6]
        nohead += not (len(gs) == 1 and gs[0][0] == "mixamorig:Head" and abs(gs[0][1] - 1) < 1e-6)
    return dict(verts=len(o.data.vertices), sum_off=bad, worst=worst, not_full_head=nohead)
rim = [v.index for v in body.data.vertices if abs(v.co.x) < 0.16 and abs(v.co.z - 0.815) < 0.115 and v.co.y < -0.08]  # everything inside / at the opening
info["weights_body"] = wcheck(body, sorted(set(lip_idx) | set(rim))); info["weights_lcd"] = wcheck(lcd, range(len(lcd.data.vertices)))
info["rim_verts"] = len(rim); print("weights", info["weights_body"], info["weights_lcd"])
assert info["weights_body"]["sum_off"] == 0 and info["weights_lcd"]["sum_off"] == 0
assert info["weights_body"]["not_full_head"] == 0 and info["weights_lcd"]["not_full_head"] == 0
info["tris_total_old"] = 32603 + 1536; info["lcd_tris"] = sum(len(p.vertices) - 2 for p in lcd.data.polygons)
info["tris_total_new"] = info["body_tris_new"] + info["lcd_tris"]

# ---------------------------------------------------------------- 4. save + GLB (as tools/anim/export.py (a))
for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
arm.animation_data_clear(); ad = arm.animation_data_create(); ad.action = bpy.data.actions["idle_happy"]; ad.action_slot = ad.action.slots[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=True)
bpy.ops.object.select_all(action="DESELECT")
for o in (arm, body, lcd): o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format="GLB", use_selection=True,
                          export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
                          export_frame_step=1, export_anim_single_armature=True, export_reset_pose_bones=True,
                          export_optimize_animation_size=True, export_image_format="JPEG", export_jpeg_quality=92, export_yup=True)

# ---------------------------------------------------------------- 5. Unity FBX: armature + body + LCD, no clips (they are mixamo/clean_fbx/*.fbx), texture alongside
arm.animation_data_clear()
img = [n.image for n in body.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"][0]
img.save(filepath=FBX_TEX); fimg = bpy.data.images.load(FBX_TEX)
[n for n in body.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"][0].image = fimg
bpy.ops.export_scene.fbx(filepath=OUT_FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, bake_anim=False,
                         add_leaf_bones=False, apply_scale_options="FBX_SCALE_UNITS", armature_nodetype="NULL",
                         primary_bone_axis="Y", secondary_bone_axis="X", path_mode="RELATIVE", embed_textures=False)
info["sizes"] = {os.path.basename(p): os.path.getsize(p) for p in (OUT_BLEND, OUT_GLB, OUT_FBX, FBX_TEX)}
json.dump(info, open(os.path.join(HERE, "made_anims_v2.json"), "w"), indent=1, default=float)
print("DONE", json.dumps(info, default=float))

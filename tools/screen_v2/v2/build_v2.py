"""v2 screen preview: cut a recessed rounded-rect opening into a COPY of the body, cream lip, curved LCD inside.
run: blender -b screen_preview.blend --python build_v2.py   (input never saved; result saved as screen_preview_v2.blend)"""
import sys, os, math, json, bpy, numpy as np, mathutils
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.abspath(__file__)); OLD = os.path.join(os.path.dirname(HERE), "scr")
sys.path.insert(0, OLD); import studio
V = mathutils.Vector
OUT = r"C:\Users\ahmma\Downloads\Pash 3D\screen_preview"
BLEND = r"C:\Users\ahmma\Downloads\Pash 3D\screen_preview_v2.blend"
P = json.load(open(os.path.join(HERE, "params_v2.json")))
A, B, R, ZC = P["a"], P["b"], P["r"], P["zc"]       # opening (wall line), front-view half sizes
RB, DREC, OV, BACK = P["rb"], P["d"], P["ov"], P["back"]
AC, BC, RC = A + RB, B + RB, R + RB                 # surface cut line (lip starts here)
info = {}

# ------------------------------------------------------------------ scene cleanup (v1 bezels/panel out)
for n in [o.name for o in bpy.data.objects if o.name.startswith(("Googoo_screen_bezel", "Googoo_screen_panel"))]:
    bpy.data.objects.remove(bpy.data.objects[n])
for m in [m for m in bpy.data.materials if m.name.startswith("Bezel_")]: bpy.data.materials.remove(m)
arm = bpy.data.objects['Googoo_tripo_rig']; arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
body = bpy.data.objects['Googoo_body']; me = body.data; old = bpy.data.objects['Googoo_face_screen']
assert body.matrix_world == mathutils.Matrix.Identity(4)

# ------------------------------------------------------------------ outline helpers (x, z) plane, front view
def rr_poly(a, b, r, narc=64, step=0.004):
    pts = []; cx, cz = a - r, b - r
    def line(p0, p1):
        p0, p1 = np.array(p0), np.array(p1); n = max(1, int(math.ceil(np.linalg.norm(p1 - p0) / step)))
        for k in range(n): pts.append(p0 + (p1 - p0) * k / n)
    def arc(c, a0):
        for k in range(narc):
            t = math.radians(a0 + 90 * k / narc); pts.append(np.array(c) + r * np.array((math.cos(t), math.sin(t))))
    line((a, -cz), (a, cz)); arc((cx, cz), 0); line((cx, b), (-cx, b)); arc((-cx, cz), 90)
    line((-a, cz), (-a, -cz)); arc((-cx, -cz), 180); line((-cx, -b), (cx, -b)); arc((cx, -cz), 270)
    return np.array(pts) + [0, ZC]
def rr_sdf(p, a, b, r):
    q = np.abs(np.atleast_2d(p) - [0, ZC]) - [a - r, b - r]
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.maximum(q[:, 0], q[:, 1]), 0) - r
def rr_n(p, a, b, r):
    x, z = p[0], p[1] - ZC; qx, qz = abs(x) - (a - r), abs(z) - (b - r)
    if qx > 0 and qz > 0: n = np.array((qx, qz)) / math.hypot(qx, qz)
    elif qx > qz: n = np.array((1.0, 0.0))
    else: n = np.array((0.0, 1.0))
    return n * [math.copysign(1, x), math.copysign(1, z)]
CP = rr_poly(AC, BC, RC); NCP = len(CP)          # CCW cut polygon

# ------------------------------------------------------------------ body arrays
nv, nt = len(me.vertices), len(me.polygons)
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.zeros(nt * 3, int); me.loops.foreach_get('vertex_index', lv); TV = lv.reshape(-1, 3)
uvd = np.zeros(nt * 6); me.uv_layers['UVMap'].data.foreach_get('uv', uvd); TUV = uvd.reshape(-1, 3, 2)
cn = np.array([c.vector[:] for c in me.corner_normals]).reshape(-1, 3, 3)
TP = co[TV]                                       # (nt,3,3)
gn = np.cross(TP[:, 1] - TP[:, 0], TP[:, 2] - TP[:, 0]); gn /= np.linalg.norm(gn, axis=1, keepdims=True) + 1e-30
cen = TP.mean(1)
front = (gn[:, 1] < -0.25) & (cen[:, 1] < -0.09) & (np.abs(cen[:, 0]) < AC + 0.05) & (np.abs(cen[:, 2] - ZC) < BC + 0.05)
FT = np.where(front)[0]; print("front candidate tris", len(FT))
headg = body.vertex_groups['mixamorig:Head'].index
def head_full(vi): return any(g.group == headg and g.weight > 0.999 for g in me.vertices[vi].groups)

# BVH of the original body for ray casts (rest pose == raw coords, checked 1.8e-7)
bvh = BVHTree.FromPolygons([V(p) for p in co], [tuple(t) for t in TV])
def head_hit(x, z):
    h = bvh.ray_cast(V((x, -1.0, z)), V((0, 1, 0))); return h

# ------------------------------------------------------------------ 2D clipping
def clip(poly, a, b, keep_left=True):
    """Sutherland-Hodgman against line a->b; keep left side (inside of CCW polygon) or right side."""
    d = b - a
    def side(p): s = d[0] * (p[1] - a[1]) - d[1] * (p[0] - a[0]); return s if keep_left else -s
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]; sp, sq = side(p), side(q)
        if sp >= 0: out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq); out.append(p + (q - p) * t)
    return out
def area(poly):
    if len(poly) < 3: return 0.0
    p = np.array(poly); return 0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
def bary(p, t2):
    a, b, c = t2; v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01; v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    return np.array((1 - v - w, v, w))

T2 = TP[:, :, [0, 2]]
new_v, new_f, new_uv, new_n = [], [], [], []      # new geometry (positions, faces as vert idx, per-corner uv / normal)
dele = set(); clipped = []
for ti in FT:
    t2 = T2[ti]; ins = rr_sdf(t2, AC, BC, RC) < 0
    if ins.all(): dele.add(ti); continue
    poly = [p for p in t2]
    inter = poly
    for i in range(NCP):
        inter = clip(inter, CP[i], CP[(i + 1) % NCP], True)
        if len(inter) < 3: break
    if area(inter) < 1e-12: continue               # disjoint from cut region: untouched
    assert all(head_full(v) for v in TV[ti]), "clipped tri not 100% head"
    dele.add(ti); clipped.append(ti)
    rest = poly
    for i in range(NCP):
        a, b = CP[i], CP[(i + 1) % NCP]
        out = clip(rest, a, b, False)
        if area(out) > 1e-13:
            base = len(new_v)
            for p in out:
                w = bary(p, t2); new_v.append(w @ TP[ti]); new_uv.append(w @ TUV[ti])
                nn = w @ cn[ti]; new_n.append(nn / np.linalg.norm(nn))
            for k in range(1, len(out) - 1): new_f.append((base, base + k, base + k + 1))
        rest = clip(rest, a, b, True)
        if area(rest) < 1e-13: break
print("deleted tris", len(dele), "clipped", len(clipped), "new piece tris", len(new_f))
info["tris_removed_inside"] = len(dele) - len(clipped); info["tris_clipped"] = len(clipped); info["piece_tris"] = len(new_f)
NPIECE_V = len(new_v)

# ------------------------------------------------------------------ ring along the cut line (C vertices + crossings with triangle edges)
cum = np.r_[0, np.cumsum(np.linalg.norm(np.roll(CP, -1, 0) - CP, axis=1))]
ring = [(float(i), CP[i]) for i in range(NCP)]
for ti in clipped:
    t2 = T2[ti]
    for e in range(3):
        p, q = t2[e], t2[(e + 1) % 3]; d = q - p
        A0 = CP; B0 = np.roll(CP, -1, 0); E = B0 - A0
        den = d[0] * E[:, 1] - d[1] * E[:, 0]
        ok = np.abs(den) > 1e-15
        w = A0 - p
        s = np.where(ok, (w[:, 0] * E[:, 1] - w[:, 1] * E[:, 0]) / np.where(ok, den, 1), -1)
        u = np.where(ok, (w[:, 0] * d[1] - w[:, 1] * d[0]) / np.where(ok, den, 1), -1)
        for i in np.where(ok & (s >= 0) & (s <= 1) & (u >= 0) & (u < 1))[0]:
            ring.append((i + float(u[i]), p + d * s[i]))
ring.sort(key=lambda r: r[0])
rr = [ring[0]]
for r in ring[1:]:
    if np.linalg.norm(r[1] - rr[-1][1]) > 2e-6: rr.append(r)
if np.linalg.norm(rr[-1][1] - rr[0][1]) < 2e-6: rr.pop()
ring = rr; NR = len(ring); print("ring points", NR)

# triangle lookup in 2D (clipped tris + their front neighbours)
cand = [ti for ti in FT]
def find_tri(p, prefer=None):
    best, bw = None, -1e9
    for ti in cand:
        t2 = T2[ti]
        if p[0] < t2[:, 0].min() - 1e-4 or p[0] > t2[:, 0].max() + 1e-4 or p[1] < t2[:, 1].min() - 1e-4 or p[1] > t2[:, 1].max() + 1e-4: continue
        w = bary(p, t2); m = w.min()
        if m > bw: best, bw = ti, m
    return best, bw
def lift(p, ti):
    w = bary(p, T2[ti]); nn = w @ cn[ti]
    return w @ TP[ti], w @ TUV[ti], nn / np.linalg.norm(nn)

# per ring point: surface point P0, extrapolated corner Q, bevel/wall
rpts = []
for par, p in ring:
    ti, bw = find_tri(p + rr_n(p, AC, BC, RC) * 2e-5); assert bw > -1e-3, ("no tri for ring pt", p, bw)
    P0, uv0, n0 = lift(p, ti)
    n2 = rr_n(p, AC, BC, RC)
    pi_, po = p + n2 * 0.0005, p + n2 * 0.0025
    dy = (head_hit(pi_[0], pi_[1])[0].y - head_hit(po[0], po[1])[0].y) / 0.002   # skin slope moving inward, measured just outside the cut
    dy = float(np.clip(dy, -P["dy_clip"], P["dy_clip"]))
    rpts.append(dict(p=p, n2=n2, P0=P0, dy=dy, ti=ti))
DY = np.array([r["dy"] for r in rpts]); DYs = sum(np.roll(DY, k) for k in range(-5, 6)) / 11
for r, d in zip(rpts, DYs):
    r["dy"] = d; r["Q"] = r["P0"] + np.array((-r["n2"][0], d, -r["n2"][1])) * RB
info["lip_slope_range"] = [float(DYs.min()), float(DYs.max())]; print("lip slope dy range", DYs.min(), DYs.max())

# ------------------------------------------------------------------ LCD surface fit: y = c0 + (Rc - sqrt(Rc^2 - x^2)) + t*z + q*z^2   (z rel. ZC)
QX = np.array([r["Q"][0] for r in rpts]); QZ = np.array([r["Q"][2] for r in rpts]) - ZC; QY = np.array([r["Q"][1] for r in rpts])
best = None
for Rc in np.linspace(0.20, 2.0, 91):
    gx = Rc - np.sqrt(Rc * Rc - QX ** 2)
    for t in np.linspace(-0.20, 0.20, 81):
        for q in np.linspace(0, P["qmax"], 6):
            g = gx + t * QZ + q * QZ ** 2; c0 = np.max(QY + DREC - g); dep = c0 + g - QY
            sc = np.mean(dep ** 2)
            if best is None or sc < best[0]: best = (sc, Rc, t, q, c0)
_, Rc, TT, QQ, C0 = best
if "force" in P: Rc, TT, QQ = P["force"]; C0 = np.max(QY + DREC - (Rc - np.sqrt(Rc * Rc - QX ** 2) + TT * QZ + QQ * QZ ** 2))
def lcd_y(x, z): zr = z - ZC; return C0 + Rc - math.sqrt(Rc * Rc - x * x) + TT * zr + QQ * zr * zr
dep = np.array([lcd_y(r["Q"][0], r["Q"][2]) - r["Q"][1] for r in rpts])
info.update(lcd_Rc=Rc, lcd_tilt=TT, lcd_q=QQ, lcd_c0=C0, recess_min=dep.min(), recess_max=dep.max(), recess_mean=dep.mean(),
            lcd_sag_h=lcd_y(A, ZC) - lcd_y(0, ZC), lcd_sag_v=QQ * B * B, head_sag_h=float(head_hit(A, ZC)[0].y - head_hit(0, ZC)[0].y))
print("LCD fit", {k: round(float(v), 4) for k, v in info.items() if k.startswith(("lcd", "recess", "head"))})

# ------------------------------------------------------------------ hidden inner shell inside the opening (would poke out in front of the LCD): delete
FTs = set(FT.tolist()); inner_del = []
reg = (np.abs(cen[:, 0]) < AC + 0.02) & (np.abs(cen[:, 2] - ZC) < BC + 0.02) & (cen[:, 1] < -0.05)
# barycentric sample grid (works for edge-on triangles too, whose front projection has no area)
_g = np.array([(i / 12, j / 12) for i in range(13) for j in range(13 - i)]); BW = np.c_[1 - _g.sum(1), _g]
for ti in np.where(reg)[0]:
    if ti in FTs: continue
    S = BW @ TP[ti]; ins = rr_sdf(S[:, [0, 2]], AC, BC, RC) < 0
    if not ins.any(): continue
    if all(S[k, 1] > lcd_y(S[k, 0], S[k, 2]) + BACK + 0.004 for k in np.where(ins)[0]): continue
    inner_del.append(ti)   # inset step walls / inner shell of the old painted screen: all of it goes
dele.update(inner_del)
info["inner_tris_removed"] = len(inner_del)
print("inner hidden tris removed", len(inner_del), "normal y mean", gn[inner_del, 1].mean() if inner_del else None)

# ------------------------------------------------------------------ bevel + wall profile vertices
NBEV = 6
prof_pos, prof_nrm = [], []
for r in rpts:
    P0, Q, n2 = r["P0"], r["Q"], r["n2"]
    L = RB * math.sqrt(1 + r["dy"] ** 2)
    W0 = Q + np.array((0, L, 0))
    yb = lcd_y(Q[0], Q[2]) + BACK
    assert yb > W0[1] + 2e-4, ("wall too short", yb - W0[1])
    pts, nrs = [], []
    nwall = np.array((-n2[0], 0, -n2[1]))
    t0 = Q - P0; t0 /= np.linalg.norm(t0)
    for k in range(NBEV + 1):
        u = k / NBEV
        pos = (1 - u) ** 2 * P0 + 2 * u * (1 - u) * Q + u * u * W0
        tan = 2 * (1 - u) * (Q - P0) + 2 * u * (W0 - Q); tan /= np.linalg.norm(tan)
        # geometric normal: in the plane (inward dir, y), perpendicular to tangent, facing the viewer/opening
        side = np.cross(tan, np.array((n2[1], 0, -n2[0])))  # rim tangent x profile tangent
        side /= np.linalg.norm(side)
        if side @ np.array((-n2[0], -1, -n2[1])) < 0: side = -side
        pts.append(pos); nrs.append(side)
    nrs[-1] = nwall
    # blend top normal into the surface's smooth normal for a seamless join (per-face overrides later)
    pts.append(np.array((Q[0], yb, Q[2]))); nrs.append(nwall)
    prof_pos.append(pts); prof_nrm.append(nrs)
NPR = NBEV + 2
info["bevel_leg_mm"] = RB * 1000

# assemble lip/wall quads (new verts appended after pieces)
base = len(new_v)
for i in range(NR):
    for j in range(NPR): new_v.append(prof_pos[i][j])
lipf, lipuv, lipn = [], [], []
for i in range(NR):
    k = (i + 1) % NR
    mid = (ring[i][1] + ring[k][1]) / 2; nm = rr_n(mid, AC, BC, RC)
    ti, bw = find_tri(mid + nm * 2e-5)
    uvi = lift(ring[i][1], ti)[1]; uvk = lift(ring[k][1], ti)[1]
    ni_s = lift(ring[i][1], ti)[2]; nk_s = lift(ring[k][1], ti)[2]
    for j in range(NPR - 1):
        f = (base + i * NPR + j, base + i * NPR + j + 1, base + k * NPR + j + 1, base + k * NPR + j)
        lipf.append(f); lipuv.append((uvi, uvi, uvk, uvk))
        def nn(ii, jj, ns):
            v = prof_nrm[ii][jj]
            if jj <= 2:  # ease from the surface normal into the bevel over the first segments
                w = jj / 3.0; v = (1 - w) * ns + w * v; v = v / np.linalg.norm(v)
            return v
        lipn.append((nn(i, j, ni_s), nn(i, j + 1, ni_s), nn(k, j + 1, nk_s), nn(k, j, nk_s)))
# orientation: first lip face normal should face forward/inward
f0 = lipf[0]; pa, pb, pc = (np.array(new_v[v]) for v in f0[:3]); fnorm = np.cross(pb - pa, pc - pa)
if fnorm @ prof_nrm[0][1] < 0:
    lipf = [f[::-1] for f in lipf]; lipuv = [u[::-1] for u in lipuv]; lipn = [n[::-1] for n in lipn]
print("lip quads", len(lipf))
info["lip_quads"] = len(lipf)

# weld lip top ring to clipped-piece boundary verts (exact same positions, avoids hairline cracks)
kd = KDTree(NPIECE_V)
for i in range(NPIECE_V): kd.insert(new_v[i], i)
kd.balance()
remap = {}; maxd = 0; welded = 0
for i in range(NR):
    vi = base + i * NPR
    hit = kd.find(new_v[vi])
    maxd = max(maxd, hit[2])
    if hit[2] < 2e-6: remap[vi] = hit[1]; welded += 1
print("ring->piece weld", welded, "/", NR, "max dist", maxd)
info["ring_weld"] = (welded, NR, maxd)

# ------------------------------------------------------------------ build the new body mesh
keep = np.array([ti for ti in range(nt) if ti not in dele])
NV0 = nv
all_v = np.vstack([co, np.array(new_v)])
faces = [tuple(TV[ti]) for ti in keep]
faces += [tuple(v + NV0 for v in f) for f in new_f]
faces += [tuple((remap.get(v, v)) + NV0 for v in f) for f in lipf]
corner_uv = [TUV[ti][c] for ti in keep for c in range(3)] + [new_uv[v] for f in new_f for v in f] + [u for fu in lipuv for u in fu]
corner_n = [cn[ti][c] for ti in keep for c in range(3)] + [new_n[v] for f in new_f for v in f] + [n for fn in lipn for n in fn]
used = sorted({v for f in faces for v in f}); vmap = {v: i for i, v in enumerate(used)}
faces = [tuple(vmap[v] for v in f) for f in faces]
m2 = bpy.data.meshes.new("Googoo_body_v2"); m2.from_pydata(all_v[used].tolist(), [], faces); m2.update()
uvl = m2.uv_layers.new(name="UVMap"); uvl.data.foreach_set('uv', np.array(corner_uv).ravel())
for p in m2.polygons: p.use_smooth = True
m2.normals_split_custom_set([tuple(n) for n in corner_n])
b2 = body.copy(); b2.data = m2; b2.name = "Googoo_body_v2"
for c in body.users_collection: c.objects.link(b2)
# weights: original verts copy theirs; all new verts are in the 100%-head region
b2.vertex_groups.clear()
vgs = {g.index: b2.vertex_groups.new(name=g.name) for g in body.vertex_groups}
inv = {}
for newi, oldi in enumerate(used):
    if oldi < NV0:
        for g in me.vertices[oldi].groups: inv.setdefault((g.group, round(g.weight, 6)), []).append(newi)
    else: inv.setdefault((headg, 1.0), []).append(newi)
for (gi, w), ids in inv.items(): vgs[gi].add(ids, w, 'REPLACE')
tri_old = nt; tri_new = sum(len(p.vertices) - 2 for p in m2.polygons)
info.update(tris_old=tri_old, tris_new=tri_new, verts_old=nv, verts_new=len(m2.vertices))
print("body tris", tri_old, "->", tri_new)

# ------------------------------------------------------------------ texture copy: paint out the black screen + soft edge around the opening
mat = me.materials[0]; tex = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE'][0].image
W_, H_ = tex.size; px = np.array(tex.pixels[:], np.float32).reshape(H_, W_, 4)
orig_px = px.copy()
FULL, BLEND_TO, SAMP = P["paint_full"], P["paint_blend"], P["paint_sample"]
sel_tris = [ti for ti in FT if rr_sdf(T2[ti], A, B, R).min() < SAMP[1]]
tex_s, tex_th, tex_ij = [], [], []
for ti in sel_tris:
    uvp = TUV[ti] * [W_, H_] - 0.5
    i0, i1 = int(np.floor(uvp[:, 0].min())) - 1, int(np.ceil(uvp[:, 0].max())) + 1
    j0, j1 = int(np.floor(uvp[:, 1].min())) - 1, int(np.ceil(uvp[:, 1].max())) + 1
    I, J = np.meshgrid(np.arange(max(i0, 0), min(i1, W_ - 1) + 1), np.arange(max(j0, 0), min(j1, H_ - 1) + 1))
    pts = np.c_[I.ravel(), J.ravel()].astype(float)
    a, b_, c = uvp; v0, v1 = b_ - a, c - a; v2 = pts - a
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-9: continue
    wv = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den; ww = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den; wu = 1 - wv - ww
    tol = 1.2 / max(np.linalg.norm(v0), np.linalg.norm(v1), 1)   # ~1 texel dilation against bilinear/mip bleed
    ok = (wu > -tol) & (wv > -tol) & (ww > -tol)
    Wb = np.c_[wu, wv, ww][ok]; xyz = Wb @ TP[ti]
    s = rr_sdf(xyz[:, [0, 2]], A, B, R)
    th = np.arctan2((xyz[:, 2] - ZC) / B, xyz[:, 0] / A)
    tex_s.append(s); tex_th.append(th); tex_ij.append(pts[ok].astype(int))
tex_s = np.concatenate(tex_s); tex_th = np.concatenate(tex_th); tex_ij = np.concatenate(tex_ij)
cols = orig_px[tex_ij[:, 1], tex_ij[:, 0], :3]
NB = 120; bins = ((tex_th + math.pi) / (2 * math.pi) * NB).astype(int) % NB
ring_sel = (tex_s > SAMP[0]) & (tex_s < SAMP[1])
rc = np.zeros((NB, 3)); cnt = np.zeros(NB)
np.add.at(rc, bins[ring_sel], cols[ring_sel]); np.add.at(cnt, bins[ring_sel], 1)
for _ in range(NB):                                   # fill empty bins from neighbours
    e = cnt == 0
    if not e.any(): break
    rc[e] = (np.roll(rc, 1, 0) + np.roll(rc, -1, 0))[e]; cnt[e] = (np.roll(cnt, 1) + np.roll(cnt, -1))[e]
rc /= cnt[:, None]
K = np.array([1, 2, 3, 2, 1], float); K /= K.sum()
for _ in range(3): rc = sum(np.roll(rc, k - 2, 0) * K[k] for k in range(5))
tgt = rc[bins]
wgt = np.clip((BLEND_TO - tex_s) / (BLEND_TO - FULL), 0, 1); wgt = wgt * wgt * (3 - 2 * wgt)
newc = cols * (1 - wgt[:, None]) + tgt * wgt[:, None]
px[tex_ij[:, 1], tex_ij[:, 0], :3] = newc
tex2 = bpy.data.images.new("GooGoo_basecolor_v2_screencut", W_, H_, alpha=True)
tex2.colorspace_settings.name = tex.colorspace_settings.name
tex2.pixels.foreach_set(px.ravel()); tex2.pack()
mat2 = mat.copy(); mat2.name = "tripo_mat_v2_screencut"
[n for n in mat2.node_tree.nodes if n.type == 'TEX_IMAGE'][0].image = tex2
m2.materials.append(mat2)
info["texels_changed"] = int((wgt > 0).sum()); info["cream_ring_sRGB_mean"] = (rc.mean(0) * 255).round().tolist()
print("texels painted", info["texels_changed"])

# ------------------------------------------------------------------ curved LCD panel
AP, BP, RP = A + OV, B + OV, R + OV
def axis(half, r, n_c, n_m):
    m = half - r
    return list(np.linspace(-half, -m, n_c + 1)) + list(np.linspace(-m, m, n_m + 1)[1:-1]) + list(np.linspace(m, half, n_c + 1))
def to_rr(X, Z):
    mx, mz = AP - RP, BP - RP; ax, az = abs(X), abs(Z)
    if ax > mx and az > mz:
        s, t = (ax - mx) / RP, (az - mz) / RP
        ax, az = mx + RP * s * math.sqrt(1 - t * t / 2), mz + RP * t * math.sqrt(1 - s * s / 2)
    return math.copysign(ax, X), math.copysign(az, Z)
gx = axis(AP, RP, 14, 40); gz = axis(BP, RP, 14, 20)
pts = [[to_rr(X, Z) for X in gx] for Z in gz]; nx = len(gx)
pv, puv = [], []
for row in pts:
    for (x, z) in row:
        pv.append((x, lcd_y(x, z + ZC), z + ZC)); puv.append(((x + AP) / (2 * AP), (z + BP) / (2 * BP)))
pf = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(len(gz) - 1) for i in range(nx - 1)]
pm = bpy.data.meshes.new("Googoo_screen_lcd"); pm.from_pydata(pv, [], pf); pm.update()
ul = pm.uv_layers.new(name="UVMap")
for p in pm.polygons:
    p.use_smooth = True
    for li, vi in zip(p.loop_indices, p.vertices): ul.data[li].uv = puv[vi]
if pm.polygons[len(pf) // 2].normal.y > 0: pm.flip_normals()
lcd = bpy.data.objects.new("Googoo_screen_lcd", pm)
for c in old.users_collection: c.objects.link(lcd)
lcd.parent = arm; lcd.matrix_parent_inverse = arm.matrix_world.inverted(); lcd.matrix_world = mathutils.Matrix.Identity(4)
lcd.vertex_groups.new(name='mixamorig:Head').add(list(range(len(pv))), 1.0, 'REPLACE')
lcd.modifiers.new("Armature", 'ARMATURE').object = arm
# face-kit front composite cropped to the panel's front bbox (same mapping as v1)
comp = bpy.data.images.load(os.path.join(OLD, "neutral_front.png")); cw, chh = comp.size
a = np.array(comp.pixels[:], np.float32).reshape(chh, cw, 4)
X0, X1, Z0, Z1 = json.load(open(os.path.join(OLD, "params.json")))["draw_bbox"]; ppm = cw / (X1 - X0)
c0 = int(round((-AP - X0) * ppm)); c1 = int(round((AP - X0) * ppm)); r0 = int(round((ZC - BP - Z0) * ppm)); r1 = int(round((ZC + BP - Z0) * ppm))
pad = max(0, -r0, -c0, r1 - chh, c1 - cw)
ap = np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode='edge')[r0 + pad:r1 + pad, c0 + pad:c1 + pad]
crop = bpy.data.images.new("screen_neutral_front_v2", ap.shape[1], ap.shape[0]); crop.pixels = ap.ravel(); crop.pack()
smat = bpy.data.materials['Screen_new'].copy(); smat.name = "Screen_v2_lcd"
[n for n in smat.node_tree.nodes if n.type == 'TEX_IMAGE'][0].image = crop
smat.node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = P["coat_rough"]   # curved glass: softer sun streak
pm.materials.append(smat)
info["lcd_tris"] = sum(len(p.vertices) - 2 for p in pm.polygons); info["lcd_size"] = [2 * AP, 2 * BP, RP]

# ------------------------------------------------------------------ checks: nothing of the body in front of the LCD inside the opening
bvh2 = BVHTree.FromObject(b2, bpy.context.evaluated_depsgraph_get())
bad = 0; tot = 0
for x in np.linspace(-A + 0.001, A - 0.001, 120):
    for z in np.linspace(-B + 0.001, B - 0.001, 80):
        if rr_sdf(np.array([[x, z + ZC]]), A, B, R)[0] > -0.0005: continue
        tot += 1; h = bvh2.ray_cast(V((x, -1, z + ZC)), V((0, 1, 0)))
        if h[0] is not None and h[0].y < lcd_y(x, z + ZC): bad += 1
info["rays_blocked_in_opening"] = (bad, tot); print("body hits in front of LCD inside opening:", bad, "/", tot)
# second-surface check: anything of the ORIGINAL body behind the front skin but in front of the LCD (inner shells)?
inner = 0
for x in np.linspace(-A + 0.002, A - 0.002, 40):
    for z in np.linspace(-B + 0.002, B - 0.002, 30):
        h = bvh.ray_cast(V((x, -1, z + ZC)), V((0, 1, 0)))
        if h[0] is None: continue
        h2 = bvh.ray_cast(h[0] + V((0, 1e-4, 0)), V((0, 1, 0)))
        if h2[0] is not None and h2[0].y < lcd_y(x, z + ZC) + 0.001: inner += 1
info["inner_surface_hits"] = inner; print("inner-shell hits before LCD:", inner)

json.dump({k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in info.items()}, open(os.path.join(HERE, "built_v2.json"), "w"), indent=1, default=float)

# ------------------------------------------------------------------ cameras + save + render
sc = studio.setup(1600)
tgt = V((0, -0.1, 0.82))
def orbit(t, yaw, pitch, dist=2.0):
    y, p = math.radians(yaw), math.radians(pitch)
    return t + dist * V((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
cx = -(A - R) - R * .7071; cz = ZC + (B - R) + R * .7071
corner = V((cx, head_hit(cx, cz)[0].y, cz)); edge = V((0, head_hit(0, ZC + B)[0].y, ZC + B))
cams = {"front": studio.cam("cam_front", (0, -2.0, 0.815), (0, 0, 0.815), lens=150),
        "34": studio.cam("cam_34", orbit(tgt, 35, 10), tgt, lens=150),
        "side": studio.cam("cam_side", orbit(V((0, -0.06, 0.815)), 90, 0), V((0, -0.06, 0.815)), lens=150),
        "corner": studio.cam("cam_corner_v2", orbit(corner, -22, 14), corner, lens=600),
        "edge": studio.cam("cam_edge_v2", orbit(edge, 8, 16), edge, lens=600),
        "up": studio.cam("cam_up", orbit(tgt, -25, -18), tgt, lens=150),
        "down": studio.cam("cam_down", orbit(tgt, 20, 30), tgt, lens=150)}
for n in ("cam_corner", "cam_edge"):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
def show(v2):
    body.hide_render = body.hide_viewport = v2; old.hide_render = old.hide_viewport = v2
    b2.hide_render = b2.hide_viewport = not v2; lcd.hide_render = lcd.hide_viewport = not v2
show(True); arm.data.pose_position = 'POSE'; sc.camera = cams["front"]
bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True)
arm.data.pose_position = 'REST'
views = os.environ.get("VIEWS", "front,34,side,corner,edge").split(","); rows = os.environ.get("ROWS", "current,v2").split(",")
for row in rows:
    show(row == "v2")
    for cn_ in views:
        studio.render(cams[cn_], os.path.join(OUT, f"v2cmp_{'new' if row == 'v2' else 'current'}_{cn_}.png"))
if os.environ.get("POSECHECK"):
    show(True); arm.data.pose_position = 'POSE'; pb = arm.pose.bones['mixamorig:Head']; pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (math.radians(15), math.radians(25), math.radians(10))
    studio.render(cams["34"], os.path.join(HERE, "posecheck_v2.png"))

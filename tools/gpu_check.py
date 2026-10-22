"""Offline GPU budget check for GLB props (see docs/gpu-budget.md).

  python tools/gpu_check.py "C:/Users/ahmma/Downloads/Pash 3D/props" assets/googoo/googoo.glb
  python tools/gpu_check.py --selftest

Folders are scanned non-recursively (so props/raw, props/old, props/optimized are skipped).
Class (S/M/L) comes from the "S small / M medium / L large" column in docs/tripo-props.md,
else from the model's longest side; files named googoo* are the hero (H).
Prints a markdown table; exits 1 if any file breaks a hard budget (tris, texture side, texture MB).
"""
import json, re, struct, sys, pathlib, base64, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
# class: (max tris, max texture side px, max texture GPU MB as loaded)
BUDGET = {"S": (3000, 512, 1.5), "M": (8000, 1024, 4.5), "L": (15000, 1024, 4.5), "H": (40000, 2048, 24.0)}
MIPS = 4 / 3

def table_classes():
    out, doc = {}, ROOT / "docs/tripo-props.md"
    if doc.exists():
        for line in doc.read_text(encoding="utf-8").splitlines():
            f, c = re.search(r"`([\w]+\.glb)`", line), re.search(r"\b([SML]) (?:small|medium|large)\b", line)
            if f and c: out.setdefault(f.group(1), c.group(1))
    return out

def read_glb(b):
    n = struct.unpack_from("<I", b, 12)[0]
    g = json.loads(b[20:20 + n])
    rest = b[20 + n:]
    binc = rest[8:8 + struct.unpack_from("<I", rest, 0)[0]] if len(rest) >= 8 else b""
    return g, binc

def image_info(data):
    """-> (width, height, format) from the first bytes of a PNG/JPEG/WebP/KTX2 file."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return (*struct.unpack(">II", data[16:24]), "png")
    if data[:12] == b"\xabKTX 20\xbb\r\n\x1a\n":
        w, h = struct.unpack_from("<II", data, 20)
        return w, h, "ktx2-etc1s" if struct.unpack_from("<I", data, 44)[0] == 1 else "ktx2-uastc"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        k = data[12:16]
        if k == b"VP8 ": return struct.unpack_from("<H", data, 26)[0] & 0x3FFF, struct.unpack_from("<H", data, 28)[0] & 0x3FFF, "webp"
        if k == b"VP8L":
            v = int.from_bytes(data[21:25], "little"); return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1, "webp"
        if k == b"VP8X": return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1, "webp"
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF: i += 1; continue
            m = data[i + 1]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack_from(">HH", data, i + 5); return w, h, "jpeg"
            i += 2 + struct.unpack_from(">H", data, i + 2)[0]
    return 0, 0, "?"

def image_bytes(g, binc, img, base):
    if "bufferView" in img:
        bv = g["bufferViews"][img["bufferView"]]; o = bv.get("byteOffset", 0)
        return binc[o:o + bv["byteLength"]]
    uri = img.get("uri", "")
    if uri.startswith("data:"): return base64.b64decode(uri.split(",", 1)[1])
    p = base / uri
    return p.read_bytes() if p.exists() else b""

def tri_count(g, prim):
    mode = prim.get("mode", 4)
    n = g["accessors"][prim["indices"]]["count"] if "indices" in prim else g["accessors"][prim["attributes"]["POSITION"]]["count"]
    return n // 3 if mode == 4 else max(n - 2, 0) if mode in (5, 6) else 0

def check(path, classes):
    g, binc = read_glb(path.read_bytes())
    # walk the scene so meshes used by several nodes count every time (that's what the GPU draws)
    # ponytail: only node scale is applied to the bbox (Tripo/resize_props roots are unrotated); add full TRS if rotated roots show up
    tris = verts = draws = 0; lo, hi = [1e9] * 3, [-1e9] * 3
    def walk(i, s):
        nonlocal tris, verts, draws
        n = g["nodes"][i]; s = [a * b for a, b in zip(s, n.get("scale", [1, 1, 1]))]
        if "mesh" in n:
            for p in g["meshes"][n["mesh"]]["primitives"]:
                a = g["accessors"][p["attributes"]["POSITION"]]
                tris += tri_count(g, p); verts += a["count"]; draws += 1
                if "min" in a:
                    for k in range(3):
                        lo[k] = min(lo[k], a["min"][k] * s[k]); hi[k] = max(hi[k], a["max"][k] * s[k])
        for c in n.get("children", []): walk(c, s)
    for sc in g.get("scenes", [])[:1]:
        for i in sc["nodes"]: walk(i, [1, 1, 1])
    if not draws: return None  # animation-only file
    size = max(h - l for h, l in zip(hi, lo))
    name = path.name
    cls = "H" if name.lower().startswith("googoo") else classes.get(name) or ("S" if size < 0.5 else "M" if size < 1.2 else "L")
    used = {m.get("name", "?") for m in g.get("materials", [])}
    texs, dims, mb_now, mb_ktx, side = [], [], 0.0, 0.0, 0
    for t in g.get("textures", []):
        src = t.get("extensions", {}).get("KHR_texture_basisu", {}).get("source", t.get("extensions", {}).get("EXT_texture_webp", {}).get("source", t.get("source")))
        if src is None: continue
        w, h, fmt = image_info(image_bytes(g, binc, g["images"][src], path.parent))
        bpp = 1 if fmt.startswith("ktx2") else 4  # KTX2 -> ASTC 4x4 / ETC2 ~1 B/px; everything else decodes to RGBA8
        mb_now += w * h * bpp * MIPS / 2**20; mb_ktx += w * h * MIPS / 2**20; side = max(side, w, h); dims += [w, h]
        texs.append(f"{w}{'' if w == h else 'x%d' % h} {fmt}")
    mt, mpx, mmb = BUDGET[cls]
    hard = [f"tris {tris} > {mt}"] * (tris > mt) + [f"texture {side}px > {mpx}"] * (side > mpx) + [f"tex {mb_now:.1f}MB > {mmb}"] * (mb_now > mmb)
    soft = [f"{len(used)} materials"] * (len(used) > (2 if cls == "H" else 1)) + [f"{draws} draws"] * (draws > (3 if cls == "H" else 2))
    soft += ["NPOT texture"] * any(v & (v - 1) for v in dims)
    return dict(file=name, cls=cls, size=size, tris=tris, verts=verts, mats=len(used), draws=draws, texs=texs,
                mb_now=mb_now, mb_ktx=mb_ktx, kb=path.stat().st_size / 1024, hard=hard, soft=soft)

def main(args):
    classes, files = table_classes(), []
    for a in args:
        p = pathlib.Path(a)
        files += sorted(p.glob("*.glb")) if p.is_dir() else [p]
    rows = [r for r in (check(f, classes) for f in files) if r]
    print("| file | class | size m | tris (max) | verts | mats | draws | textures | tex MB loaded | tex MB as KTX2 | file KB | result |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        res = ("**OVER: " + "; ".join(r["hard"]) + "**") if r["hard"] else "ok"
        if r["soft"]: res += " (warn: " + ", ".join(r["soft"]) + ")"
        print(f"| {r['file']} | {r['cls']} | {r['size']:.2f} | {r['tris']:,} ({BUDGET[r['cls']][0] // 1000}k) | {r['verts']:,} | {r['mats']} | {r['draws']} | "
              f"{', '.join(r['texs']) or '-'} | {r['mb_now']:.1f} | {r['mb_ktx']:.1f} | {r['kb']:.0f} | {res} |")
    if rows:
        s = lambda k: sum(r[k] for r in rows)
        print(f"| **total {len(rows)}** | | | {s('tris'):,} | {s('verts'):,} | | {s('draws')} | | {s('mb_now'):.1f} | {s('mb_ktx'):.1f} | {s('kb'):.0f} | "
              f"{sum(bool(r['hard']) for r in rows)} over |")
    return 1 if any(r["hard"] for r in rows) else 0

def selftest():
    import tempfile
    png = lambda w, h: b"\x89PNG\r\n\x1a\n" + struct.pack(">I4sII", 13, b"IHDR", w, h) + b"\x08\x06\x00\x00\x00" + b"\0" * 4
    assert image_info(png(512, 256))[:2] == (512, 256)
    jpg = b"\xff\xd8\xff\xe0\x00\x04ab\xff\xc0\x00\x11\x08\x01\x00\x02\x00" + b"\0" * 12
    assert image_info(jpg) == (512, 256, "jpeg")
    pos = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    img = png(1024, 1024); binc = pos + img + b"\0" * (-len(img) % 4)
    g = {"asset": {"version": "2.0"}, "scenes": [{"nodes": [0]}], "nodes": [{"children": [1, 2]}, {"mesh": 0}, {"mesh": 0}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}], "materials": [{"name": "m"}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]}],
         "bufferViews": [{"buffer": 0, "byteLength": 36}, {"buffer": 0, "byteOffset": 36, "byteLength": len(img)}],
         "images": [{"bufferView": 1, "mimeType": "image/png"}], "textures": [{"source": 0}], "buffers": [{"byteLength": len(binc)}]}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    body = struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binc), 0x004E4942) + binc
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d, "toy_test.glb"); p.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
        r = check(p, {"toy_test.glb": "S"})
    assert (r["tris"], r["draws"], r["mats"]) == (2, 2, 1), r          # mesh used by 2 nodes = 2 draws
    assert abs(r["mb_now"] - 1024 * 1024 * 4 * MIPS / 2**20) < 1e-6   # 1024 RGBA8 + mips = 5.33 MB
    assert any("1024px > 512" in h for h in r["hard"]) and any("MB > 1.5" in h for h in r["hard"])
    print("selftest ok")

if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest()
    else: sys.exit(main(sys.argv[1:] or [str(ROOT / "models")]))

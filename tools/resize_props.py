"""Scale Tripo GLBs to real-world size (Tripo normalises every model to ~1 unit).

Reads each prop's real size (e.g. 1.9x1.0x0.9 m) from docs/tripo-props.md, finds the model's
largest side and wraps the scene in one uniformly scaled root node. Originals stay in raw/.

  python tools/resize_props.py ["C:/Users/ahmma/Downloads/Pash 3D/props"]
Drop new Tripo exports into props/raw/, run this, and the sized copies land in props/.
"""
import json, re, struct, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ahmma\Downloads\Pash 3D\props")

def sizes():
    # table rows: | `file.glb` | ... | 1.9x1.0x0.9 | ...  -> {file: longest side in metres}
    out = {}
    for line in (ROOT / "docs/tripo-props.md").read_text(encoding="utf-8").splitlines():
        f, d = re.search(r"`([\w]+\.glb)`", line), re.search(r"\|\s*([\d.]+(?:x[\d.]+){2})\s*\|", line)
        if f and d: out.setdefault(f.group(1), max(map(float, d.group(1).split("x"))))
    return out

def read_glb(b):
    _, _, total = struct.unpack_from("<4sII", b)
    n, _ = struct.unpack_from("<II", b, 12)
    return json.loads(b[20:20 + n]), b[20 + n:total]  # rest = BIN chunk incl. its header

def write_glb(gltf, rest):
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    body = struct.pack("<II", len(js), 0x4E4F534A) + js + rest
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body

def longest_side(g):
    # POSITION accessors carry min/max; node transforms from Tripo are ~identity, so this is close enough
    lo, hi = [1e9] * 3, [-1e9] * 3
    for m in g["meshes"]:
        for p in m["primitives"]:
            a = g["accessors"][p["attributes"]["POSITION"]]
            lo = [min(x, y) for x, y in zip(lo, a["min"])]; hi = [max(x, y) for x, y in zip(hi, a["max"])]
    return max(h - l for h, l in zip(hi, lo))

def resize(src, dst, target):
    g, rest = read_glb(src.read_bytes())
    s = round(target / longest_side(g), 4)
    for sc in g["scenes"]:
        g["nodes"].append({"name": "real_size", "scale": [s, s, s], "children": sc["nodes"]})
        sc["nodes"] = [len(g["nodes"]) - 1]
    dst.write_bytes(write_glb(g, rest))
    return s

def main():
    raw, want = PROPS / "raw", sizes()
    raw.mkdir(exist_ok=True)
    for f in PROPS.glob("*.glb"):  # first run: move Tripo originals aside
        if not (raw / f.name).exists(): f.rename(raw / f.name)
    for f in sorted(raw.glob("*.glb")):
        if f.name not in want: print(f"skip {f.name}: no size in tripo-props.md"); continue
        s = resize(f, PROPS / f.name, want[f.name])
        g, _ = read_glb((PROPS / f.name).read_bytes())
        assert g["nodes"][g["scenes"][0]["nodes"][0]]["scale"] == [s, s, s]  # self-check: round-trips
        print(f"{f.name}: longest side -> {want[f.name]} m (x{s})")

if __name__ == "__main__":
    main()

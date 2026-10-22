"""Optimize sized props to the GPU budget (docs/gpu-budget.md) with glTF-Transform. Sources are never touched.

  python tools/optimize_props.py ["C:/Users/ahmma/Downloads/Pash 3D/props"] [--out DIR] [--webp|--ktx2] [--meshopt] [--verify] [--only NAME ...]

Per file: dedup, prune, lossless weld, flatten/join (NO simplify/decimation, all vertex attributes kept), resize textures
to the class max (S 512, M/L 1024), then KTX2 (UASTC for normal/ORM data maps, ETC1S for colour; needs
`toktx` from KTX-Software on PATH) or, without toktx, WebP at HALF that size (WebP still decodes to RGBA8
on the GPU, so half size is what keeps it inside the same texture-MB budget). --meshopt adds
EXT_meshopt_compression (web: needs MeshoptDecoder; positions get quantized).
Default output: <src>/optimized/. --verify renders before|after in three.js r128 (headless Chromium,
GLTFLoader + KTX2Loader r128, real GPU via tools/browser.py; GOOGOO_SWIFTSHADER=1 for CPU) from 3 angles into <out>/_verify/*.png
(top row before, bottom after) and flags any prop whose silhouette or colour moved beyond compression noise.
"""
import argparse, pathlib, shutil, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gpu_check import BUDGET, check, table_classes

NODE = shutil.which("node")
NPX = [NODE, str(pathlib.Path(NODE).parent / "node_modules/npm/bin/npx-cli.js"), "-y", "@gltf-transform/cli@4"]  # node + npx-cli.js: no .cmd quoting trouble with spaces in paths

def gt(*args):
    r = subprocess.run(NPX + [str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode: raise RuntimeError(f"gltf-transform {args[0]} failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")

def optimize(src, dst, cls, ktx2, meshopt):
    # never reshape: no simplify; weld in gltf-transform v4 is exact-match only (lossless); keep every vertex attribute
    side = BUDGET[cls][1] if ktx2 else BUDGET[cls][1] // 2
    with tempfile.TemporaryDirectory() as d:
        a, b = pathlib.Path(d, "a.glb"), pathlib.Path(d, "b.glb")
        gt("optimize", src, a if ktx2 else dst, "--compress", "meshopt" if meshopt else "false",
           "--texture-compress", "false" if ktx2 else "webp", "--texture-size", side, "--palette", "false",
           "--simplify", "false", "--prune-attributes", "false", "--instance", "false")
        if ktx2:
            gt("uastc", a, b, "--slots", "{normalTexture,metallicRoughnessTexture,occlusionTexture}", "--level", 2, "--zstd", 18)
            gt("etc1s", b, dst, "--slots", "{baseColorTexture,emissiveTexture}", "--quality", 160)

PAGE = """<!doctype html><meta charset=utf-8><style>body{margin:0;background:#fff}canvas{display:block;float:left}div{width:840px}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/libs/meshopt_decoder.js"></script>
<script type="importmap">{"imports":{"three":"./three-global.js"}}</script>
<div id=v></div>
<script type="module">
import {KTX2Loader} from 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/loaders/KTX2Loader.js';
// 2 rows (before, after) x 3 angles; magenta clear colour so the silhouette can be measured
const views=[0,1,2,3,4,5].map(()=>{const r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});r.setSize(280,280);r.setClearColor(0xff00ff);
  r.outputEncoding=THREE.sRGBEncoding;r.toneMapping=THREE.ACESFilmicToneMapping;r.toneMappingExposure=.9;document.getElementById('v').appendChild(r.domElement);return r});
const ktx2=new KTX2Loader().setTranscoderPath('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/libs/basis/').detectSupport(views[0]);
const loader=new THREE.GLTFLoader().setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
const load=u=>new Promise((ok,no)=>loader.load(u,g=>ok(g.scene),0,no));
const ANGLES=[[.8,.6,1.2],[-1.2,.4,-.6],[0,1.6,.2]]; // 3/4 front, back-side, top
window.show=async(a,b)=>{const ms=await Promise.all([load(a),load(b)]);
  const box=new THREE.Box3().setFromObject(ms[0]),c=box.getCenter(new THREE.Vector3()),r=box.getSize(new THREE.Vector3()).length()/2;
  ms.forEach((m,row)=>{const s=new THREE.Scene();s.add(new THREE.HemisphereLight(0xffffff,0xe0b870,.75));const d=new THREE.DirectionalLight(0xffffff,.85);d.position.set(4,8,6);s.add(d);s.add(m);
    ANGLES.forEach((v,i)=>{const cam=new THREE.PerspectiveCamera(35,1,r/50,r*20);cam.position.copy(c).add(new THREE.Vector3(...v).normalize().multiplyScalar(r*3.2));cam.lookAt(c);views[row*3+i].render(s,cam)})});
  return ms.map(m=>{let t=0;m.traverse(o=>{if(o.isMesh){const g=o.geometry;t+=(g.index?g.index.count:g.attributes.position.count)/3}});return t})};
window.ready=true;
</script>"""
SHIM = ("const T=window.THREE;export const {CompressedTexture,CompressedTextureLoader,FileLoader,LinearEncoding,sRGBEncoding,LinearFilter,"
        "LinearMipmapLinearFilter,Loader,RGBAFormat,RGBA_ASTC_4x4_Format,RGBA_BPTC_Format,RGBA_ETC2_EAC_Format,RGBA_PVRTC_4BPPV1_Format,"
        "RGBA_S3TC_DXT5_Format,RGB_ETC1_Format,RGB_ETC2_Format,RGB_PVRTC_4BPPV1_Format,RGB_S3TC_DXT1_Format,UnsignedByteType}=T;\n")
SHAPE_MAX, COLOUR_MAX = 1.0, 4.0  # % : silhouette mismatch (shape changed) / mean colour diff inside the prop (beyond compression noise)

def compare(png):
    """-> worst (silhouette mismatch %, colour diff %) over the 3 angles of a 2x3 before/after sheet."""
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
    worst = [0.0, 0.0]
    for i in range(3):
        A, B = im[:280, i * 280:(i + 1) * 280], im[280:560, i * 280:(i + 1) * 280]
        ma, mb = [np.abs(x - [255, 0, 255]).sum(2) > 40 for x in (A, B)]  # not magenta = the prop
        sil = (ma ^ mb).sum() / max(ma.sum(), 1) * 100
        both = ma & mb
        col = np.abs(A - B)[both].mean() / 255 * 100 if both.any() else 100
        worst = [max(worst[0], sil), max(worst[1], col)]
    return worst

def verify(pairs, out):
    from playwright.sync_api import sync_playwright
    from browser import launch, gpu_info
    vdir = out / "_verify"; vdir.mkdir(exist_ok=True); bad = []
    with tempfile.TemporaryDirectory() as d, sync_playwright() as p:
        d = pathlib.Path(d); (d / "index.html").write_text(PAGE, encoding="utf-8"); (d / "three-global.js").write_text(SHIM, encoding="utf-8")
        files = {"index.html": d / "index.html", "three-global.js": d / "three-global.js"}
        for i, (a, b) in enumerate(pairs): files[f"a{i}.glb"], files[f"b{i}.glb"] = a, b
        br = launch(p)
        pg = br.new_page(viewport={"width": 840, "height": 560}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.route("http://verify.test/**", lambda r: r.fulfill(path=str(files[r.request.url.rsplit("/", 1)[1]])))
        pg.goto("http://verify.test/index.html"); pg.wait_for_function("window.ready", timeout=60000)
        print(f"\nvisual check in three.js r128 (GLTFLoader + KTX2Loader + MeshoptDecoder), GPU: {gpu_info(pg)}")
        print("| file | tris loaded before -> after | shape diff % (worst of 3 angles) | colour diff % | verdict | sheet |\n|---|---|---|---|---|---|")
        for i, (a, b) in enumerate(pairs):
            ta, tb = pg.evaluate(f"show('a{i}.glb','b{i}.glb')")
            png = vdir / (a.stem + ".png"); pg.screenshot(path=str(png))
            sil, col = compare(png)
            ok = sil <= SHAPE_MAX and col <= COLOUR_MAX and ta == tb
            if not ok: bad.append(a.name)
            print(f"| {a.name} | {ta:,.0f} -> {tb:,.0f} | {sil:.2f} | {col:.2f} | {'same' if ok else '**CHECK**'} | {png.name} |", flush=True)
        br.close()
    if errs: print("page errors:", *errs, sep="\n  ")
    if bad: print("flagged:", ", ".join(bad))
    return not errs and not bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default=r"C:\Users\ahmma\Downloads\Pash 3D\props")
    ap.add_argument("--out"); ap.add_argument("--meshopt", action="store_true"); ap.add_argument("--verify", action="store_true")
    ap.add_argument("--only", nargs="*"); g = ap.add_mutually_exclusive_group()
    g.add_argument("--webp", action="store_true"); g.add_argument("--ktx2", action="store_true")
    a = ap.parse_args()
    src = pathlib.Path(a.src); out = pathlib.Path(a.out) if a.out else src / "optimized"
    if out.resolve() == src.resolve(): sys.exit("--out must differ from the source folder")
    toktx = shutil.which("toktx")
    print(f"tools: node {NODE}; gltf-transform via npx @4; toktx {'found: ' + toktx if toktx else 'NOT found (KTX2 off, WebP fallback)'}")
    if a.ktx2 and not toktx: sys.exit("--ktx2 needs toktx (KTX-Software 4.x) on PATH")
    ktx2 = toktx and not a.webp
    out.mkdir(parents=True, exist_ok=True); classes, pairs = table_classes(), []
    print(f"mode: {'KTX2 (UASTC data maps + ETC1S colour)' if ktx2 else 'WebP, half-size textures'}{' + meshopt' if a.meshopt else ''}\n")
    print("| file | class | tris | file KB | tex MB loaded | result after |\n|---|---|---|---|---|---|")
    for f in sorted(src.glob("*.glb")):
        if a.only and f.stem not in a.only and f.name not in a.only: continue
        before = check(f, classes)
        if not before: continue
        dst = out / f.name
        optimize(f, dst, before["cls"], ktx2, a.meshopt)
        after = check(dst, {f.name: before["cls"]})
        res = ("OVER: " + "; ".join(after["hard"])) if after["hard"] else "ok"
        print(f"| {f.name} | {before['cls']} | {before['tris']:,} -> {after['tris']:,} | {before['kb']:.0f} -> {after['kb']:.0f} | "
              f"{before['mb_now']:.1f} -> {after['mb_now']:.1f} | {res} |", flush=True)
        pairs.append((f, dst))
    if a.verify and pairs and not verify(pairs, out): sys.exit(1)

if __name__ == "__main__":
    main()

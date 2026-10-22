"""Runtime GPU check of the web game: per room/screen draw calls, triangles, textures vs docs/gpu-budget.md.

  python tools/gpu_runtime_check.py [--port 8770] [--page index.html] [--props DIR]

Serves Pash-dev on localhost, opens the page in headless Chromium on the real GPU (tools/browser.py;
GOOGOO_SWIFTSHADER=1 = software) as an iPhone 11-size phone and an iPad 9, taps "Wake up", visits every
screen and reads renderer.info after a rendered frame. --props DIR serves DIR/<name>.glb in place of
models/<name>.glb (e.g. the optimized props) without touching the repo. Calls/tris are one full frame incl. the shadow pass.
FPS is desktop best case (RTX 3060 Ti), not a phone number. Exits 1 if any screen is over budget.
Texture MB = what is really on the GPU: the WebGL texture calls are wrapped (HOOK) and every live GL texture's bytes are added up
(RGB counted as 4 bytes/px, + 1/3 for mipmaps, shadow maps and PMREM included). Until 2026-10-22 this column was an estimate of every
three.js texture reachable from the scene, which also counted the props of rooms already left (their GPU copies are disposed): ~2x too high.
"""
import argparse, functools, http.server, pathlib, sys, threading
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from browser import launch, gpu_info, fps

ROOT = pathlib.Path(__file__).resolve().parent.parent
CALLS, TRIS, TEX_MB = 100, 200_000, 96
SCREENS = ["home", "play", "bed", "bed-night", "say", "library", "library-book"]  # library-book: a picture book open on his face
DEVICES = {"phone 414x896@2 (iPhone 11)": dict(viewport={"width": 414, "height": 896}, screen={"width": 414, "height": 896},
                                                device_scale_factor=2, is_mobile=True, has_touch=True),
           "tablet 810x1080@2 (iPad 9)": dict(viewport={"width": 810, "height": 1080}, screen={"width": 810, "height": 1080},
                                               device_scale_factor=2, has_touch=True)}
# live GL textures: bytes per texture object, from the upload calls; deleteTexture drops it
HOOK = r"""(() => {
  const live = new Map(); window.__gpuTex = live; let n = 0;
  const BPP = f => ({6406:1,6409:1,6410:2,6407:4,6408:4,32856:4,35907:4,32849:4,33321:1,33323:2,34842:8,34836:16,6402:4,33189:4,33190:4,36012:4,35056:4}[f] || 4); // RGB is padded to 4 on GPUs
  for (const P of [WebGLRenderingContext.prototype, window.WebGL2RenderingContext && WebGL2RenderingContext.prototype].filter(Boolean)) {
    const bound = new WeakMap(), cur = gl => { const m = bound.get(gl) || {}; bound.set(gl, m); return m; };
    const o = {}; for (const k of ['createTexture','deleteTexture','bindTexture','activeTexture','texImage2D','texStorage2D','compressedTexImage2D','generateMipmap','texImage3D','texStorage3D']) o[k] = P[k];
    P.createTexture = function () { const t = o.createTexture.call(this); t.__id = ++n; live.set(t, {id: t.__id, lv: {}, mip: false, w: 0, h: 0}); return t; };
    P.deleteTexture = function (t) { live.delete(t); return o.deleteTexture.call(this, t); };
    P.activeTexture = function (u) { cur(this).unit = u; return o.activeTexture.call(this, u); };
    P.bindTexture = function (tg, t) { const m = cur(this); (m.b = m.b || {})[(m.unit || 0) + ':' + tg] = t; return o.bindTexture.call(this, tg, t); };
    const tex = (gl, tg) => { const m = cur(gl), t = (m.b || {})[(m.unit || 0) + ':' + (tg >= 34069 && tg <= 34074 ? 34067 : tg)]; return t && live.get(t); };
    const dims = a => { if (a.length >= 8 || (a.length === 9)) return [a[3], a[4], a[2], a[7]]; const s = a[5]; return [s.width || s.videoWidth || 0, s.height || s.videoHeight || 0, a[2], a[4]]; };
    P.texImage2D = function (...a) { const r = tex(this, a[0]); if (r) { let w, h, ifmt, fmt; if (a.length >= 8) { w = a[3]; h = a[4]; ifmt = a[2]; } else { const s = a[5]; w = s.width || s.videoWidth || 0; h = s.height || s.videoHeight || 0; ifmt = a[2]; }
        r.lv[a[0] + ':' + a[1]] = w * h * BPP(ifmt); if (a[1] === 0) { r.w = w; r.h = h; } } return o.texImage2D.apply(this, a); };
    P.compressedTexImage2D = function (...a) { const r = tex(this, a[0]); if (r) { r.lv[a[0] + ':' + a[1]] = a[6].byteLength; if (a[1] === 0) { r.w = a[3]; r.h = a[4]; } } return o.compressedTexImage2D.apply(this, a); };
    P.texStorage2D = function (tg, levels, ifmt, w, h) { const r = tex(this, tg); if (r) { let b = 0, x = w, y = h; for (let i = 0; i < levels; i++) { b += x * y * BPP(ifmt); x = Math.max(1, x >> 1); y = Math.max(1, y >> 1); } r.lv.storage = b * (tg === 34067 ? 6 : 1); r.w = w; r.h = h; } return o.texStorage2D.apply(this, arguments); };
    P.generateMipmap = function (tg) { const r = tex(this, tg); if (r) r.mip = true; return o.generateMipmap.call(this, tg); };
  }
})()"""
# one whole game frame: r128 resets renderer.info AFTER the shadow pass, so autoReset is switched off for one frame to count it;
# plus a texture-memory estimate of everything in the scene (RGBA8 + mips unless compressed, + shadow maps)
INFO = """() => new Promise(res => requestAnimationFrame(() => { renderer.info.autoReset = false; renderer.info.reset(); requestAnimationFrame(() => {
  let bytes = 0; for (const r of window.__gpuTex.values()) { let b = 0; for (const k in r.lv) b += r.lv[k]; bytes += r.mip ? b * 4 / 3 : b; }
  const r = renderer.info; renderer.info.autoReset = true;
  res({ calls: r.render.calls, tris: r.render.triangles, geos: r.memory.geometries, texs: r.memory.textures,
        programs: (r.programs || []).length, texMB: bytes / 2 ** 20, dpr: renderer.getPixelRatio(),
        px: renderer.domElement.width + 'x' + renderer.domElement.height, shadows: renderer.shadowMap.enabled });
}); }))"""

def serve(port):
    h = functools.partial(type("Q", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}), directory=str(ROOT))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", port), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8770); ap.add_argument("--page", default="index.html"); ap.add_argument("--props")
    a = ap.parse_args(); srv = serve(a.port); over = False
    with sync_playwright() as p:
        br = launch(p)
        for dev, opts in DEVICES.items():
            ctx = br.new_context(service_workers="block", **opts); ctx.add_init_script(HOOK); pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            if a.props:
                alt = lambda r: (pathlib.Path(a.props) / r.request.url.split("?")[0].rsplit("/", 1)[1])
                pg.route("**/models/*.glb", lambda r: r.fulfill(path=str(alt(r))) if alt(r).exists() else r.continue_())
            pg.goto(f"http://127.0.0.1:{a.port}/{a.page}"); pg.wait_for_timeout(1500)
            print(f"\n### {dev}  GPU: {gpu_info(pg)}")
            pg.click("#go"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(3000)
            print(f"| screen | draw calls (<= {CALLS}) | triangles (<= {TRIS // 1000}k) | textures / geometries / programs | tex MB live on GPU (<= {TEX_MB}) | canvas px (DPR) | fps (desktop) | result |")
            print("|---|---|---|---|---|---|---|---|")
            for s in SCREENS:
                room = s.split("-")[0]
                pg.evaluate(f"setRoom('{room}')"); pg.wait_for_timeout(1200)
                if s.endswith("night"): pg.evaluate("setLights(false)"); pg.wait_for_timeout(300)
                if s.endswith("book"): pg.evaluate("openBook(libItems.findIndex(i=>i.kind==='cat'))"); pg.wait_for_timeout(2000)
                i = pg.evaluate(INFO); f = fps(pg, 3)
                bad = [k for k, v, m in (("calls", i["calls"], CALLS), ("tris", i["tris"], TRIS), ("tex", i["texMB"], TEX_MB)) if v > m]
                over |= bool(bad)
                print(f"| {s} | {i['calls']} | {i['tris']:,} | {i['texs']} / {i['geos']} / {i['programs']} | {i['texMB']:.1f} | "
                      f"{i['px']} ({i['dpr']}) | {f:.0f} | {'**OVER ' + ', '.join(bad) + '**' if bad else 'ok'} |", flush=True)
                if s.endswith("night"): pg.evaluate("setLights(true)")
            pg.screenshot(path=str(pathlib.Path(__import__("tempfile").gettempdir()) / f"gpu_runtime_{dev.split()[0]}.png"))
            if errs: print("page errors:", *errs[:5], sep="\n  ")
            ctx.close()
        br.close()
    srv.shutdown()
    sys.exit(1 if over else 0)

if __name__ == "__main__":
    main()

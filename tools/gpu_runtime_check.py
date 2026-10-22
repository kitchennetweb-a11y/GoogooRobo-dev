"""Runtime GPU check of the web game: per room/screen draw calls, triangles, textures vs docs/gpu-budget.md.

  python tools/gpu_runtime_check.py [--port 8770] [--page index.html] [--props DIR]

Serves Pash-dev on localhost, opens the page in headless Chromium on the real GPU (tools/browser.py;
GOOGOO_SWIFTSHADER=1 = software) as an iPhone 11-size phone and an iPad 9, taps "Wake up", visits every
screen and reads renderer.info after a rendered frame. --props DIR serves DIR/<name>.glb in place of
models/<name>.glb (e.g. the optimized props) without touching the repo. Calls/tris are one full frame incl. the shadow pass.
FPS is desktop best case (RTX 3060 Ti), not a phone number. Exits 1 if any screen is over budget.
"""
import argparse, functools, http.server, pathlib, sys, threading
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from browser import launch, gpu_info, fps

ROOT = pathlib.Path(__file__).resolve().parent.parent
CALLS, TRIS, TEX_MB = 100, 200_000, 96
SCREENS = ["home", "play", "bed", "bed-night", "say", "book"]
DEVICES = {"phone 414x896@2 (iPhone 11)": dict(viewport={"width": 414, "height": 896}, screen={"width": 414, "height": 896},
                                                device_scale_factor=2, is_mobile=True, has_touch=True),
           "tablet 810x1080@2 (iPad 9)": dict(viewport={"width": 810, "height": 1080}, screen={"width": 810, "height": 1080},
                                               device_scale_factor=2, has_touch=True)}
# one whole game frame: r128 resets renderer.info AFTER the shadow pass, so autoReset is switched off for one frame to count it;
# plus a texture-memory estimate of everything in the scene (RGBA8 + mips unless compressed, + shadow maps)
INFO = """() => new Promise(res => requestAnimationFrame(() => { renderer.info.autoReset = false; renderer.info.reset(); requestAnimationFrame(() => {
  const seen = new Set(); let bytes = 0;
  const add = t => { if (!t || !t.isTexture || seen.has(t.uuid)) return; seen.add(t.uuid);
    const i = t.image || {}, w = i.width || 0, h = i.height || 0;
    bytes += w * h * (t.isCompressedTexture ? 1 : 4) * (t.generateMipmaps !== false ? 4 / 3 : 1); };
  scene.traverse(o => { if (o.material) [].concat(o.material).forEach(m => { for (const k in m) add(m[k]); }); });
  add(scene.environment && scene.environment.isTexture ? scene.environment : null);
  scene.traverse(o => { if (o.isLight && o.castShadow && o.shadow.map) bytes += o.shadow.map.width * o.shadow.map.height * 4; });
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
            ctx = br.new_context(service_workers="block", **opts); pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            if a.props:
                alt = lambda r: (pathlib.Path(a.props) / r.request.url.split("?")[0].rsplit("/", 1)[1])
                pg.route("**/models/*.glb", lambda r: r.fulfill(path=str(alt(r))) if alt(r).exists() else r.continue_())
            pg.goto(f"http://127.0.0.1:{a.port}/{a.page}"); pg.wait_for_timeout(1500)
            print(f"\n### {dev}  GPU: {gpu_info(pg)}")
            pg.click("#go"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(3000)
            print(f"| screen | draw calls (<= {CALLS}) | triangles (<= {TRIS // 1000}k) | textures / geometries / programs | tex MB est (<= {TEX_MB}) | canvas px (DPR) | fps (desktop) | result |")
            print("|---|---|---|---|---|---|---|---|")
            for s in SCREENS:
                room = s.split("-")[0]
                pg.evaluate(f"setRoom('{room}')"); pg.wait_for_timeout(1200)
                if s.endswith("night"): pg.evaluate("setLights(false)"); pg.wait_for_timeout(300)
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

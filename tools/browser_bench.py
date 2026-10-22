import sys, time, os
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from browser import launch, gpu_info, fps
URL = "http://localhost:8771/"
for gpu in (True, False):
    with sync_playwright() as p:
        b = launch(p, gpu=gpu)
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        t0 = time.time(); pg.goto(URL, wait_until="load")
        pg.wait_for_function("!document.querySelector('#go').disabled", timeout=120000)
        load = time.time() - t0
        r = gpu_info(pg, require_nvidia=gpu)
        t1 = time.time(); pg.screenshot(path=os.environ["TEMP"] + f"/shot_{'gpu' if gpu else 'sw'}.png"); shot = time.time() - t1
        pg.click("#go"); pg.wait_for_timeout(3000)
        f = fps(pg, 5)
        print(("GPU" if gpu else "SwiftShader"), "|", r, f"| load+ready {load:.1f}s | screenshot {shot:.2f}s | fps {f:.1f}")
        b.close()

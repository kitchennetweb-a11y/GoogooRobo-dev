"""Shared Playwright launcher: real GPU (RTX 3060 Ti) by default.

  from browser import launch, gpu_info, fps
  with sync_playwright() as p:
      b = launch(p)                 # GOOGOO_SWIFTSHADER=1 -> software GL fallback
      page = b.new_page(); page.goto(url)
      print(gpu_info(page), fps(page, 5))

Headless Chromium on Windows gets the real GPU with these flags (ANGLE/D3D11), no headed mode needed.
"""
import os

GPU_ARGS = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist",
            "--enable-gpu-rasterization", "--enable-zero-copy"]
SOFT_ARGS = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"]


def launch(p, gpu=True, headless=True):
    if os.environ.get("GOOGOO_SWIFTSHADER") == "1":
        gpu = False
    return p.chromium.launch(headless=headless, args=GPU_ARGS if gpu else SOFT_ARGS)


def renderer(page):
    return page.evaluate("""() => {
      const gl = document.createElement('canvas').getContext('webgl2') || document.createElement('canvas').getContext('webgl');
      if (!gl) return 'no-webgl';
      const e = gl.getExtension('WEBGL_debug_renderer_info');
      return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    }""")


def gpu_info(page, require_nvidia=None):
    """Returns the UNMASKED_RENDERER string; asserts NVIDIA unless the SwiftShader fallback is on."""
    r = renderer(page)
    if require_nvidia is None:
        require_nvidia = os.environ.get("GOOGOO_SWIFTSHADER") != "1"
    if require_nvidia:
        assert "nvidia" in r.lower(), f"not on the NVIDIA GPU: {r!r} (set GOOGOO_SWIFTSHADER=1 to allow software)"
    return r


def fps(page, seconds=5):
    """Average requestAnimationFrame rate over `seconds`."""
    return page.evaluate("""(s) => new Promise(res => {
      let n = 0, t0 = performance.now();
      (function f(t) { n++; if (t - t0 >= s * 1000) res(n / ((t - t0) / 1000)); else requestAnimationFrame(f); })(t0);
    })""", seconds)

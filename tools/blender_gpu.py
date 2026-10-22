"""Use the RTX 3060 Ti for Blender background renders, per script (never saves preferences).

At the top of a script run with  blender.exe -b file.blend --python script.py :
    import sys; sys.path.insert(0, "C:/Users/ahmma/Documents/Virtual Pet/Pash-dev/tools")
    import blender_gpu; blender_gpu.setup()          # Cycles->OptiX GPU; EEVEE needs nothing (uses the GPU already)
Env GOOGOO_CPU=1 forces CPU Cycles (fallback). Returns a string describing what was enabled.
"""
import os
import bpy


def setup(scene=None, backends=("OPTIX", "CUDA")):
    scene = scene or bpy.context.scene
    if os.environ.get("GOOGOO_CPU") == "1":
        if scene.render.engine == "CYCLES":
            scene.cycles.device = "CPU"
        return "cpu (forced)"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for be in backends:
        try:
            prefs.compute_device_type = be
            prefs.get_devices()
        except Exception:
            continue
        gpus = [d for d in prefs.devices if d.type == be]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == be          # GPU only (CPU off: mixed is slower for small scenes)
            scene.cycles.device = "GPU"
            return f"{be}: " + ", ".join(d.name for d in gpus)
    scene.cycles.device = "CPU"
    return "cpu (no GPU backend found)"

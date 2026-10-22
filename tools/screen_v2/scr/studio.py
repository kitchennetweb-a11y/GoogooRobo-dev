"""shared scene setup: rest pose, EEVEE GPU, standard view, game-like light, camera helper"""
import sys, math, bpy, mathutils
sys.path.insert(0, "C:/Users/ahmma/Documents/Virtual Pet/Pash-dev/tools")
import blender_gpu
V = mathutils.Vector

def setup(res=1600):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    print("gpu:", blender_gpu.setup(sc))
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    sc.render.film_transparent = False
    try: sc.eevee.taa_render_samples = 64
    except Exception: pass
    for a in ("use_raytracing",):
        try: setattr(sc.eevee, a, True)
        except Exception: pass
    bpy.data.objects['Googoo_tripo_rig'].data.pose_position = 'REST'
    if 'Icosphere' in bpy.data.objects: bpy.data.objects['Icosphere'].hide_render = True
    w = bpy.data.worlds.get('Studio') or bpy.data.worlds.new('Studio'); sc.world = w
    w.use_nodes = True; bg = w.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (0.80, 0.82, 0.86, 1); bg.inputs[1].default_value = 0.55
    for n, (loc, en, col) in {"KeySun": ((-3.5, -5.5, 9), 2.6, (1, .95, .87)), "FillSun": ((5, -8, 4), 0.6, (1, .89, .77))}.items():
        L = bpy.data.objects.get(n)
        if not L:
            L = bpy.data.objects.new(n, bpy.data.lights.new(n, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = en; L.data.color = col; L.data.angle = math.radians(3)
        L.rotation_euler = (V((0, 0, 0)) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    return sc

def cam(name, loc, target, lens=85, ortho=None):
    sc = bpy.context.scene
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.location = V(loc); c.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.clip_start = 0.005; c.data.clip_end = 50
    c.data.sensor_width = 36
    if ortho: c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    return c

def render(c, path):
    sc = bpy.context.scene; sc.camera = c; sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

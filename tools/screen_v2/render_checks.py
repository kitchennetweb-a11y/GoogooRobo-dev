"""Check renders of googoo_anims_v2.blend (EEVEE, GPU): poses x views, cameras follow the head. Not saved.
run: blender -b "Downloads/Pash 3D/googoo_anims_v2.blend" --python tools/screen_v2/render_checks.py -- <face.png> <out_dir>"""
import sys, os, math, bpy, mathutils
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scr")); import studio
from mathutils.bvhtree import BVHTree
V = mathutils.Vector
FACE, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
sc = studio.setup(1000); arm = bpy.data.objects["Googoo_tripo_rig"]; arm.animation_data_clear()  # setup() puts the rig in REST
body, lcd = bpy.data.objects["Googoo_body"], bpy.data.objects["Googoo_face_screen"]
m = bpy.data.materials.new("FaceCheck"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(FACE); em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tx.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0]); lcd.data.materials[0] = m
A, B, R, ZC = 0.153, 0.109, 0.078, 0.815
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
hit = lambda x, z: bvh.ray_cast(V((x, -1, z)), V((0, 1, 0)))[0]
cx, cz = -(A - R) - (R + .002) * .7071, ZC + (B - R) + (R + .002) * .7071  # on the face, 2 mm outside the opening
corner, edge, tgt = hit(cx, cz), hit(0, ZC + B + .002), V((0, -0.1, 0.82)); arm.data.pose_position = "POSE"
orbit = lambda t, yaw, pitch, dist=2.0: t + dist * V((math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)), -math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)), math.sin(math.radians(pitch))))
VIEWS = {"front": ((0, -2.0, 0.815), (0, 0, 0.815), 150), "34": (orbit(tgt, 35, 10), tgt, 150),
         "corner": (orbit(corner, -22, 14), corner, 600), "edge": (orbit(edge, 8, 16), edge, 600), "side": (orbit(V((0, -0.06, 0.815)), 80, 5), V((0, -0.06, 0.815)), 150)}
head = arm.pose.bones["mixamorig:Head"]
def hm(): bpy.context.view_layer.update(); return arm.matrix_world @ head.matrix
def rest():
    for pb in arm.pose.bones: pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
arm.animation_data_clear(); rest(); H0 = hm()
POSES = [("rest", None, 0), ("wave_bye_both", "wave_bye_both", 45), ("cheer", "cheer", 40), ("jump", "jump_joyful", 28), ("head_twist", None, 0)]
for name, act, fr in POSES:
    arm.animation_data_clear()
    rest()
    if act:
        ad = arm.animation_data_create(); ad.action = bpy.data.actions[act]; ad.action_slot = ad.action.slots[0]
    if name == "head_twist":
        head.rotation_mode = "XYZ"; head.rotation_euler = (math.radians(15), math.radians(25), math.radians(10))
    sc.frame_set(fr); M = hm() @ H0.inverted()
    for v, (loc, t, lens) in VIEWS.items():
        if name != "rest" and v == "side": continue
        c = studio.cam("chk_" + v, M @ V(loc), M @ V(t), lens=lens)
        studio.render(c, os.path.join(OUT, f"chk_{name}_{v}.png"))
print("RENDERED")

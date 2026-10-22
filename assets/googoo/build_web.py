# Builds the phone-friendly Googoo for the game (assets/googoo/) from googoo_anims_v2.glb (Googoo with the v2 cut-in LCD face screen + 19 cleaned Mixamo clips, 30 fps):
#   googoo.glb            = mesh (body + LCD "Googoo_face_screen"), skin, base-colour texture 1024 px, no clips (loads before the start button)
#   googoo_anims_web.glb  = the clips the game uses, on a bare skeleton (no mesh), loaded after the start; the game binds them to googoo.glb by bone name
#                           (DROP: idle / sit are still poses in code, the waves are procedural)
#   both: constant (= rest pose) tracks dropped, rotation keys and skin weights as normalized 16-bit ints, shared key-time arrays
#   face.webp + face.json + face_bg.jpg = the face kit on the LCD: its FRONT-VIEW layers (the LCD has planar front UVs: canvas = LCD front box,
#                  top row = top), drawn at real size (1024 px = LCD width, the old density), the features centred in the opening, the rest = screen
#                  background; each layer cut into its pixel islands (left/right eye) and packed into one atlas
# Run: python assets/googoo/build_web.py [face_kit_dir] [googoo_anims_v2.glb]   (defaults: %USERPROFILE%/Downloads/Pash 3D/face_kit, .../googoo_anims_v2.glb)
import io, json, os, struct, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
DL = os.path.join(os.path.expanduser('~'), 'Downloads', 'Pash 3D')
KIT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DL, 'face_kit')
SRC = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DL, 'googoo_anims_v2.glb')
DROP = {'idle_happy', 'idle_breathing', 'look_around', 'sit_floor_idle', 'wave_hello', 'wave_bye_both'}  # unused by the game
SV2 = os.path.join(ROOT, 'tools', 'screen_v2')  # v2 screen build: opening / LCD sizes (v2/params_v2.json), the face kit's front-view drawing box (scr/params.json)
TEX = 1024
COMP = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
NUM = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def glb():
    d = open(SRC, 'rb').read()  # fresh copy per output (build_glb edits the json)
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(d[20:20 + jl])
    bl = struct.unpack('<I', d[20 + jl:24 + jl])[0]
    return j, d[28 + jl:28 + jl + bl]


def read(j, b, ai):
    a = j['accessors'][ai]; v = j['bufferViews'][a['bufferView']]; n = NUM[a['type']]
    assert 'byteStride' not in v
    vals = struct.unpack_from('<%d%s' % (a['count'] * n, COMP[a['componentType']]), b, v.get('byteOffset', 0) + a.get('byteOffset', 0))
    return [vals[i:i + n] for i in range(0, len(vals), n)]


def is_rest(node, path, keys, eps=1e-4):
    rest = node.get(path, {'translation': [0, 0, 0], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}[path])
    for k in keys:
        if path == 'rotation' and sum(x * y for x, y in zip(k, rest)) < 0: k = [-x for x in k]
        if max(abs(x - y) for x, y in zip(k, rest)) > eps: return False
    return True


def build_glb(keep, name, mesh=True):
    j, b = glb()
    anims, dropped = [], 0
    for an in j['animations']:
        if not keep(an['name']): continue
        ch = []
        for c in an['channels']:
            s = an['samplers'][c['sampler']]
            if is_rest(j['nodes'][c['target']['node']], c['target']['path'], read(j, b, s['output'])): dropped += 1; continue
            ch.append(c)
        samp = sorted({c['sampler'] for c in ch})
        an['samplers'] = [an['samplers'][i] for i in samp]
        for c in ch: c['sampler'] = samp.index(c['sampler'])
        an['channels'] = ch; anims.append(an)
    j['animations'] = anims
    if not anims: j.pop('animations')  # glTF: no empty arrays
    if not mesh:  # clips only: the bare skeleton (node names + hierarchy) is all the loader needs to build the tracks
        for k in ('meshes', 'skins', 'materials', 'textures', 'images', 'samplers'): j.pop(k, None)
        for nd in j['nodes']: nd.pop('mesh', None); nd.pop('skin', None)
        j['meshes'] = []
    else:  # texture -> 1024 jpeg
        assert len(j['images']) == 1, [i.get('name') for i in j['images']]  # the body texture only (the game draws the LCD)
        img = j['images'][0]; v = j['bufferViews'][img['bufferView']]
        im = Image.open(io.BytesIO(b[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])).convert('RGB')
        print('texture', im.size, '->', TEX)
        out = io.BytesIO(); im.resize((TEX, TEX), Image.LANCZOS).save(out, 'JPEG', quality=86, optimize=True); jpg = out.getvalue()
    # repack only what is still used
    used = set()
    for m in j['meshes']:
        for p in m['primitives']: used |= set(p['attributes'].values()); 'indices' in p and used.add(p['indices'])
    for s in j.get('skins', []): 'inverseBindMatrices' in s and used.add(s['inverseBindMatrices'])
    for an in anims:
        for s in an['samplers']: used |= {s['input'], s['output']}
    amap = {o: n for n, o in enumerate(sorted(used))}
    # smaller, loader-supported encodings (glTF core): rotation keys as normalized int16, skin weights as normalized uint16
    rot = {s['output'] for an in anims for c in an['channels'] for s in [an['samplers'][c['sampler']]] if c['target']['path'] == 'rotation'}
    wts = {p['attributes']['WEIGHTS_0'] for m in j['meshes'] for p in m['primitives']}
    views, bin_, seen = [], bytearray(), {}

    def put(data, target=None):
        if data in seen: return seen[data]  # identical key-time arrays are shared by many tracks
        while len(bin_) % 4: bin_.append(0)
        views.append({'buffer': 0, 'byteOffset': len(bin_), 'byteLength': len(data)}); bin_.extend(data)
        if target: views[-1]['target'] = target
        seen[data] = len(views) - 1; return len(views) - 1
    accs = []
    for o in sorted(used):
        a = dict(j['accessors'][o]); v = j['bufferViews'][a['bufferView']]; off = v.get('byteOffset', 0)
        data = b[off:off + v['byteLength']]
        if o in rot or o in wts:
            q = []
            for k in read(j, b, o):
                if o in rot: q += [round(x * 32767) for x in k]
                else:
                    w = [round(x * 65535) for x in k]; w[w.index(max(w))] += 65535 - sum(w); q += w
            data = struct.pack('<%d%s' % (len(q), 'h' if o in rot else 'H'), *q)
            a.update(componentType=5122 if o in rot else 5123, normalized=True); a.pop('min', None); a.pop('max', None)
        a['bufferView'] = put(data, v.get('target')); accs.append(a)
    if mesh: img['bufferView'] = put(jpg); img['mimeType'] = 'image/jpeg'
    j['accessors'], j['bufferViews'] = accs, views
    if not mesh: j.pop('meshes')
    for m in j.get('meshes', []):
        for p in m['primitives']:
            p['attributes'] = {k: amap[x] for k, x in p['attributes'].items()}
            if 'indices' in p: p['indices'] = amap[p['indices']]
    for s in j.get('skins', []):
        if 'inverseBindMatrices' in s: s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
    for an in anims:
        for s in an['samplers']: s['input'], s['output'] = amap[s['input']], amap[s['output']]
    while len(bin_) % 4: bin_.append(0)
    j['buffers'] = [{'byteLength': len(bin_)}]
    js = json.dumps(j, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    data = struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bin_
    open(os.path.join(HERE, name), 'wb').write(data)
    print(name, len(data) // 1024, 'KB; clips', [a['name'] for a in anims], '; dropped', dropped, 'rest-pose tracks')


def build_face():
    kit = json.load(open(os.path.join(KIT, 'face_kit.json'), encoding='utf-8'))
    FV = os.path.join(KIT, 'layers_front_view')  # 2048 x 1438, front-orthographic, covering draw_bbox (world x0, x1, z0, z1; Blender z up)
    P2 = json.load(open(os.path.join(SV2, 'v2', 'params_v2.json')))
    X0, X1, Z0, Z1 = json.load(open(os.path.join(SV2, 'scr', 'params.json')))['draw_bbox']
    AP, BP, ZC = P2['a'] + P2['ov'], P2['b'] + P2['ov'], P2['zc']  # LCD half width / height and centre height: its UV 0..1 = this front box
    W = 1024; H = round(W * BP / AP); ppm = W / (2 * AP)  # canvas px per metre on the LCD
    lay = lambda n: Image.open(os.path.join(FV, n + '.png')).convert('RGBA')
    fw, fh = lay('mouth_smile').size; s = ppm / (fw / (X1 - X0))  # front-view px -> canvas px (real size)
    exps = {k: [[l['layer'], *[c * s for c in l.get('offset', [0, 0])], l.get('clip', '')] for l in e['layers']] for k, e in kit['expressions'].items()}
    used = {l[0] for e in exps.values() for l in e} | {l[3] for e in exps.values() for l in e if l[3]}
    # centre the drawn features (union of every expression's layers; pupils stay inside the eyes) in the opening
    U = [fw, fh, 0, 0]
    for n in used - {'eyes_open_pupils', 'eyes_open_mask'}:
        b = lay(n).getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
        U = [min(U[0], b[0]), min(U[1], b[1]), max(U[2], b[2]), max(U[3], b[3])]
    cx, cz = X0 + (U[0] + U[2]) / 2 * (X1 - X0) / fw, Z1 - (U[1] + U[3]) / 2 * (X1 - X0) / fw  # world centre of the features
    L, T = round((X0 - cx + AP) * ppm), round((ZC + BP - (Z1 - cz + ZC)) * ppm)  # canvas position of the drawing's top-left corner
    sw, sh = round(fw * s), round(fh * s)
    print('face canvas', W, H, 'scale', round(s, 4), 'drawing at', L, T, sw, sh, '; features', [round((U[0]) * s + L), round(U[1] * s + T), round(U[2] * s + L), round(U[3] * s + T)])
    pieces = []  # (layer, x, y, image): each layer split at empty column gaps (left eye / right eye), cropped to its pixels
    for name in sorted(used):
        im = lay(name).resize((sw, sh), Image.LANCZOS)
        a = im.getchannel('A').point(lambda v: 255 if v > 2 else 0)
        cols = [a.crop((c, 0, c + 1, sh)).getbbox() is not None for c in range(sw)]
        c = 0
        while c < sw:
            if not cols[c]: c += 1; continue
            e = c
            while e < sw and (cols[e] or any(cols[e:e + 24])): e += 1
            box = a.crop((c, 0, e, sh)).getbbox()
            box = (max(0, c + box[0] - 2), max(0, box[1] - 2), min(sw, c + box[2] + 2), min(sh, box[3] + 2))
            pieces.append((name, box[0] + L, box[1] + T, im.crop(box))); c = e
    # shelf packing, tallest first, 1024 wide (same width as the face canvas)
    AW, x, y, row, rects = 1024, 0, 0, 0, {}
    for name, ox, oy, im in sorted(pieces, key=lambda p: -p[3].height):
        if x + im.width > AW: x, y, row = 0, y + row + 2, 0
        rects.setdefault(name, []).append([x, y, im.width, im.height, ox, oy]); x += im.width + 2; row = max(row, im.height)
    atlas = Image.new('RGBA', (AW, y + row))
    for name, ox, oy, im in pieces: atlas.paste(im, next(r[:2] for r in rects[name] if r[4:] == [ox, oy]))
    atlas.save(os.path.join(HERE, 'face.webp'), 'WEBP', quality=92, alpha_quality=100, method=6)
    Image.open(os.path.join(KIT, kit['layers']['screen_bg'])).convert('RGB').resize((W // 2, H // 2), Image.LANCZOS).save(os.path.join(HERE, 'face_bg.jpg'), quality=90)  # a soft radial glow: no warp needed
    json.dump({'w': W, 'h': H, 'pupil_max': [c * s for c in kit['pupils']['max_offset_px']], 'rects': rects, 'exp': exps},
              open(os.path.join(HERE, 'face.json'), 'w'), separators=(',', ':'))
    print('face.webp', atlas.size, os.path.getsize(os.path.join(HERE, 'face.webp')) // 1024, 'KB;', len(pieces), 'pieces of', len(rects), 'layers')


if os.environ.get('FACE_ONLY') != '1':
    build_glb(lambda n: False, 'googoo.glb')
    build_glb(lambda n: n not in DROP, 'googoo_anims_web.glb', mesh=False)
build_face()

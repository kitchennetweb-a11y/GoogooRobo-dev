"""Design mode server (stdlib only): serves Pash-dev on http://localhost:8770 and opens the room editor (/?design=1).

  python tools/design_server.py [--port 8770] [--no-browser]      (or double-click tools/design_mode.bat)

  GET  /props             the optimized prop GLBs: name, size class (S/M/L), triangles, KB
  GET  /rooms             the room paintings in assets/rooms (painted rooms)
  GET  /models/<f>.glb    from models/, else from the optimized folder (props not published yet)
  POST /save              validates and writes data/layout.json; the old one -> data/layout.backup-<time>.json (last 20 kept)
  POST /publish[?dry=1]   build, commit layout.json + index.html (+ sw.js, + newly used models), pull --rebase, push the
                          test site (devsite main) and origin dev. dry=1 only lists the commands. Never pushes origin main.
Listens on 127.0.0.1 only; POSTs need the X-Design header (a page on another site can't send it).
"""
import argparse, datetime, functools, glob, http.server, json, os, re, shutil, struct, subprocess, sys, threading, webbrowser

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OPT = os.path.join(os.path.expanduser('~'), 'Downloads', 'Pash 3D', 'props', 'optimized')
LAYOUT = os.path.join(ROOT, 'data', 'layout.json')
SKIP = {'room_living_shell'}
ROOMS = ('home', 'play', 'bed', 'library')
OPTIONAL = {'library'}  # a layout saved before the library existed has none: the game then uses its built-in library
BOOK = re.compile(r'^(cat|story):[a-z0-9_]{1,40}$')
MSG = 'Layout: published from Design mode\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'
NAME = re.compile(r'^[a-z0-9_]{1,60}$')
PIC = re.compile(r'^assets/rooms/[a-z0-9_]{1,60}\.(webp|jpg|png)$')
ROOMPICS = os.path.join(ROOT, 'assets', 'rooms')
COLOR = re.compile(r'^#[0-9a-f]{6}$')


def glb_info(path):
    """triangles and longest side of a GLB, from its JSON chunk (no geometry decode)."""
    with open(path, 'rb') as f:
        f.read(12); n, _ = struct.unpack('<I4s', f.read(8)); g = json.loads(f.read(n))
    tris, lo, hi = 0, [1e9] * 3, [-1e9] * 3
    for m in g.get('meshes', []):
        for p in m['primitives']:
            acc = g['accessors'][p['indices']] if 'indices' in p else g['accessors'][p['attributes']['POSITION']]
            tris += acc['count'] // 3
            pa = g['accessors'][p['attributes']['POSITION']]
            if 'min' in pa:
                lo = [min(a, b) for a, b in zip(lo, pa['min'])]; hi = [max(a, b) for a, b in zip(hi, pa['max'])]
    side = max(h - l for l, h in zip(lo, hi)) if hi[0] > -1e9 else 0
    return tris, side


def props_list():
    out, classes = [], {}
    try:
        classes = dict(re.findall(r'^\| `(\w+)\.glb` \|.*?\| ([SML]) (?:small|medium|large)', open(os.path.join(ROOT, 'docs', 'tripo-props.md'), encoding='utf-8').read(), re.M))
    except OSError:
        pass
    for p in sorted(glob.glob(os.path.join(OPT, '*.glb'))):
        name = os.path.basename(p)[:-4]
        if name in SKIP:
            continue
        tris, side = glb_info(p)
        cls = classes.get(name) or ('S' if tris <= 3000 else 'M' if tris <= 8000 else 'L')  # docs/tripo-props.md, else by triangles
        out.append({'name': name, 'class': cls, 'tris': tris, 'kb': os.path.getsize(p) // 1024, 'side': round(side, 3)})
    return out


def num(v, lo, hi, what):
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
        raise ValueError(f'{what}: {v!r} is not a number between {lo} and {hi}')


def room_pics():
    return sorted(f for f in os.listdir(ROOMPICS) if PIC.match('assets/rooms/' + f)) if os.path.isdir(ROOMPICS) else []


def validate_backdrop(r, B):
    """painted room (optional; null = a 3D room). Numbers are 0..1 of the picture unless noted. Unity ignores this."""
    if B is None:
        return
    if not isinstance(B, dict) or set(B) - {'keep', 'portrait', 'landscape'}:
        raise ValueError(f'{r} painting: only keep, portrait, landscape')
    if not all(isinstance(x, str) and NAME.match(x) for x in B.get('keep', [])):
        raise ValueError(f'{r} painting: 3D pieces to keep')
    if not (B.get('portrait') or B.get('landscape')):
        raise ValueError(f'{r} painting: no picture')
    def nums(v, n, lo, hi, what):
        if not isinstance(v, list) or len(v) != n:
            raise ValueError(f'{r} painting {what}: needs {n} numbers')
        for x in v:
            num(x, lo, hi, f'{r} painting {what}')
    for k in ('portrait', 'landscape'):
        P = B.get(k)
        if P is None:
            continue
        if not isinstance(P, dict) or not PIC.match(str(P.get('img', ''))) or not os.path.exists(os.path.join(ROOT, P['img'])):
            raise ValueError(f'{r} {k} picture {P.get("img") if isinstance(P, dict) else P!r}: not a file in assets/rooms')
        nums(P.get('size'), 2, 16, 4096, 'size'); nums(P.get('focus'), 2, 0, 1, 'focus'); nums(P.get('goo'), 3, 0, 1, 'Googoo')
        num(P.get('horizon'), -1, 2, f'{r} {k} eye level')
        for f, lo, hi in (('wall', 0, 1), ('fov', 10, 120), ('zoom', 1, 3)):
            if f in P:
                num(P[f], lo, hi, f'{r} {k} {f}')
        if 'rug' in P:
            nums(P['rug'], 4, 0, 1, 'rug')
        for f, n in (('dust', 4), ('dots', 2)):
            if f in P:
                nums(P[f], n, 0, 1, f)
        if 'beam' in P:
            nums(P['beam'], 6, -360, 360, 'sunbeam')
        cells = P.get('cells', [])
        if not isinstance(cells, list) or len(cells) > 30:
            raise ValueError(f'{r} {k}: shelf compartments')
        for c in cells:
            nums(c, 4, 0, 1, 'compartment')
            if c[2] <= c[0] or c[3] <= c[1]:
                raise ValueError(f'{r} {k}: a compartment has no size')
        for pid, pt in (P.get('place') or {}).items():
            if not NAME.match(pid):
                raise ValueError(f'{r} {k}: place of {pid!r}')
            nums(pt, 2, 0, 1, f'place of {pid}')
        for l in P.get('lamps', []):
            nums(l, 3, 0, 1, 'lamp')
        for t in P.get('taps', []):
            if not isinstance(t, dict) or not re.match(r'^w_[a-z0-9_]{1,40}$', str(t.get('w', ''))):
                raise ValueError(f'{r} {k}: tap zone word')
            nums(t.get('r'), 4, 0, 1, 'tap zone')
        fg = P.get('fg')
        if fg is not None:
            if not isinstance(fg, dict) or fg.get('at') not in ('tl', 'tr', 'bl', 'br'):
                raise ValueError(f'{r} {k}: foreground corner')
            nums(fg.get('crop'), 4, 0, 1, 'foreground crop'); num(fg.get('h'), 0.05, 1.5, f'{r} {k} foreground size')
        L = P.get('light')
        if L is not None:
            if not isinstance(L, dict):
                raise ValueError(f'{r} {k}: light')
            for f in ('shadow', 'exp'):
                if f in L:
                    num(L[f], 0, 3, f'{r} {k} light {f}')
            for f, n in (('sun', 2), ('fill', 2), ('hemi', 3)):
                if f in L and (not isinstance(L[f], list) or len(L[f]) != n or not all(COLOR.match(str(c)) for c in L[f][:n - 1])):
                    raise ValueError(f'{r} {k} light {f}')
                if f in L:
                    num(L[f][-1], 0, 5, f'{r} {k} light {f}')
            if 'dir' in L:
                nums(L['dir'], 3, -50, 50, 'light direction')


def validate(L):
    """raises ValueError with a plain message if the layout is not one the game can use."""
    if not isinstance(L, dict) or not isinstance(L.get('rooms'), dict) or not isinstance(L.get('ui'), dict):
        raise ValueError('layout needs "rooms" and "ui"')
    ids = set()
    for r in ROOMS:
        R = L['rooms'].get(r)
        if R is None and r in OPTIONAL:
            continue
        if not isinstance(R, dict):
            raise ValueError(f'room {r} is missing')
        if 'books' in R:  # library: which books stand on the big shelf / the small shelf (bin), in order
            B, seen = R['books'], set()
            if not isinstance(B, dict) or set(B) - {'big', 'small'}:
                raise ValueError(f'{r} books: only "big" and "small" lists')
            for k, v in B.items():
                if not isinstance(v, list) or not all(isinstance(x, str) and BOOK.match(x) for x in v):
                    raise ValueError(f'{r} books on the {k} shelf')
                if seen & set(v) or len(set(v)) != len(v):
                    raise ValueError(f'{r}: a book is on a shelf twice')
                seen |= set(v)
        validate_backdrop(r, R.get('backdrop'))
        W = R.get('walls', {})
        for k in ('left', 'right', 'back'):
            num(W.get(k), -30, 30, f'{r} wall {k}')
        if W['right'] - W['left'] < 4:
            raise ValueError(f'{r}: the room is too narrow')
        for k in ('color', 'floor'):
            if not COLOR.match(str(W.get(k, ''))):
                raise ValueError(f'{r} {k} colour {W.get(k)!r}')
        for k, v in (W.get('floorRect') or {}).items():
            if k not in ('left', 'right', 'back', 'front'):
                raise ValueError(f'{r} floor {k}')
            num(v, -40, 40, f'{r} floor {k}')
        G = R.get('googoo') or {}
        for part in (G, G.get('portrait') or {}):
            for k, v in part.items():
                if k == 'portrait':
                    continue
                if k not in ('x', 'z', 'ry', 's'):
                    raise ValueError(f'{r} googoo {k}')
                num(v, 0.2 if k == 's' else -40, 4 if k == 's' else 40, f'{r} googoo {k}')
        for grp, V in (R.get('camera') or {}).items():
            if grp not in ('phone', 'wide'):
                raise ValueError(f'{r} camera {grp}')
            for k in ('zoom', 'height', 'yaw', 'pitch'):
                num(V.get(k), -180, 180, f'{r} camera {k}')
        for p in R.get('props', []):
            if not NAME.match(str(p.get('id', ''))) or p['id'] in ids:
                raise ValueError(f'prop id {p.get("id")!r} is bad or used twice')
            ids.add(p['id'])
            if p.get('on') is not None and not NAME.match(str(p['on'])):  # "sits on" another piece (id) or null
                raise ValueError(f'{p["id"]} sits on {p["on"]!r}')
            if p.get('builtin'):  # pieces made in code (book, star mobile): place only
                if p['id'] not in ('book', 'star'):
                    raise ValueError(f'{p["id"]} is not a built-in piece')
                for k in ('x', 'y', 'z', 'ry'):
                    if k in p:
                        num(p[k], -40, 40, f'{p["id"]} {k}')
                continue
            f = str(p.get('file', ''))
            if not NAME.match(f) or not (os.path.exists(os.path.join(ROOT, 'models', f + '.glb')) or os.path.exists(os.path.join(OPT, f + '.glb'))):
                raise ValueError(f'prop {p["id"]}: no model file {f!r}')
            num(p.get('k'), 0.01, 5, f'{p["id"]} size')
            for k in ('x', 'y', 'z', 'ry', 'flatten'):
                if k in p:
                    num(p[k], -40, 40, f'{p["id"]} {k}')
            for k, v in (p.get('portrait') or {}).items():
                if k not in ('k', 'x', 'y', 'z', 'ry'):
                    raise ValueError(f'{p["id"]} portrait {k}')
                num(v, -40, 40, f'{p["id"]} portrait {k}')
            if p.get('wall') not in (None, 'back', 'left'):
                raise ValueError(f'{p["id"]} wall {p.get("wall")!r}')
    U = L['ui']
    num(U.get('size'), 0.5, 2, 'button size')
    if U.get('shape') not in ('round', 'square'):
        raise ValueError('button shape')
    T, N = U.get('top') or {}, U.get('nav') or {}
    if U.get('style', 'jelly') not in ('jelly', 'classic'):
        raise ValueError('button style')
    for grp, F in (U.get('free') or {}).items():  # free placement: % from the nearest screen edges
        if grp not in ('phone', 'wide'):
            raise ValueError(f'free placement group {grp}')
        for b, v in F.items():
            if not re.match(r'^(b[A-Za-z]+|score|parentBtn|tab-(home|play|bed|library|say|book))$', b) or v.get('ax') not in ('l', 'r') or v.get('ay') not in ('t', 'b'):
                raise ValueError(f'free placement of {b}')
            num(v.get('x'), -5, 100, f'{b} x'); num(v.get('y'), -5, 100, f'{b} y')
    for part, ids_ok in ((T, ('score', 'bTalk', 'parentBtn')), (N, ('home', 'play', 'bed', 'library', 'say', 'book'))):
        if 'size' in part:
            num(part['size'], 0.5, 2, 'top/tab size')
        if part.get('shape', 'round') not in ('round', 'square'):
            raise ValueError('top/tab shape')
        for k in ('order', 'hide'):
            if not all(x in ids_ok for x in part.get(k, [])):
                raise ValueError(f'top/tab {k}')
        for x, c in (part.get('colors') or {}).items():
            if x not in ids_ok or not COLOR.match(str(c)):
                raise ValueError(f'colour of {x}')
    if 'parentBtn' in T.get('hide', []) or any(r in N.get('hide', []) for r in ROOMS):
        raise ValueError('the gear and the room tabs must stay')
    for b, v in U.get('buttons', {}).items():
        if not re.match(r'^b[A-Za-z]+$', b) or not COLOR.match(str(v.get('color', ''))):
            raise ValueError(f'button {b} colour')
    for s, v in U.get('screens', {}).items():
        for side in ('left', 'right'):
            if not all(isinstance(b, str) and re.match(r'^b[A-Za-z]+$', b) for b in v.get(side, [])):
                raise ValueError(f'buttons of {s}')


def save(L):
    validate(L)
    os.makedirs(os.path.dirname(LAYOUT), exist_ok=True)
    if os.path.exists(LAYOUT):
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3]
        shutil.copy2(LAYOUT, os.path.join(os.path.dirname(LAYOUT), f'layout.backup-{stamp}.json'))
        for old in sorted(glob.glob(os.path.join(os.path.dirname(LAYOUT), 'layout.backup-*.json')))[:-20]:
            os.remove(old)
    tmp = LAYOUT + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(L, indent=1, ensure_ascii=False) + '\n')
    os.replace(tmp, LAYOUT)


def git(*a):
    return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')


def publish(dry):
    """build, commit only the layout files, push to the test site. Returns (ok, log text)."""
    log = []
    br = git('branch', '--show-current').stdout.strip()
    if br != 'dev':
        return False, f'Not on the dev branch (on {br!r}); nothing done.'
    if git('diff', '--quiet', 'HEAD', '--', 'src_pash-robot.html').returncode:
        if dry:
            log.append('NOTE: src_pash-robot.html has uncommitted code changes; a real publish would stop here.')
        else:
            return False, ('src_pash-robot.html has code changes that are not committed yet (another session is working on it). '
                           'Publishing now would put them on the test site, so nothing was done. Ask Claude to commit them first.')
    L = json.load(open(LAYOUT, encoding='utf-8'))
    used = sorted({p['file'] for R in L['rooms'].values() for p in R.get('props', []) if p.get('file')})
    new = [f for f in used if not os.path.exists(os.path.join(ROOT, 'models', f + '.glb'))]
    paths = ['data/layout.json', 'index.html', 'sw.js'] + [f'models/{f}.glb' for f in new]
    steps = [[sys.executable, 'tools/build.py']] + [['copy', os.path.join(OPT, f + '.glb'), f'models/{f}.glb'] for f in new] + [
        ['git', 'add', '--', *paths], ['git', 'commit', '-m', MSG, '--', *paths],
        ['git', 'pull', '--rebase', 'origin', 'dev'], ['git', 'push', 'devsite', 'dev:main'], ['git', 'push', 'origin', 'dev']]
    for s in steps:
        assert not (s[:2] == ['git', 'push'] and s[2] == 'origin' and 'main' in s[3]), 'never push origin main'
        log.append('$ ' + ' '.join(f'"{x}"' if ' ' in x or '\n' in x else x for x in s))
        if dry:
            continue
        if s[0] == 'copy':
            shutil.copy2(s[1], os.path.join(ROOT, s[2])); continue
        if s[:2] == ['git', 'commit'] and not git('diff', '--cached', '--quiet', '--', *paths).returncode:
            log.append('(nothing new to commit: the layout is already published or unchanged)'); continue
        r = subprocess.run(s, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        log.append((r.stdout + r.stderr).strip())
        if r.returncode:
            log.append(f'FAILED (exit {r.returncode}). Stopped here; nothing after this step was run.')
            return False, '\n'.join(log)
    if dry:
        log.insert(0, 'DRY RUN: these commands would run (nothing was changed):')
    return True, '\n'.join(log)


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def reply(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/props':
            return self.reply(200, props_list())
        if path == '/rooms':
            return self.reply(200, room_pics())
        if path == '/data/layout.json' and os.path.abspath(LAYOUT) != os.path.join(ROOT, 'data', 'layout.json'):  # --layout (tests)
            b = open(LAYOUT, 'rb').read()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        m = re.match(r'^/models/([a-z0-9_]+)\.glb$', path)
        if m and not os.path.exists(os.path.join(ROOT, 'models', m[1] + '.glb')) and os.path.exists(os.path.join(OPT, m[1] + '.glb')):
            b = open(os.path.join(OPT, m[1] + '.glb'), 'rb').read()
            self.send_response(200); self.send_header('Content-Type', 'model/gltf-binary'); self.send_header('Content-Length', str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        super().do_GET()

    def do_POST(self):
        origin = self.headers.get('Origin', '')
        if self.headers.get('X-Design') != '1' or (origin and not re.match(r'^http://(localhost|127\.0\.0\.1)(:\d+)?$', origin)):
            return self.reply(403, {'ok': False, 'error': 'not from Design mode'})
        path, _, q = self.path.partition('?')
        try:
            if path == '/save':
                n = int(self.headers.get('Content-Length', 0))
                save(json.loads(self.rfile.read(n)))
                return self.reply(200, {'ok': True, 'time': datetime.datetime.now().strftime('%H:%M:%S')})
            if path == '/publish':
                with LOCK:
                    ok, out = publish('dry=1' in q)
                return self.reply(200, {'ok': ok, 'output': out})
        except Exception as e:  # bad layout or I/O error: tell the editor, change nothing
            return self.reply(400, {'ok': False, 'error': str(e)})
        self.reply(404, {'ok': False, 'error': 'unknown'})


LOCK = threading.Lock()


def selftest():
    import copy
    L = json.load(open(LAYOUT, encoding='utf-8')); validate(L)
    for bad in (lambda x: x['rooms']['home']['walls'].update(left='a'), lambda x: x['rooms']['bed']['props'].append({'id': 'bed', 'file': 'bedroom_bed', 'k': 1}),
                lambda x: x['rooms']['play']['props'][0].update(file='../x'), lambda x: x['ui'].update(shape='star')):
        y = copy.deepcopy(L); bad(y)
        try:
            validate(y); raise AssertionError('bad layout passed')
        except ValueError:
            pass
    y = copy.deepcopy(L); y['rooms'].pop('library', None); validate(y)  # no library room: still valid
    good = {'keep': ['teddy'], 'portrait': {'img': 'assets/rooms/play_portrait.webp', 'size': [1056, 1440], 'focus': [.5, .6], 'horizon': .44, 'wall': .62, 'goo': [.5, .7, .25],
            'rug': [.5, .7, .3, .07], 'cells': [[.1, .1, .2, .2]], 'place': {'teddy': [.3, .7]}, 'taps': [{'r': [0, 0, .1, .1], 'w': 'w_car'}]}}
    y = copy.deepcopy(L); y['rooms']['play']['backdrop'] = good; validate(y); y['rooms']['play']['backdrop'] = None; validate(y)
    for bad in (lambda b: b['portrait'].update(img='../x.webp'), lambda b: b['portrait'].update(img='assets/rooms/nope.webp'), lambda b: b['portrait'].update(goo=[.5, 2, .2]),
                lambda b: b['portrait'].update(cells=[[.3, .3, .2, .4]]), lambda b: b.update(extra=1), lambda b: b['portrait'].update(taps=[{'r': [0, 0, 1, 1], 'w': 'x;y'}])):
        y = copy.deepcopy(L); b = copy.deepcopy(good); bad(b); y['rooms']['play']['backdrop'] = b
        try:
            validate(y); raise AssertionError('bad painting passed')
        except ValueError:
            pass
    assert 'library_portrait.webp' in room_pics()
    for bad in ({'big': ['cat:animals'], 'small': ['cat:animals']}, {'big': ['x']}, {'top': []}):
        y = copy.deepcopy(L); y['rooms'].setdefault('library', copy.deepcopy(L['rooms']['home']))['books'] = bad
        try:
            validate(y); raise AssertionError('bad books passed')
        except ValueError:
            pass
    assert any(p['name'] == 'living_sofa' and p['tris'] > 8000 for p in props_list())
    ok, out = publish(True); print(out); assert 'origin main' not in out and 'devsite dev:main' in out
    print('selftest ok')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8770); ap.add_argument('--no-browser', action='store_true')
    ap.add_argument('--selftest', action='store_true'); ap.add_argument('--layout', help='edit this layout file instead of data/layout.json (tests)'); a = ap.parse_args()
    if a.layout:
        LAYOUT = os.path.abspath(a.layout)
    if a.selftest:
        sys.exit(selftest())
    http.server.ThreadingHTTPServer.allow_reuse_address = False  # on Windows reuse would let a second copy share the port
    try:
        srv = http.server.ThreadingHTTPServer(('127.0.0.1', a.port), functools.partial(H, directory=ROOT))
    except OSError:
        print(f'Design mode is already running (port {a.port} is in use): use the browser tab that is open, or close the other black window first.')
        if not a.no_browser:
            webbrowser.open(f'http://localhost:{a.port}/?design=1')
        sys.exit(1)
    url = f'http://localhost:{a.port}/?design=1'
    print(f'Design mode: {url}  (keep this window open; close it to stop)')
    if not a.no_browser:
        threading.Timer(.5, webbrowser.open, [url]).start()
    srv.serve_forever()

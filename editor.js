// Googoo Robo Design mode: a room editor on top of the real game. Loaded by the game page only with ?design=1
// (start it with tools/design_mode.bat, which runs tools/design_server.py for Save and Publish).
// This page becomes the editor; the real game runs in an iframe sized like a phone or tablet, and the editor
// drives it through the game's own globals (PROPS, furnGroup, applyLayout, loadProp, ...). Everything is saved to data/layout.json.
(() => {
'use strict';
// the copy of the game in this page stops (the one in the iframe is the one we edit)
try { window.loop = function () {}; cancelAnimationFrame(raf); renderer.forceContextLoss(); renderer.domElement.remove(); } catch (e) {}

const ROOMS = ['home', 'play', 'bed'], ROOM_NAME = { home: 'Living room', play: 'Play room', bed: 'Bedroom' };
const SCREEN_NAME = { home: 'Living room', play: 'Play room', bed: 'Bedroom', night: 'Bedroom, lamp off', say: 'Say it', book: 'Picture book' };
const DEVICES = { up: ['iPhone upright', 390, 844], side: ['iPhone sideways', 844, 390], small: ['Small phone', 360, 640], ipad: ['iPad', 820, 1180] };
// these replace a built-in piece of the room: removing them would bring the old piece back, so they are hidden instead
const BUILTIN = ['window', 'tv', 'picture', 'chair', 'carpet', 'toybox', 'teddy', 'blocks', 'drum', 'kite', 'bed', 'lamp', 'nightstand', 'rug'];
const PRIM = ['bed', 'lamp', 'book', 'chair', 'tv', 'picture', 'shelf', 'teddy', 'blocks', 'drum', 'kite', 'nightstand', 'star', 'ball'];
const LIMIT = { calls: [80, 100], tris: [150e3, 200e3], mb: [64, 96] }; // docs/gpu-budget.md: target, hard limit
const CDN = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/';
const DEG = Math.PI / 180;

let L = null, saved = '', undo = [], redo = [], lastKey = '', lastT = 0;
let W = null, X = null, RBH = 1, mode = 'props', sel = null, selWall = null, selBtn = null, ptMode = false, clip = null;
let free = false, orbit = null, freeCam = null, device = 'up', chip = 'all', query = '', propsList = [], serverOk = false;
const inflight = new Set();

// ---------- editor page ----------
document.title = 'Googoo Robo: Design mode';
const css = document.createElement('style');
css.textContent = `
body>*:not(#ed){display:none!important}
body{background:#e9edf2!important;overflow:hidden;user-select:none;-webkit-user-select:none;touch-action:auto!important}
#ed{position:fixed;inset:0;display:grid;grid-template-columns:272px 1fr 300px;grid-template-rows:54px 1fr 34px;font:14px/1.4 system-ui,"Segoe UI",sans-serif;color:#1d2433}
#ed :is(button,select,input){font:inherit}
#ed header{grid-column:1/-1;display:flex;align-items:center;gap:6px;padding:0 10px;background:#fff;border-bottom:1px solid #d5dbe3;overflow-x:auto;white-space:nowrap}
#ed header h1{font:800 16px system-ui,sans-serif;margin:0 8px 0 4px;white-space:nowrap}
#ed .sep{width:1px;height:28px;background:#dde2ea;margin:0 4px;flex:none}
.eb{color:#1d2433;border:1px solid #cdd4de;background:#fff;border-radius:8px;padding:5px 10px;cursor:pointer;white-space:nowrap;line-height:1.3}
.eb:hover{background:#f2f5f9}.eb:disabled{opacity:.45;cursor:default}
.eb.on{background:#1d2433;border-color:#1d2433;color:#fff}
.eb.go{background:#2563eb;border-color:#2563eb;color:#fff}.eb.pub{background:#16a34a;border-color:#16a34a;color:#fff}
.eb.warn{color:#b42318;border-color:#f1b5ae}
.grp{display:flex;gap:0}.grp .eb{border-radius:0;margin-left:-1px}.grp .eb:first-child{border-radius:8px 0 0 8px;margin:0}.grp .eb:last-child{border-radius:0 8px 8px 0}
#ed aside{background:#fff;overflow:auto;padding:12px}
#ed aside.l{border-right:1px solid #d5dbe3}#ed aside.r{border-left:1px solid #d5dbe3}
#ed h2{font:700 13px system-ui,sans-serif;text-transform:uppercase;letter-spacing:.04em;color:#5b6576;margin:4px 0 8px}
#ed .hint{color:#5b6576;font-size:13px;margin:6px 0 10px}
#ed main{position:relative;overflow:hidden}
#fbox{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%)}
#frame{border:0;position:absolute;left:0;top:0;transform-origin:0 0;border-radius:14px;box-shadow:0 10px 30px #1d243333;background:#e9dccb}
#ed footer{grid-column:1/-1;display:flex;align-items:center;gap:14px;padding:0 12px;background:#fff;border-top:1px solid #d5dbe3;font-size:13px;white-space:nowrap;overflow:hidden}
#status{flex:1;overflow:hidden;text-overflow:ellipsis}#status.dirty{color:#b45309;font-weight:600}
.meter{display:flex;align-items:center;gap:5px}.dot{width:10px;height:10px;border-radius:50%;background:#aaa}
.dot.g{background:#16a34a}.dot.a{background:#f59e0b}.dot.r{background:#dc2626}
#search{width:100%;box-sizing:border-box;border:1px solid #cdd4de;border-radius:8px;padding:6px 10px;margin-bottom:8px}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px}.chips .eb{padding:3px 9px;font-size:13px;border-radius:14px}
.prow{display:flex;align-items:center;gap:8px;padding:5px 6px;border-radius:8px}
.prow .ic{font-size:20px;width:26px;text-align:center;flex:none}.prow .nm{flex:1;min-width:0}.prow .nm small{display:block;color:#7a8394;font-size:11.5px}
.prow .ib{border:0;background:none;cursor:pointer;font-size:16px;padding:3px 5px;border-radius:6px}.prow .ib:hover{background:#e8edf4}
.inst{margin-left:34px;cursor:pointer}.inst:hover{background:#f2f5f9}.inst.sel{background:#dbe7ff}.inst.off .nm{opacity:.5;text-decoration:line-through}
.field{display:grid;grid-template-columns:96px 1fr 64px;align-items:center;gap:8px;margin:8px 0}
.field label{color:#3b4455}.field input[type=number]{width:64px;box-sizing:border-box;border:1px solid #cdd4de;border-radius:6px;padding:3px 5px}
.field input[type=range]{width:100%}.row{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.check{display:flex;gap:8px;align-items:flex-start;margin:10px 0}.check input{margin-top:3px}
.tabs{display:flex;margin-bottom:12px}.tabs .eb{flex:1}
.blist{margin:6px 0}.brow{display:flex;align-items:center;gap:8px;padding:3px 4px;border-radius:8px}.brow.sel{background:#dbe7ff}
.brow .em{font-size:18px;width:24px;text-align:center}.brow .nm{flex:1}
.brow input[type=color],.field input[type=color]{width:38px;height:26px;border:1px solid #cdd4de;border-radius:6px;padding:0;background:#fff}
#modal{position:fixed;inset:0;background:#1d243388;display:grid;place-items:center;z-index:10}
#modal>div{background:#fff;border-radius:14px;padding:18px;width:min(720px,90vw);max-height:80vh;overflow:auto}
#modal pre{white-space:pre-wrap;font:12px/1.45 ui-monospace,Consolas,monospace;background:#f4f6f9;padding:10px;border-radius:8px}
`;
document.head.appendChild(css);
const ed = document.createElement('div'); ed.id = 'ed';
ed.innerHTML = `
<header>
 <h1>🛠️ Design mode</h1>
 <div class="grp" id="rooms">${ROOMS.map(r => `<button class="eb" data-room="${r}">${ROOM_NAME[r]}</button>`).join('')}</div>
 <span class="sep"></span>
 <select class="eb" id="device" title="Screen size">${Object.entries(DEVICES).map(([k, d]) => `<option value="${k}">${d[0]} (${d[1]}x${d[2]})</option>`).join('')}</select>
 <div class="grp"><button class="eb on" id="gameCam" title="The camera the child sees">Game camera</button><button class="eb" id="freeCam" title="Turn around the room with the mouse">Free camera</button></div>
 <span class="sep"></span>
 <button class="eb" id="undo" title="Undo (Ctrl+Z)">↶ Undo</button><button class="eb" id="redo" title="Redo (Ctrl+Y)">↷ Redo</button>
 <button class="eb go" id="save" title="Save (Ctrl+S)">💾 Save</button>
 <button class="eb warn" id="reset" title="Put this room back to how it was at the last save">Reset room</button>
 <button class="eb pub" id="publish" title="Put the saved layout on the test site">🚀 Publish to test site</button>
</header>
<aside class="l">
 <div class="tabs grp"><button class="eb on" data-mode="props">🪑 Props</button><button class="eb" data-mode="walls">🧱 Walls</button><button class="eb" data-mode="buttons">🔘 Buttons</button></div>
 <div id="left"></div>
</aside>
<main id="main"><div id="fbox"><iframe id="frame" title="Game preview"></iframe></div></main>
<aside class="r"><div id="right"></div></aside>
<footer><span id="status">Loading the game…</span>
 <span class="meter" title="Draw calls this frame (budget 100)"><span class="dot" id="dCalls"></span><span id="mCalls">calls –</span></span>
 <span class="meter" title="Triangles this frame (budget 200k)"><span class="dot" id="dTris"></span><span id="mTris">tris –</span></span>
 <span class="meter" title="Estimated texture memory (target 64 MB, max 96 MB)"><span class="dot" id="dMb"></span><span id="mMb">textures –</span></span></footer>`;
document.body.appendChild(ed);
const $ = id => document.getElementById(id), frame = $('frame');

// ---------- helpers ----------
const clone = o => JSON.parse(JSON.stringify(o));
const room = () => X ? W.eval('curRoom') : 'home';
const screenKey = () => { const s = W.eval('scr'); return s === 'bed' && !W.eval('lightsOn') ? 'night' : s; };
const isPortrait = () => W && W.innerWidth < W.innerHeight;
const sq = () => Math.min(1, (isPortrait() ? .3 : .35) + W.innerWidth / W.innerHeight * .75); // the game's portrait squeeze (resize())
const pretty = f => f.replace(/^(living|bedroom|toy|farm)_/, '').replace(/_/g, ' ');
const cat = f => /^(toy|farm)_/.test(f) ? 'toys' : /(bed|nightstand|wardrobe|sofa|armchair|bookshelf|tv_cabinet|korsi|coffee_table|door|box)$/.test(f) ? 'furniture' : 'decor';
const ICON = { toys: '🧸', furniture: '🛋️', decor: '🖼️' };
const propOf = id => { for (const r of ROOMS) { const p = L.rooms[r].props.find(p => p.id === id); if (p) return p; } return null; };
const grp = id => X && X.furnGroup.children.find(g => g.userData.furn === id && g.userData.m);
const usePt = () => ptMode && isPortrait();
const r2 = v => Math.round(v * 1000) / 1000;
function status(t, cls) { const s = $('status'); s.textContent = t; s.className = cls || ''; }
function dirtyStatus() { const d = JSON.stringify(L) !== saved; if (d) status('● Unsaved changes', 'dirty'); return d; }

// ---------- history ----------
function change(fn, key, kind = 'props') {
  const now = Date.now();
  if (!(key && key === lastKey && now - lastT < 900)) { undo.push(JSON.stringify(L)); if (undo.length > 300) undo.shift(); redo = []; }
  lastKey = key; lastT = now; fn(); apply(kind);
}
function restore(json) { L = JSON.parse(json); lastKey = ''; apply('all'); }
function doUndo() { if (!undo.length) return; redo.push(JSON.stringify(L)); restore(undo.pop()); }
function doRedo() { if (!redo.length) return; undo.push(JSON.stringify(L)); restore(redo.pop()); }

// ---------- apply the layout to the game in the iframe ----------
function apply(kind) {
  if (!X) return;
  if (kind === 'all' || kind === 'ui') W.applyLayout(L);
  else if (kind === 'walls') { W.applyWalls(room()); }
  syncProps();
  if (kind !== 'props' || !sel) renderLeft();
  if (kind === 'all') renderRight(); // panels rebuild only on big changes, so a slider being dragged keeps working
  dirtyStatus(); $('undo').disabled = !undo.length; $('redo').disabled = !redo.length;
}
// loaded prop groups follow L: size, place, turn, portrait values, shadow, hidden; removed ones go, new ones load
function syncProps() {
  const cur = room(), want = new Map();
  for (const r of ROOMS) for (const p of L.rooms[r].props) want.set(p.id, [p, r]);
  for (const g of [...X.furnGroup.children]) {
    const u = g.userData; if (!u.m) continue;
    const w = want.get(u.furn); if (!w) { X.furnGroup.remove(g); inflight.delete(u.furn); continue; }
    const [p, r] = w, sc = RBH * p.k;
    u.base.set(sc, sc * (p.flatten || 1), sc); u.y0 = p.y || 0; u.ry0 = p.ry || 0; u.pt = p.portrait; u.nosq = p.noSqueeze ? 1 : 0; u.off = p.hidden ? 1 : 0; u.room = r;
    if (!u.bb1) { const s0 = u.m.scale.clone(), par = u.m.parent; par.remove(u.m); u.m.scale.set(1, 1, 1); u.m.updateMatrixWorld(true); u.bb1 = new X.THREE.Box3().setFromObject(u.m); u.m.scale.copy(s0); par.add(u.m); }
    const WL = L.rooms[r].walls;
    u.x0 = p.wall === 'left' ? WL.left - u.bb1.min.z * sc + .03 : p.x ?? u.x0;
    u.z0 = p.wall === 'back' ? WL.back - u.bb1.min.z * sc + .03 : p.z ?? u.z0;
    u.m.traverse(o => { if (o.isMesh) o.castShadow = !!p.castShadow; });
    g.visible = r === cur && !p.hidden;
  }
  for (const p of L.rooms[cur].props) if (!grp(p.id) && !inflight.has(p.id) && X.PROPS[p.id]) { inflight.add(p.id); W.loadProp(p.id); }
  W.roomProps(cur); W.placeProps(sq());
  if (free) restoreFree();
}

// ---------- wait for the game in the iframe ----------
frame.src = 'index.html?frame=1';
frame.addEventListener('load', async () => {
  W = frame.contentWindow;
  for (let i = 0; i < 300 && !(W.__ggReady && typeof W.applyLayout === 'function'); i++) await new Promise(r => setTimeout(r, 100));
  await W.eval('LAYOUT');
  X = W.eval('({THREE,scene,camera,renderer,furnGroup,PROPS,WALLS,back,wallSides,RB0})');
  RBH = X.RB0.h;
  try { L = await (await fetch('data/layout.json', { cache: 'no-store' })).json(); } catch (e) { L = null; }
  if (!L || !L.rooms) { status('Could not read data/layout.json', 'dirty'); return; }
  saved = JSON.stringify(L);
  // start the game without the start screen (no sound in Design mode); the room's props load
  W.eval("document.getElementById('start').hidden=true;document.getElementById('hint').hidden=true;propsOn=true;loadProps(curRoom)");
  for (const p of L.rooms[room()].props) inflight.add(p.id);
  setupFrame(); apply('all'); setDevice(device); renderTop();
  status(serverOk ? 'Ready. Click a piece in the room to move it.' : 'Design server is not running (start tools/design_mode.bat): you can try things but Save and Publish will not work.', serverOk ? '' : 'dirty');
  setInterval(tick, 250); setInterval(budget, 1500);
});
fetch('props').then(r => r.json()).then(list => { propsList = list; serverOk = true; renderLeft(); }).catch(() => { serverOk = false; });

// ---------- inside the iframe: overlay for picking, button dragging, free camera ----------
let ov, box;
function setupFrame() {
  const d = W.document, st = d.createElement('style');
  st.textContent = `#edOv{position:fixed;inset:0;z-index:50;cursor:default}#edOv.grab{cursor:grabbing}
    body.edBtns .col{z-index:60}body.edBtns .col .rb{cursor:grab}.edSel{outline:3px dashed #2563eb!important;outline-offset:4px}
    #parentBtn,#top,#surp{pointer-events:none}`;
  d.head.appendChild(st);
  ov = d.createElement('div'); ov.id = 'edOv'; d.body.appendChild(ov);
  box = new X.THREE.BoxHelper(undefined, 0x2563eb); box.visible = false; box.material.depthTest = false; box.renderOrder = 999; X.scene.add(box);
  ov.addEventListener('pointerdown', onDown, true);
  ov.addEventListener('wheel', onWheel, { capture: true, passive: false });
  W.addEventListener('pointermove', onMove); W.addEventListener('pointerup', onUp);
  W.addEventListener('keydown', onKey);
  // buttons mode: rail buttons drag; their game actions are blocked
  d.addEventListener('pointerdown', onBtnDown, true);
  d.addEventListener('click', e => { if (e.target.closest && e.target.closest('.col .rb')) { e.stopImmediatePropagation(); e.preventDefault(); } }, true);
  // the game's resize() re-aims the camera: in free camera mode keep ours
  const orig = W.resize;
  W.resize = function () { orig(); if (free) restoreFree(); };
  W.addEventListener('resize', () => { if (free) restoreFree(); fit(); });
}
const ray = () => new X.THREE.Raycaster();
function ndc(e) { return new X.THREE.Vector2(e.clientX / W.innerWidth * 2 - 1, -(e.clientY / W.innerHeight) * 2 + 1); }
function pickProp(e) {
  const rc = ray(); rc.setFromCamera(ndc(e), X.camera);
  const cands = X.furnGroup.children.filter(g => g.visible && g.userData.m && propOf(g.userData.furn));
  const h = rc.intersectObjects(cands.map(g => g.userData.m), true)[0]; // the model itself, not the game's padded tap box (sized before the portrait shrink)
  if (h) { let o = h.object; while (o.parent !== X.furnGroup) o = o.parent; return o; }
  let best = null, bd = 1e9; // flat rugs ignore rays in the game: fall back to their boxes
  for (const g of cands.filter(g => propOf(g.userData.furn).flatten)) { const b = new X.THREE.Box3().setFromObject(g), p = rc.ray.intersectBox(b, new X.THREE.Vector3()); if (p) { const dd = p.distanceTo(rc.ray.origin); if (dd < bd) { bd = dd; best = g; } } }
  return best;
}
function planeHit(e, plane) { const rc = ray(); rc.setFromCamera(ndc(e), X.camera); return rc.ray.intersectPlane(plane, new X.THREE.Vector3()); }

let drag = null;
function onDown(e) {
  if (mode === 'buttons') return;
  const T = X.THREE;
  if (mode === 'walls') {
    const rc = ray(); rc.setFromCamera(ndc(e), X.camera);
    const ws = [X.back, ...X.wallSides], h = rc.intersectObjects(ws)[0];
    if (!h) { if (!free) { selWall = null; renderRight(); showBox(); } return; }
    selWall = h.object === X.back ? 'back' : h.object === X.wallSides[0] ? 'left' : 'right'; renderRight(); showBox();
    drag = { wall: selWall, key: 'wall' + Date.now(), plane: new T.Plane(new T.Vector3(0, 1, 0), 0) };
    e.stopImmediatePropagation(); ov.setPointerCapture(e.pointerId); ov.classList.add('grab'); return;
  }
  const g = pickProp(e);
  if (!g) { if (!free) select(null); return; }
  select(g.userData.furn); e.stopImmediatePropagation();
  const p = propOf(sel), y = g.position.y;
  if (e.shiftKey) { // Shift+drag: height
    const n = new T.Vector3(); X.camera.getWorldDirection(n); n.y = 0; n.normalize();
    const plane = new T.Plane().setFromNormalAndCoplanarPoint(n, g.position), h = planeHit(e, plane);
    drag = { id: sel, key: 'h' + Date.now(), plane, height: true, dy: h ? h.y - y : 0 };
  } else {
    const plane = new T.Plane(new T.Vector3(0, 1, 0), -y), h = planeHit(e, plane);
    drag = { id: sel, key: 'm' + Date.now(), plane, ox: h ? h.x - g.position.x : 0, oz: h ? h.z - g.position.z : 0, z0: g.position.z, x0: g.position.x, wall: p.wall };
  }
  ov.setPointerCapture(e.pointerId); ov.classList.add('grab');
}
function onMove(e) {
  if (!drag) return onBtnMove(e);
  const h = planeHit(e, drag.plane); if (!h) return;
  if (drag.wall && !drag.id) { // a wall
    const r = room(), v = drag.wall === 'back' ? Math.min(-1.5, Math.max(-14, h.z)) : drag.wall === 'left' ? Math.min(-2, Math.max(-16, h.x)) : Math.max(2, Math.min(16, h.x));
    return change(() => { L.rooms[r].walls[drag.wall] = r2(v); }, drag.key, 'walls');
  }
  const p = propOf(drag.id);
  if (drag.height) return change(() => setVal(p, 'y', Math.max(-.5, h.y - drag.dy)), drag.key);
  let x = h.x - drag.ox, z = h.z - drag.oz;
  // pieces on a wall slide along it until pulled more than 0.8 away
  if (drag.wall === 'back' && Math.abs(z - drag.z0) < .8) z = null;
  if (drag.wall === 'left' && Math.abs(x - drag.x0) < .8) x = null;
  change(() => { if (x !== null) setVal(p, 'x', x); if (z !== null) setVal(p, 'z', z); }, drag.key);
}
function onUp() { if (drag) { drag = null; ov.classList.remove('grab'); renderLeft(); } onBtnUp(); }
function onWheel(e) {
  if (mode !== 'props' || !sel) return;
  e.preventDefault(); e.stopImmediatePropagation(); resizeSel(e.deltaY < 0 ? 1.05 : 1 / 1.05);
}
function resizeSel(f) { const p = propOf(sel); if (p) change(() => setVal(p, 'k', view(p).k * f), 'size' + sel); }

// values the current view shows (portrait-only edits read/write p.portrait)
function view(p) {
  const u = grp(p.id)?.userData || {}, pt = usePt() ? p.portrait || {} : {};
  return { x: pt.x ?? (p.wall === 'left' ? u.x0 ?? 0 : p.x ?? 0), z: pt.z ?? (p.wall === 'back' ? u.z0 ?? 0 : p.z ?? 0), y: pt.y ?? p.y ?? 0, ry: pt.ry ?? p.ry ?? 0, k: p.k * (pt.k || 1) };
}
// x/z arrive as world positions from drags; the shared x is stored before the portrait squeeze
function setVal(p, key, v, world = true) {
  v = r2(v);
  if (usePt()) { const pt = p.portrait = p.portrait || {}; pt[key] = key === 'k' ? r2(Math.max(.01, v) / p.k) : v; return; }
  if (key === 'k') { p.k = Math.max(.01, v); return; }
  // a piece against the back wall leaves it when its z changes, one against the left wall when its x changes
  if (key === 'x') { if (p.wall === 'left') delete p.wall; if (world && isPortrait() && !p.noSqueeze) v = r2(v / sq()); }
  if (key === 'z' && p.wall === 'back') delete p.wall;
  p[key] = v;
}

// ---------- selection ----------
function select(id) {
  sel = id; selBtn = null; const p = id && propOf(id); ptMode = !!(p && p.portrait && isPortrait());
  showBox(); renderLeft(); renderRight();
}
function showBox() {
  if (!box) return;
  const o = mode === 'props' && sel ? grp(sel) : mode === 'walls' && selWall ? (selWall === 'back' ? X.back : X.wallSides[selWall === 'left' ? 0 : 1]) : null;
  box.visible = !!(o && o.visible); if (o) box.setFromObject(o);
}
function tick() { if (box && box.visible) showBox(); else if (sel || selWall) showBox(); if (X && X.furnGroup.children.length !== tick.n) { tick.n = X.furnGroup.children.length; syncProps(); renderLeft(); } }

// ---------- keyboard ----------
function onKey(e) {
  const t = e.target, typing = t && (t.tagName === 'INPUT' && t.type !== 'range' && t.type !== 'checkbox' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA');
  const k = e.key.toLowerCase(), ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && k === 's') { e.preventDefault(); return doSave(); }
  if (ctrl && k === 'z' && !e.shiftKey) { if (typing) return; e.preventDefault(); return doUndo(); }
  if (ctrl && (k === 'y' || k === 'z' && e.shiftKey)) { if (typing) return; e.preventDefault(); return doRedo(); }
  if (typing || mode !== 'props' || !sel || ctrl) return;
  const p = propOf(sel); if (!p) return; const v = view(p), st = e.shiftKey ? .25 : .05;
  const act = {
    r: () => change(() => setVal(p, 'ry', v.ry + (e.shiftKey ? -15 : 15) * DEG), 'ry' + sel),
    delete: () => removeProp(sel), backspace: () => removeProp(sel), escape: () => select(null),
    '+': () => resizeSel(1.05), '=': () => resizeSel(1.05), '-': () => resizeSel(1 / 1.05),
    arrowleft: () => change(() => setVal(p, 'x', v.x - st, false), 'ax' + sel), arrowright: () => change(() => setVal(p, 'x', v.x + st, false), 'ax' + sel),
    arrowup: () => change(() => setVal(p, 'z', v.z - st, false), 'az' + sel), arrowdown: () => change(() => setVal(p, 'z', v.z + st, false), 'az' + sel),
    pageup: () => change(() => setVal(p, 'y', v.y + st, false), 'ay' + sel), pagedown: () => change(() => setVal(p, 'y', v.y - st, false), 'ay' + sel),
  }[k];
  if (act) { e.preventDefault(); act(); }
}
addEventListener('keydown', onKey);
addEventListener('beforeunload', e => { if (L && JSON.stringify(L) !== saved) { e.preventDefault(); e.returnValue = ''; } });

// ---------- props: add, hide, remove ----------
function addProp(file) {
  const r = room(), info = propsList.find(p => p.name === file) || {}, base = pretty(file).replace(/ /g, '_');
  const used = new Set([...PRIM, ...ROOMS.flatMap(x => L.rooms[x].props.map(p => p.id))]);
  let id = base, n = 2; while (used.has(id)) id = base + '_' + n++;
  const k = { S: .3, M: .5, L: .7 }[info.class] || .5; // new pieces start at the back on the right, out of Googoo's way
  change(() => L.rooms[r].props.push({ id, file, k, x: 2.6, z: -3, ry: 0, castShadow: info.class === 'L', hidden: false }), '', 'all');
  select(id); status(`Added ${pretty(file)}. Drag it where you want it.`);
}
function removeProp(id) {
  const p = propOf(id); if (!p) return;
  if (BUILTIN.includes(id)) { change(() => { p.hidden = true; }, '', 'all'); return status(`${pretty(p.file)} is hidden (it stands in for a built-in piece of the room). Use 👁 to show it again.`); }
  change(() => { for (const r of ROOMS) L.rooms[r].props = L.rooms[r].props.filter(q => q.id !== id); }, '', 'all');
  if (sel === id) select(null);
}
function toggleHidden(id) { const p = propOf(id); change(() => { p.hidden = !p.hidden; }, '', 'all'); }

// ---------- buttons mode: drag rail buttons ----------
let bdrag = null;
function onBtnDown(e) {
  if (mode !== 'buttons') return;
  const b = e.target.closest && e.target.closest('.col .rb'); if (!b) return;
  e.stopImmediatePropagation(); e.preventDefault();
  selBtn = b.id; markBtn(); renderRight(); bdrag = { b, moved: false };
}
function onBtnMove(e) {
  if (!bdrag) return; const d = W.document, b = bdrag.b;
  const rail = d.getElementById(e.clientX < W.innerWidth / 2 ? 'colL' : 'colR');
  const others = [...rail.children].filter(x => x !== b && !x.hidden);
  const before = others.find(x => { const r = x.getBoundingClientRect(); return e.clientY < r.top + r.height / 2; });
  if (b.parentNode !== rail || b.nextElementSibling !== (before || null)) { rail.insertBefore(b, before || null); bdrag.moved = true; }
}
function onBtnUp() {
  if (!bdrag) return; const moved = bdrag.moved; bdrag = null; if (!moved) return;
  const d = W.document, k = screenKey(), ids = id => [...d.getElementById(id).children].map(x => x.id);
  change(() => { L.ui.screens[k] = { left: ids('colL'), right: ids('colR') }; }, '', 'ui'); markBtn(); renderRight();
}
function markBtn() { if (!W) return; W.document.querySelectorAll('.edSel').forEach(x => x.classList.remove('edSel')); if (mode === 'buttons' && selBtn) W.document.getElementById(selBtn)?.classList.add('edSel'); }
const btnLabel = id => { const b = W && W.document.getElementById(id); return b ? [b.textContent.trim(), b.getAttribute('aria-label')] : ['', id]; };

// ---------- camera ----------
async function loadScript(src) { return new Promise((res, rej) => { const s = W.document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej; W.document.head.appendChild(s); }); }
async function setFree(on) {
  if (on && !orbit) {
    try { await loadScript(CDN + 'OrbitControls.js'); } catch (e) { return status('Could not load the free camera (no internet?)', 'dirty'); }
    orbit = new X.THREE.OrbitControls(X.camera, ov); orbit.target.set(0, 2, -1.5); orbit.enableDamping = false;
    orbit.addEventListener('change', () => { if (free) freeCam = { p: X.camera.position.clone(), q: X.camera.quaternion.clone() }; });
  }
  free = on; $('freeCam').classList.toggle('on', on); $('gameCam').classList.toggle('on', !on);
  if (orbit) orbit.enabled = on;
  if (on) { freeCam = null; X.camera.clearViewOffset(); X.camera.updateProjectionMatrix(); orbit.update(); freeCam = { p: X.camera.position.clone(), q: X.camera.quaternion.clone() }; }
  else W.resize();
}
function restoreFree() { if (!freeCam) return; const c = X.camera; c.clearViewOffset(); c.position.copy(freeCam.p); c.quaternion.copy(freeCam.q); c.updateProjectionMatrix(); c.updateMatrixWorld(); }

// ---------- device size ----------
function setDevice(k) {
  device = k; const [, w, h] = DEVICES[k]; frame.style.width = w + 'px'; frame.style.height = h + 'px'; $('device').value = k; fit();
  if (!isPortraitSize(k)) ptMode = false; setTimeout(() => { renderRight(); }, 300);
}
const isPortraitSize = k => DEVICES[k][1] < DEVICES[k][2];
function fit() { const m = $('main'), [, w, h] = DEVICES[device], s = Math.min((m.clientWidth - 40) / w, (m.clientHeight - 40) / h, 1.5); frame.style.transform = `scale(${s})`; Object.assign($('fbox').style, { width: w * s + 'px', height: h * s + 'px' }); }
addEventListener('resize', fit);

// ---------- top bar ----------
$('rooms').onclick = async e => { const r = e.target.dataset.room; if (!r || !X) return; await goRoom(r); };
async function goRoom(r) { select(null); selWall = null; await W.setRoom(r); for (const p of L.rooms[r].props) if (!grp(p.id)) inflight.add(p.id); apply('props'); renderTop(); renderLeft(); }
function renderTop() { const r = room(); document.querySelectorAll('#rooms .eb').forEach(b => b.classList.toggle('on', b.dataset.room === r)); }
$('device').onchange = e => setDevice(e.target.value);
$('gameCam').onclick = () => setFree(false); $('freeCam').onclick = () => setFree(true);
$('undo').onclick = doUndo; $('redo').onclick = doRedo; $('save').onclick = doSave;
$('reset').onclick = () => { const r = room(); if (confirm(`Put the ${ROOM_NAME[r]} back to how it was at the last save?`)) change(() => { L.rooms[r] = clone(JSON.parse(saved).rooms[r]); }, '', 'all'); };
$('publish').onclick = doPublish;
document.querySelector('#ed .tabs').onclick = e => { const m = e.target.dataset.mode; if (m) setMode(m); };
function setMode(m) {
  mode = m; document.querySelectorAll('#ed .tabs .eb').forEach(b => b.classList.toggle('on', b.dataset.mode === m));
  if (W) W.document.body.classList.toggle('edBtns', m === 'buttons');
  sel = null; selWall = null; selBtn = null; showBox(); markBtn(); renderLeft(); renderRight();
}

async function post(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Design': '1' }, body: body ? JSON.stringify(body) : '' });
  return r.json();
}
async function doSave() {
  if (!L) return false;
  try { const r = await post('save', L); if (!r.ok) { status('Not saved: ' + r.error, 'dirty'); return false; } saved = JSON.stringify(L); status(`✔ Saved at ${r.time}. (Only on this PC until you publish.)`); return true; }
  catch (e) { status('Not saved: the design server is not running (start tools/design_mode.bat).', 'dirty'); return false; }
}
async function doPublish() {
  if (!confirm('Publish to the test site? (The live game is not changed.)')) return;
  if (JSON.stringify(L) !== saved && !(await doSave())) return;
  status('Publishing… (this takes a few seconds)');
  try { const r = await post('publish' + (new URLSearchParams(location.search).get('dry') ? '?dry=1' : '')); showModal(r.ok ? '✔ Published to the test site' : '✖ Publish failed: nothing else was changed', r.output || r.error); status(r.ok ? '✔ Published. The test site updates in about a minute.' : '✖ Publish failed (see the message).', r.ok ? '' : 'dirty'); }
  catch (e) { status('Publish failed: the design server is not running.', 'dirty'); }
}
function showModal(title, text) {
  const m = document.createElement('div'); m.id = 'modal';
  m.innerHTML = `<div><h2 style="font-size:18px;text-transform:none;color:#1d2433"></h2><pre></pre><button class="eb go">Close</button></div>`;
  m.querySelector('h2').textContent = title; m.querySelector('pre').textContent = text; m.querySelector('button').onclick = () => m.remove(); $('ed').appendChild(m);
}

// ---------- left panel ----------
function renderLeft() {
  const el = $('left'); if (!L) return;
  if (mode === 'walls') { el.innerHTML = `<h2>Walls</h2><p class="hint">Click the back, left or right wall in the picture, then drag it in or out to make the room smaller or bigger. Colours are on the right.</p><p class="hint">Pieces standing against a wall move with it.</p>`; return; }
  if (mode === 'buttons') { el.innerHTML = `<h2>Buttons</h2><p class="hint">Drag a round button in the picture up or down to change the order, or across to the other side.</p><p class="hint">Click a button to change its colour. Size and shape for all buttons are on the right.</p><p class="hint">Each screen has its own buttons: pick the screen on the right.</p>`; return; }
  const r = room(), here = L.rooms[r].props;
  const files = propsList.length ? propsList : [...new Set(ROOMS.flatMap(x => L.rooms[x].props.map(p => p.file)))].map(name => ({ name }));
  const keepFocus = document.activeElement && document.activeElement.id === 'search';
  if (!el.querySelector('#search')) {
    el.innerHTML = `<h2>Props in the ${ROOM_NAME[r].toLowerCase()}</h2><input id="search" type="search" placeholder="Search props…"><div class="chips">${[['all', 'All'], ['furniture', 'Furniture'], ['toys', 'Toys'], ['decor', 'Decor'], ['here', 'In this room'], ['hidden', 'Hidden']].map(([k, t]) => `<button class="eb" data-chip="${k}">${t}</button>`).join('')}</div><div id="plist"></div>
    <p class="hint">Click a piece in the picture to select it. Drag = move on the floor · Shift+drag = height · wheel or +/- = size · R = turn · arrows = nudge · Delete = remove.</p>`;
    el.querySelector('#search').oninput = e => { query = e.target.value.toLowerCase(); renderLeft(); };
    el.querySelector('.chips').onclick = e => { if (e.target.dataset.chip) { chip = e.target.dataset.chip; renderLeft(); } };
  }
  el.querySelector('h2').textContent = 'Props in the ' + ROOM_NAME[r].toLowerCase();
  el.querySelectorAll('[data-chip]').forEach(b => b.classList.toggle('on', b.dataset.chip === chip));
  const rows = [];
  const order = f => here.some(p => p.file === f.name) ? 0 : 1; // pieces in this room first
  for (const f of [...files].sort((a, b) => order(a) - order(b))) {
    const inst = here.filter(p => p.file === f.name), c = cat(f.name);
    if (query && !pretty(f.name).includes(query) && !inst.some(p => p.id.includes(query))) continue;
    if (['furniture', 'toys', 'decor'].includes(chip) && c !== chip) continue;
    if (chip === 'here' && !inst.length) continue;
    if (chip === 'hidden' && !inst.some(p => p.hidden)) continue;
    rows.push(`<div class="prow"><span class="ic">${ICON[c]}</span><span class="nm">${pretty(f.name)}<small>${f.class ? f.class + ' · ' + (f.tris / 1000).toFixed(1) + 'k triangles' : ''}${inst.length ? ' · in this room' : ''}</small></span><button class="ib" data-add="${f.name}" title="Add to this room">➕</button></div>`);
    for (const p of inst) rows.push(`<div class="prow inst${p.id === sel ? ' sel' : ''}${p.hidden ? ' off' : ''}" data-sel="${p.id}"><span class="nm">${p.id}${p.hidden ? ' (hidden)' : ''}</span><button class="ib" data-eye="${p.id}" title="${p.hidden ? 'Show' : 'Hide'}">${p.hidden ? '🙈' : '👁'}</button><button class="ib" data-del="${p.id}" title="Remove">🗑</button></div>`);
  }
  const list = el.querySelector('#plist'); list.innerHTML = rows.join('') || '<p class="hint">Nothing matches.</p>';
  list.onclick = e => { const t = e.target.closest('[data-add],[data-eye],[data-del],[data-sel]'); if (!t) return;
    if (t.dataset.add) addProp(t.dataset.add); else if (t.dataset.eye) toggleHidden(t.dataset.eye); else if (t.dataset.del) removeProp(t.dataset.del); else select(t.dataset.sel); };
  if (keepFocus) el.querySelector('#search').focus();
}

// ---------- right panel ----------
function field(label, key, min, max, step, val, unit = '') {
  return `<div class="field"><label>${label}</label><input type="range" data-k="${key}" min="${min}" max="${max}" step="${step}" value="${val}"><input type="number" data-k="${key}" step="${step}" value="${val}">${unit}</div>`;
}
function renderRight() {
  const el = $('right'); if (!L || !X) return;
  if (mode === 'walls') return renderWalls(el);
  if (mode === 'buttons') return renderButtons(el);
  const p = sel && propOf(sel);
  if (!p) { el.innerHTML = `<h2>Nothing selected</h2><p class="hint">Click a piece of furniture or a toy in the picture, or pick one in the list on the left.</p><p class="hint">Googoo is there to show the size; he can't be moved.</p>`; return; }
  const v = view(p), por = isPortrait(), r3 = x => Math.round(x * 100) / 100;
  el.innerHTML = `<h2>${pretty(p.file)} <span style="text-transform:none;font-weight:400">(${p.id})</span></h2>
   <label class="check"><input type="checkbox" id="ptOnly" ${usePt() ? 'checked' : ''} ${por ? '' : 'disabled'}><span>Upright phones only<br><small class="hint">${por ? (p.portrait ? 'This piece has its own place on upright phones.' : 'Tick to give it a different place on upright phones.') : 'Pick an upright screen size to use this.'}</small></span></label>
   ${field('Size', 'k', .05, 2.5, .01, r3(v.k))}
   ${field('Turn (°)', 'ry', -180, 180, 1, Math.round(v.ry / DEG))}
   ${field('Height', 'y', -.5, 6, .05, r3(v.y))}
   ${field('Left / right', 'x', -10, 10, .05, r3(v.x))}
   ${field('Back / front', 'z', -10, 8, .05, r3(v.z))}
   <div class="field"><label>Against a wall</label><select class="eb" id="wall" ${usePt() ? 'disabled' : ''}><option value="">No</option><option value="back">Back wall</option><option value="left">Left wall</option></select><span></span></div>
   <label class="check"><input type="checkbox" id="shadow" ${p.castShadow ? 'checked' : ''}><span>Casts a shadow<br><small class="hint">Only for big furniture (each shadow costs speed on phones).</small></span></label>
   <div class="row"><button class="eb" id="copy">Copy position</button><button class="eb" id="paste" ${clip ? '' : 'disabled'}>Paste position</button></div>
   ${usePt() && p.portrait ? '<div class="row"><button class="eb" id="ptClear">Use the same place as on other screens</button></div>' : ''}
   <div class="row"><button class="eb" id="hide">${p.hidden ? '👁 Show' : '🙈 Hide'}</button><button class="eb warn" id="del">🗑 Remove</button></div>`;
  el.querySelector('#wall').value = p.wall || '';
  el.oninput = e => { const k = e.target.dataset.k; if (!k) return; let val = parseFloat(e.target.value); if (isNaN(val)) return; if (k === 'ry') val *= DEG;
    change(() => setVal(p, k, val, false), 'f' + k + sel); el.querySelectorAll(`[data-k="${k}"]`).forEach(i => { if (i !== e.target) i.value = e.target.value; }); };
  el.querySelector('#ptOnly').onchange = e => { ptMode = e.target.checked; renderRight(); };
  el.querySelector('#wall').onchange = e => change(() => { const w = e.target.value, vv = view(p); if (w) p.wall = w; else { p.x = r2(vv.x); p.z = r2(vv.z); delete p.wall; } }, '', 'props');
  el.querySelector('#shadow').onchange = e => change(() => { p.castShadow = e.target.checked; });
  el.querySelector('#copy').onclick = () => { clip = view(p); status('Position copied. Pick another view or piece and press Paste.'); renderRight(); };
  el.querySelector('#paste').onclick = () => change(() => { for (const k of ['x', 'z', 'y', 'ry', 'k']) setVal(p, k, clip[k], false); }, '');
  el.querySelector('#ptClear') && (el.querySelector('#ptClear').onclick = () => { change(() => { delete p.portrait; }, ''); renderRight(); });
  el.querySelector('#hide').onclick = () => toggleHidden(p.id);
  el.querySelector('#del').onclick = () => removeProp(p.id);
}
// keep the numbers in the right panel live while dragging in the picture (without rebuilding it)
setInterval(() => {
  if (!L || !X) return; let vals;
  if (mode === 'walls') vals = L.rooms[room()].walls;
  else if (mode === 'buttons') vals = { size: L.ui.size };
  else { const p = sel && propOf(sel); if (!p) return; const v = view(p); vals = { k: Math.round(v.k * 100) / 100, ry: Math.round(v.ry / DEG), y: Math.round(v.y * 100) / 100, x: Math.round(v.x * 100) / 100, z: Math.round(v.z * 100) / 100 }; }
  document.querySelectorAll('#right [data-k]').forEach(i => { if (i !== document.activeElement) i.value = vals[i.dataset.k]; });
}, 200);

function renderWalls(el) {
  const r = room(), w = L.rooms[r].walls, r3 = x => Math.round(x * 100) / 100;
  el.innerHTML = `<h2>${ROOM_NAME[r]}: walls</h2>
   <p class="hint">${selWall ? `Selected: <b>${selWall} wall</b>. Drag it in the picture, or type a number.` : 'Click a wall in the picture to select it.'}</p>
   ${field('Back wall', 'back', -14, -1.5, .05, r3(w.back))}${field('Left wall', 'left', -16, -2, .05, r3(w.left))}${field('Right wall', 'right', 2, 16, .05, r3(w.right))}
   <div class="field"><label>Wall colour</label><input type="color" id="wcol" value="${w.color}"><span></span></div>
   <div class="field"><label>Floor colour</label><input type="color" id="fcol" value="${w.floor}"><span></span></div>
   <p class="hint">The floor keeps its wood pattern; the colour tints it. White = as it is now.</p>`;
  el.oninput = e => { const k = e.target.dataset.k, t = e.target;
    if (k) { const val = parseFloat(t.value); if (isNaN(val)) return; change(() => { w[k] = val; }, 'w' + k, 'walls'); el.querySelectorAll(`[data-k="${k}"]`).forEach(i => { if (i !== t) i.value = t.value; }); }
    if (t.id === 'wcol') change(() => { w.color = t.value; }, 'wcol', 'ui');
    if (t.id === 'fcol') change(() => { w.floor = t.value; }, 'fcol', 'walls'); };
}
function renderButtons(el) {
  const k = screenKey(), S = L.ui.screens[k] || { left: [], right: [] }, all = Object.keys(L.ui.buttons), on = new Set([...S.left, ...S.right]);
  const row = id => { const [em, nm] = btnLabel(id); return `<div class="brow${id === selBtn ? ' sel' : ''}"><span class="em">${em}</span><span class="nm">${nm}</span><input type="color" data-col="${id}" value="${L.ui.buttons[id].color}" title="Colour"><button class="ib eb" data-rm="${id}" title="Take off this screen">✕</button></div>`; };
  el.innerHTML = `<h2>Buttons</h2>
   <div class="field"><label>Screen</label><select class="eb" id="scr">${Object.keys(SCREEN_NAME).map(s => `<option value="${s}">${SCREEN_NAME[s]}</option>`).join('')}</select><span></span></div>
   ${field('Size (all)', 'size', .7, 1.4, .05, L.ui.size)}
   <div class="field"><label>Shape (all)</label><div class="grp"><button class="eb${L.ui.shape === 'round' ? ' on' : ''}" data-shape="round">● Round</button><button class="eb${L.ui.shape === 'square' ? ' on' : ''}" data-shape="square">■ Square</button></div><span></span></div>
   <h2 style="margin-top:14px">Left side</h2><div class="blist">${S.left.map(row).join('') || '<p class="hint">none</p>'}</div>
   <h2>Right side</h2><div class="blist">${S.right.map(row).join('') || '<p class="hint">none</p>'}</div>
   <div class="field"><label>Add a button</label><select class="eb" id="addb"><option value="">Choose…</option>${all.filter(id => !on.has(id)).map(id => `<option value="${id}">${btnLabel(id).join(' ')}</option>`).join('')}</select><span></span></div>`;
  el.querySelector('#scr').value = k;
  el.querySelector('#scr').onchange = async e => { const s = e.target.value; selBtn = null; if (s === 'night') { await W.setRoom('bed'); W.setLights(false); } else { if (s === 'bed' && !W.eval('lightsOn')) W.setLights(true); await W.setRoom(s); } renderTop(); renderButtons(el); };
  el.oninput = e => { const t = e.target;
    if (t.dataset.k === 'size') { const v = parseFloat(t.value); if (!isNaN(v)) change(() => { L.ui.size = v; }, 'bsize', 'ui'); el.querySelectorAll('[data-k=size]').forEach(i => { if (i !== t) i.value = t.value; }); }
    if (t.dataset.col) { const id = t.dataset.col; selBtn = id; markBtn(); change(() => { L.ui.buttons[id].color = t.value; }, 'bc' + id, 'ui'); } };
  el.onclick = e => { const t = e.target;
    if (t.dataset.shape) { change(() => { L.ui.shape = t.dataset.shape; }, '', 'ui'); renderButtons(el); }
    if (t.dataset.rm) { change(() => { const s = L.ui.screens[k]; s.left = s.left.filter(x => x !== t.dataset.rm); s.right = s.right.filter(x => x !== t.dataset.rm); }, '', 'ui'); renderButtons(el); } };
  el.querySelector('#addb').onchange = e => { const id = e.target.value; if (id) { change(() => { (L.ui.screens[k] = L.ui.screens[k] || { left: [], right: [] }).left.push(id); }, '', 'ui'); renderButtons(el); } };
  markBtn();
}

// ---------- budget meter (docs/gpu-budget.md): one whole frame incl. the shadow pass ----------
function budget() {
  if (!X || document.hidden) return;
  W.requestAnimationFrame(() => {
    const ri = X.renderer.info, bv = box.visible; box.visible = false; ri.autoReset = false; ri.reset();
    W.requestAnimationFrame(() => {
      const seen = new Set(); let bytes = 0;
      const add = t => { if (!t || !t.isTexture || seen.has(t.uuid)) return; seen.add(t.uuid); const i = t.image || {}; bytes += (i.width || 0) * (i.height || 0) * (t.isCompressedTexture ? 1 : 4) * (t.generateMipmaps !== false ? 4 / 3 : 1); };
      const shown = o => { for (; o; o = o.parent) if (!o.visible) return false; return true; };
      X.scene.traverse(o => { if (o.material && shown(o)) [].concat(o.material).forEach(m => { for (const k in m) add(m[k]); }); if (o.isLight && o.castShadow && o.shadow.map) bytes += o.shadow.map.width * o.shadow.map.height * 4; });
      const calls = ri.render.calls, tris = ri.render.triangles, mb = bytes / 2 ** 20; ri.autoReset = true; box.visible = bv;
      const lvl = (v, [a, b]) => v > b ? 'r' : v > a ? 'a' : 'g';
      $('dCalls').className = 'dot ' + lvl(calls, LIMIT.calls); $('mCalls').textContent = `${calls} / 100 draw calls`;
      $('dTris').className = 'dot ' + lvl(tris, LIMIT.tris); $('mTris').textContent = `${(tris / 1000).toFixed(1)}k / 200k triangles`;
      $('dMb').className = 'dot ' + lvl(mb, LIMIT.mb); $('mMb').textContent = `${mb.toFixed(0)} MB textures (64, max 96)`;
    });
  });
}

window.ED = { get L() { return L; }, get sel() { return sel; }, select, setMode, setDevice, setFree, goRoom, doSave, doUndo, doRedo, addProp, removeProp, toggleHidden, get saved() { return saved; } }; // for tests
})();

// Googoo Robo Design mode: a room editor on top of the real game. Loaded by the game page only with ?design=1
// (start it with tools/design_mode.bat, which runs tools/design_server.py for Save and Publish).
// This page becomes the editor; the real game runs in an iframe sized like a phone or tablet, and the editor
// drives it through the game's own globals (PROPS, furnGroup, applyLayout, loadProp, HOME, CAMS, ...). Everything is saved to data/layout.json.
(() => {
'use strict';
// the copy of the game in this page stops (the one in the iframe is the one we edit)
try { window.loop = function () {}; cancelAnimationFrame(raf); renderer.forceContextLoss(); renderer.domElement.remove(); } catch (e) {}

const ROOMS = ['home', 'play', 'bed', 'library'], ROOM_NAME = { home: 'Living room', play: 'Play room', bed: 'Bedroom', library: 'Library' };
const SHELVES = { lib_shelf: 'big', lib_bin: 'small' }; // the library's two shelves (game LIBSH): their books are set in the Props panel
const SCREEN_NAME = { home: 'Living room', play: 'Play room', bed: 'Bedroom', night: 'Bedroom, lamp off', library: 'Library', say: 'Say it', book: 'Library, book open', top: 'Top bar (stars, mic, gear)', nav: 'Room tabs (bottom)' };
const DEVICES = { up: ['iPhone upright', 390, 844], side: ['iPhone sideways', 844, 390], small: ['Small phone', 360, 640], ipad: ['iPad', 820, 1180] };
// these stand in for a built-in piece of the room: removing them would bring the old piece back, so they are hidden instead
const BUILTIN = ['window', 'tv', 'picture', 'chair', 'carpet', 'toybox', 'teddy', 'blocks', 'drum', 'kite', 'bed', 'lamp', 'nightstand', 'rug', 'book', 'star'];
const PRIMS = { book: ['home', 'Book', '📕'], star: ['bed', 'Star mobile', '⭐'] }; // built-in pieces made in code: movable, no size
const PRIM = ['bed', 'lamp', 'book', 'chair', 'tv', 'picture', 'shelf', 'teddy', 'blocks', 'drum', 'kite', 'nightstand', 'star', 'ball', 'googoo'];
const NAMES = { living_armchair: 'Armchair', living_window_curtains: 'Window', living_carpet_persian: 'Persian carpet', living_tv_cabinet: 'TV', living_coffee_table: 'Coffee table',
  living_floor_lamp: 'Floor lamp', living_picture_frame: 'Picture', living_bookshelf: 'Bookshelf', living_door: 'Door', living_korsi: 'Korsi', living_sofa: 'Sofa',
  toy_teddy_bear: 'Teddy bear', toy_box: 'Toy box', toy_blocks: 'Blocks', toy_ball: 'Ball', toy_doll: 'Doll', toy_drum: 'Drum', toy_kite: 'Kite', toy_piano: 'Piano', farm_cow: 'Cow',
  bedroom_bed: 'Bed', bedroom_lamp: 'Bedside lamp', bedroom_nightstand: 'Nightstand', bedroom_rug: 'Rug', bedroom_wardrobe: 'Wardrobe', bedroom_pillow: 'Pillow', bedroom_blanket: 'Blanket',
  library_bookshelf: 'Library bookshelf', library_book_bin: 'Book bin', library_beanbag: 'Beanbag', library_reading_lamp: 'Reading lamp', library_letter_garland: 'Letter garland' };
const TOPS = { score: ['⭐', 'Stars'], bTalk: ['🎤', 'Microphone'], parentBtn: ['⚙︎', 'Parent corner (always shown)'] };
const TABS = { home: ['🏠', 'Living room'], play: ['🧸', 'Play room'], bed: ['🛏️', 'Bedroom'], say: ['🗣️', 'Say it'], book: ['📖', 'Picture book'], library: ['📖', 'Library'] };
const LIMIT = { calls: [80, 100], tris: [150e3, 200e3], mb: [64, 96] }; // docs/gpu-budget.md: target, hard limit
const CDN = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/';
const DEG = Math.PI / 180, FRONT = 7.8; // the room's open front edge (game: BACK + RD)

let L = null, saved = '', undo = [], redo = [], lastKey = '', lastT = 0;
let W = null, X = null, RBH = 1, mode = 'props', sel = null, selWall = null, selBtn = null, bscr = null, ptMode = false, clip = null;
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
.prow{display:flex;align-items:center;gap:6px;padding:4px 6px;border-radius:8px}
.prow .ic{font-size:20px;width:26px;text-align:center;flex:none}.prow .nm{flex:1;min-width:0}.prow .nm small{display:block;color:#7a8394;font-size:11.5px}
.prow .ib{border:0;background:none;cursor:pointer;font-size:15px;padding:3px 4px;border-radius:6px}.prow .ib:hover{background:#e8edf4}
.prow.placed{cursor:pointer}.prow.placed:hover{background:#f2f5f9}.prow.sel{background:#dbe7ff}.prow.off .nm{opacity:.5}
.prow.new .nm{color:#5b6576}.sub{font:700 11.5px system-ui;color:#7a8394;text-transform:uppercase;letter-spacing:.04em;margin:12px 6px 4px}
.field{display:grid;grid-template-columns:96px 1fr 64px;align-items:center;gap:8px;margin:8px 0}
.field label{color:#3b4455}.field input[type=number]{width:64px;box-sizing:border-box;border:1px solid #cdd4de;border-radius:6px;padding:3px 5px}
.field input[type=range]{width:100%}.row{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.check{display:flex;gap:8px;align-items:flex-start;margin:10px 0}.check input{margin-top:3px}
.tabs{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:12px}.tabs .eb{border-radius:8px;margin:0}
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
 <div class="tabs"><button class="eb on" data-mode="props">🪑 Props</button><button class="eb" data-mode="walls">🧱 Walls & floor</button><button class="eb" data-mode="buttons">🔘 Buttons</button><button class="eb" data-mode="camera">📷 Camera</button><button class="eb" data-mode="paint">🖼️ Painting</button></div>
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
const camKey = () => W.eval('camKey()');
const sq = () => Math.min(1, (isPortrait() ? .3 : .35) + W.innerWidth / W.innerHeight * .75); // the game's portrait squeeze (resize())
const nice = f => NAMES[f] || f.replace(/^(living|bedroom|toy|farm|library)_/, '').replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
const nameOf = p => p.builtin ? PRIMS[p.id][1] : nice(p.file);
const cat = f => !f ? 'decor' : /^(toy|farm)_/.test(f) ? 'toys' : /(bed|nightstand|wardrobe|sofa|armchair|bookshelf|tv_cabinet|korsi|coffee_table|door|box|book_bin|beanbag)$/.test(f) ? 'furniture' : 'decor';
const ICON = { toys: '🧸', furniture: '🛋️', decor: '🖼️' };
const propOf = id => { for (const r of ROOMS) { const p = L.rooms[r].props.find(p => p.id === id); if (p) return p; } return virt[id] || null; };
// the book and the star mobile are built in code: they get a layout entry only once they are actually changed (virt = not in the layout yet)
let VIRT0 = {}, virt = {};
function resetVirt() { virt = {}; for (const id in VIRT0) if (!L.rooms[PRIMS[id][0]].props.some(p => p.id === id)) virt[id] = clone(VIRT0[id]); }
function promoteVirt() { for (const id in virt) if (JSON.stringify(virt[id]) !== JSON.stringify(VIRT0[id])) { L.rooms[PRIMS[id][0]].props.push(virt[id]); delete virt[id]; } }
const propsIn = r => [...L.rooms[r].props, ...Object.values(virt).filter(v => PRIMS[v.id][0] === r)];
const grp = id => X && X.furnGroup.children.find(g => g.userData.furn === id && (g.userData.m || PRIMS[id]));
const usePt = () => ptMode && isPortrait();
const r2 = v => Math.round(v * 1000) / 1000, r100 = v => Math.round(v * 100) / 100;
const hex = c => { const m = String(c).match(/\d+(\.\d+)?/g); return m ? '#' + m.slice(0, 3).map(v => (+v | 0).toString(16).padStart(2, '0')).join('') : '#ffffff'; };
function status(t, cls) { const s = $('status'); s.textContent = t; s.className = cls || ''; }
function dirtyStatus() { const d = JSON.stringify(L) !== saved; if (d) status('● Unsaved changes', 'dirty'); return d; }
const walls = (r = room()) => L.rooms[r].walls;
const onOf = p => p.on !== undefined ? p.on : X.SITS[p.id]; // "sits on" another piece (the lamp on the nightstand by default)
// size as the real rendered height in % of Googoo's height (each GLB has its own inner scale, so k alone says little); rugs: their length
function pctUnit(p) { const u = grp(p.id)?.userData; if (!u || !u.bb1) return null; const s = u.bb1.getSize(new X.THREE.Vector3()); return (p.flatten ? Math.max(s.x, s.z) : s.y) * RBH / W.eval('RB.h') * 100; }
const floorOf = (r = room()) => { const w = walls(r); return w.floorRect || { left: w.left, right: w.right, back: w.back, front: FRONT }; };

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
  const r = room(); promoteVirt(); resetVirt();
  if (kind === 'all' || kind === 'ui') W.applyLayout(L);
  else if (kind === 'walls') { X.WALLS[r] = walls(r); W.applyWalls(r); }
  else if (kind === 'paint') { W.eval('PAINT')[r] = L.rooms[r].backdrop ?? null; W.showScreen(W.eval('scr')); }
  else if (kind === 'goo' || kind === 'cam') { X.GOO[r] = L.rooms[r].googoo || {}; X.CAMS[r] = L.rooms[r].camera || {}; }
  syncProps();
  if (kind === 'all' || kind === 'goo' || kind === 'cam') { W.resize(); if (kind !== 'cam') W.eval('robot.position.x=HOME.x;robot.position.z=HOME.z'); }
  if (kind !== 'props' && kind !== 'goo' || !sel) renderLeft();
  if (mode === 'paint') renderPaint();
  if (kind === 'all') renderRight(); // panels rebuild only on big changes, so a slider being dragged keeps working
  dirtyStatus(); $('undo').disabled = !undo.length; $('redo').disabled = !redo.length;
}
// loaded prop groups follow L: size, place, turn, portrait values, shadow, hidden; removed ones go, new ones load
function syncProps() {
  const cur = room(), want = new Map();
  for (const r of ROOMS) for (const p of propsIn(r)) want.set(p.id, [p, r]);
  for (const g of [...X.furnGroup.children]) {
    const u = g.userData, w = want.get(u.furn);
    if (PRIMS[u.furn] && w) { const [p] = w; u.x0 = p.x ?? u.x0; if (p.z != null) g.position.z = p.z; if (p.y != null) g.position.y = p.y; if (p.ry != null && !u.spin) g.rotation.y = p.ry; u.off = p.hidden ? 1 : 0; u.on = onOf(p); g.visible = PRIMS[u.furn][0] === cur && !p.hidden; continue; }
    if (!u.m) continue;
    if (!w) { X.furnGroup.remove(g); inflight.delete(u.furn); continue; }
    const [p, r] = w, sc = RBH * p.k;
    u.base.set(sc, sc * (p.flatten || 1), sc); u.y0 = p.y || 0; u.ry0 = p.ry || 0; u.pt = p.portrait; u.nosq = p.noSqueeze ? 1 : 0; u.off = p.hidden ? 1 : 0; u.room = r; u.on = onOf(p);
    if (!u.bb1) { const s0 = u.m.scale.clone(), par = u.m.parent; par.remove(u.m); u.m.scale.set(1, 1, 1); u.m.updateMatrixWorld(true); u.bb1 = new X.THREE.Box3().setFromObject(u.m); u.m.scale.copy(s0); par.add(u.m); }
    const WL = L.rooms[r].walls;
    u.x0 = p.wall === 'left' ? WL.left - u.bb1.min.z * sc + .03 : p.x ?? u.x0;
    u.z0 = p.wall === 'back' ? WL.back - u.bb1.min.z * sc + .03 : p.z ?? u.z0;
    u.m.traverse(o => { if (o.isMesh) o.castShadow = !!p.castShadow; });
    g.visible = r === cur && !p.hidden;
  }
  for (const p of L.rooms[cur].props) if (!p.builtin && !grp(p.id) && !inflight.has(p.id) && X.PROPS[p.id]) { inflight.add(p.id); W.loadProp(p.id); }
  W.roomProps(cur); W.placeProps(sq());
  if (free) restoreFree();
}

// ---------- wait for the game in the iframe ----------
frame.src = 'index.html?frame=1';
frame.addEventListener('load', async () => {
  W = frame.contentWindow;
  for (let i = 0; i < 300 && !(W.__ggReady && typeof W.applyLayout === 'function'); i++) await new Promise(r => setTimeout(r, 100));
  await W.eval('LAYOUT');
  X = W.eval('({THREE,scene,camera,renderer,furnGroup,PROPS,WALLS,GOO,CAMS,SITS,back,wallSides,wood,robot,RB0})');
  RBH = X.RB0.h;
  try { L = await (await fetch('data/layout.json', { cache: 'no-store' })).json(); } catch (e) { L = null; }
  if (!L || !L.rooms) { status('Could not read data/layout.json', 'dirty'); return; }
  // a layout from before the library: it starts from the game's built-in library (Save writes it into layout.json)
  if (!L.rooms.library) L.rooms.library = clone(W.eval("roomLayout('library')"));
  if (!L.ui.screens.library) L.ui.screens.library = { left: [...W.eval('SCREENS.library[0]')], right: [...W.eval('SCREENS.library[1]')] };
  if (!L.ui.buttons.bRead) L.ui.buttons.bRead = { color: '#ff8fab' };
  // the book and the star mobile are built in code: give them a layout entry (their place today) so they can be moved
  for (const id in PRIMS) { const g = W.eval(`furnById('${id}')`); if (g) VIRT0[id] = { id, builtin: true, x: r2(g.userData.x0), z: r2(g.position.z), y: r2(g.position.y), ...(g.userData.spin ? {} : { ry: r2(g.rotation.y) }), hidden: false }; }
  for (const r of ROOMS) if (!('backdrop' in L.rooms[r]) && W.eval('PAINT0')[r]) L.rooms[r].backdrop = clone(W.eval('PAINT0')[r]); // painted rooms: the built-in pictures (Save writes them)
  resetVirt();
  saved = JSON.stringify(L);
  // start the game without the start screen (no sound in Design mode); the room's props load
  W.eval("document.getElementById('start').hidden=true;document.getElementById('hint').hidden=true;propsOn=true;loadProps(curRoom)");
  for (const p of L.rooms[room()].props) inflight.add(p.id);
  W.__safe = SAFE[device]; setupFrame(); apply('all'); setDevice(device); renderTop();
  status(serverOk ? 'Ready. Click a piece (or Googoo) in the room to move it.' : 'Design server is not running (start tools/design_mode.bat): you can try things but Save and Publish will not work.', serverOk ? '' : 'dirty');
  setInterval(tick, 250); setInterval(budget, 1500);
});
fetch('props').then(r => r.json()).then(list => { propsList = list; serverOk = true; renderLeft(); }).catch(() => { serverOk = false; });

// ---------- inside the iframe: overlay for picking, button dragging, free camera ----------
let ov, box;
function setupFrame() {
  const d = W.document, st = d.createElement('style');
  st.textContent = `#edOv{position:fixed;inset:0;z-index:50;cursor:default}#edOv.grab{cursor:grabbing}
    body.edBtns .col,body.edBtns #nav,body.edBtns #top,body.edBtns #parentBtn{z-index:60}body.edBtns :is(.col .rb,#nav .rb,#top>*,#parentBtn){cursor:grab}
    .edSel{outline:3px dashed #2563eb!important;outline-offset:4px}.edWarn{outline:3px solid #e11d48!important;outline-offset:3px}.edG{position:fixed;background:#e11d48;z-index:80;pointer-events:none}body.edBtns #free{z-index:60}body.edBtns :is(.rb,.ec.nav,#free>*){animation:none!important;transform:none!important}body:not(.edBtns) .edG{display:none}body:not(.edBtns) .edWarn{outline:none!important}body:not(.edBtns) :is(#parentBtn,#top,#surp){pointer-events:none}`;
  d.head.appendChild(st);
  ov = d.createElement('div'); ov.id = 'edOv'; d.body.appendChild(ov);
  box = new X.THREE.BoxHelper(undefined, 0x2563eb); box.visible = false; box.material.depthTest = false; box.renderOrder = 999; X.scene.add(box);
  ov.addEventListener('pointerdown', onDown, true);
  ov.addEventListener('wheel', onWheel, { capture: true, passive: false });
  W.addEventListener('pointermove', onMove); W.addEventListener('pointerup', onUp);
  W.addEventListener('keydown', onKey);
  // buttons mode: buttons drag; their game actions (and the gear's hold) are blocked
  d.addEventListener('pointerdown', onBtnDown, true);
  d.addEventListener('click', e => { if (mode === 'buttons' && e.target.closest && e.target.closest(BTNQ)) { e.stopImmediatePropagation(); e.preventDefault(); } }, true);
  // the game's resize() re-aims the camera: in free camera mode keep ours
  const orig = W.resize;
  W.resize = function () { orig(); if (free) restoreFree(); };
  W.addEventListener('resize', () => { if (free) restoreFree(); fit(); });
}
const ray = () => new X.THREE.Raycaster();
function ndc(e) { return new X.THREE.Vector2(e.clientX / W.innerWidth * 2 - 1, -(e.clientY / W.innerHeight) * 2 + 1); }
// a prop id, 'googoo', or null: the nearest of the props' own meshes, Googoo's box, rugs' boxes
function pick(e) {
  const T = X.THREE, rc = ray(); rc.setFromCamera(ndc(e), X.camera);
  const cands = X.furnGroup.children.filter(g => g.visible && propOf(g.userData.furn) && (g.userData.m || PRIMS[g.userData.furn]));
  let best = null, bd = 1e9;
  const h = rc.intersectObjects(cands.map(g => g.userData.m || g), true)[0]; // the model itself, not the game's padded tap box (sized before the portrait shrink)
  if (h) { let o = h.object; while (o.parent !== X.furnGroup) o = o.parent; best = o.userData.furn; bd = h.distance; }
  const hit = (b, id) => { const p = rc.ray.intersectBox(b, new T.Vector3()); if (p) { const dd = p.distanceTo(rc.ray.origin); if (dd < bd) { bd = dd; best = id; } } };
  hit(new T.Box3().setFromObject(X.robot), 'googoo');
  if (!best) for (const g of cands.filter(g => propOf(g.userData.furn).flatten)) hit(new T.Box3().setFromObject(g), g.userData.furn);
  return best;
}
function planeHit(e, plane) { const rc = ray(); rc.setFromCamera(ndc(e), X.camera); return rc.ray.intersectPlane(plane, new X.THREE.Vector3()); }
const objPos = id => id === 'googoo' ? X.robot.position : grp(id).position;

let drag = null;
function onDown(e) {
  if (mode === 'buttons' || mode === 'paint') return;
  const T = X.THREE;
  if (mode === 'camera') return; // the camera tab works with its sliders (free camera still orbits)
  if (mode === 'walls') {
    const rc = ray(); rc.setFromCamera(ndc(e), X.camera);
    const h = rc.intersectObjects([X.back, ...X.wallSides, X.wood])[0];
    if (!h) { if (!free) { selWall = null; renderRight(); showBox(); } return; }
    selWall = h.object === X.back ? 'back' : h.object === X.wallSides[0] ? 'left' : h.object === X.wallSides[1] ? 'right' : 'floor'; renderRight(); showBox();
    let edge = null;
    if (selWall === 'floor') { const f = floorOf(), p = h.point; edge = Object.entries({ left: Math.abs(p.x - f.left), right: Math.abs(p.x - f.right), back: Math.abs(p.z - f.back), front: Math.abs(p.z - f.front) }).sort((a, b) => a[1] - b[1])[0][0]; }
    drag = { wall: selWall, edge, key: 'wall' + Date.now(), plane: new T.Plane(new T.Vector3(0, 1, 0), 0) };
    e.stopImmediatePropagation(); ov.setPointerCapture(e.pointerId); ov.classList.add('grab'); return;
  }
  const id = pick(e);
  if (!id) { if (!free) select(null); return; }
  if (bd() && W.eval('PNT') && (id === 'googoo' || (ori() || {}).place?.[id])) { status('This is a painted room: move Googoo and the 3D toys in the 🖼️ Painting tab (their place is a spot on the picture).', 'dirty'); return; }
  if (id !== sel) select(id); e.stopImmediatePropagation();
  const o = objPos(id), y = id === 'googoo' ? 0 : o.y;
  if (e.shiftKey && id !== 'googoo') { // Shift+drag: height
    const n = new T.Vector3(); X.camera.getWorldDirection(n); n.y = 0; n.normalize();
    const plane = new T.Plane().setFromNormalAndCoplanarPoint(n, o), h = planeHit(e, plane);
    drag = { id, key: 'h' + Date.now(), plane, height: true, dy: h ? h.y - y : 0 };
  } else {
    const plane = new T.Plane(new T.Vector3(0, 1, 0), -y), h = planeHit(e, plane), p = propOf(id);
    drag = { id, key: 'm' + Date.now(), plane, ox: h ? h.x - o.x : 0, oz: h ? h.z - o.z : 0, z0: o.z, x0: o.x, wall: p && p.wall };
  }
  ov.setPointerCapture(e.pointerId); ov.classList.add('grab');
}
function onMove(e) {
  if (!drag) return onBtnMove(e);
  const h = planeHit(e, drag.plane); if (!h) return;
  if (drag.wall && !drag.id) { // a wall or the floor
    const r = room();
    if (drag.wall === 'floor') return change(() => { const f = walls(r).floorRect = { ...floorOf(r) }; f[drag.edge] = r2(drag.edge === 'left' || drag.edge === 'right' ? h.x : h.z); }, drag.key, 'walls');
    const v = drag.wall === 'back' ? Math.min(-1.5, Math.max(-14, h.z)) : drag.wall === 'left' ? Math.min(-2, Math.max(-16, h.x)) : Math.max(2, Math.min(16, h.x));
    return change(() => { const w = walls(r); w.floorRect = { ...floorOf(r) }; w[drag.wall] = r2(v); }, drag.key, 'walls'); // the floor stays where it is
  }
  if (drag.id === 'googoo') return change(() => { gooSet('x', h.x - drag.ox); gooSet('z', h.z - drag.oz); }, drag.key, 'goo');
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
function resizeSel(f) {
  if (sel === 'googoo') return change(() => gooSet('s', Math.min(3, Math.max(.3, gooView().s * f))), 'gs', 'goo');
  const p = propOf(sel); if (p && !p.builtin) change(() => setVal(p, 'k', view(p).k * f), 'size' + sel);
}

// Googoo's place and size in this room (upright-phone values when "upright phones only" is ticked)
function gooView() { const g = L.rooms[room()].googoo || {}, p = usePt() ? g.portrait || {} : {}; return { x: p.x ?? g.x ?? 0, z: p.z ?? g.z ?? 0, ry: p.ry ?? g.ry ?? 0, s: p.s ?? g.s ?? 1 }; }
function gooSet(k, v) { const r = room(), g = L.rooms[r].googoo = L.rooms[r].googoo || {}; v = r2(v); if (usePt()) (g.portrait = g.portrait || {})[k] = v; else g[k] = v; }
// values the current view shows (portrait-only edits read/write p.portrait)
function view(p) {
  const u = grp(p.id)?.userData || {}, pt = usePt() ? p.portrait || {} : {};
  return { x: pt.x ?? (p.wall === 'left' ? u.x0 ?? 0 : p.x ?? 0), z: pt.z ?? (p.wall === 'back' ? u.z0 ?? 0 : p.z ?? 0), y: pt.y ?? p.y ?? 0, ry: pt.ry ?? p.ry ?? 0, k: (p.k || 1) * (pt.k || 1) };
}
// x/z arrive as world positions from drags; the shared x is stored before the portrait squeeze
function setVal(p, key, v, world = true) {
  v = r2(v);
  if (p.builtin) { if (key === 'k') return; if (key === 'x' && world && isPortrait()) v = r2(v / sq()); p[key] = v; return; }
  if (usePt()) { const pt = p.portrait = p.portrait || {}; pt[key] = key === 'k' ? r2(Math.max(.01, v) / p.k) : v; return; }
  if (key === 'k') { p.k = Math.max(.01, v); return; }
  // a piece against the back wall leaves it when its z changes, one against the left wall when its x changes
  if (key === 'x') { if (p.wall === 'left') delete p.wall; if (world && isPortrait() && !p.noSqueeze) v = r2(v / sq()); }
  if (key === 'z' && p.wall === 'back') delete p.wall;
  p[key] = v;
}

// ---------- selection ----------
function select(id) {
  sel = id; selBtn = null; const p = id && id !== 'googoo' && propOf(id), g = id === 'googoo' && L.rooms[room()].googoo;
  ptMode = !!((p && p.portrait || g && g.portrait) && isPortrait());
  showBox(); renderLeft(); renderRight();
}
function showBox() {
  if (!box) return;
  const o = mode === 'props' && sel ? (sel === 'googoo' ? X.robot : grp(sel)) : mode === 'walls' && selWall ? ({ back: X.back, left: X.wallSides[0], right: X.wallSides[1], floor: X.wood })[selWall] : null;
  box.visible = !!(o && o.visible); if (o) box.setFromObject(o);
}
function tick() { showBox(); if (X && X.furnGroup.children.length !== tick.n) { tick.n = X.furnGroup.children.length; syncProps(); renderLeft(); } }

// ---------- keyboard ----------
function onKey(e) {
  const t = e.target, typing = t && (t.tagName === 'INPUT' && t.type !== 'range' && t.type !== 'checkbox' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA');
  const k = e.key.toLowerCase(), ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && k === 's') { e.preventDefault(); return doSave(); }
  if (ctrl && k === 'z' && !e.shiftKey) { if (typing) return; e.preventDefault(); return doUndo(); }
  if (ctrl && (k === 'y' || k === 'z' && e.shiftKey)) { if (typing) return; e.preventDefault(); return doRedo(); }
  if (typing || mode !== 'props' || !sel || ctrl) return;
  const st = e.shiftKey ? .25 : .05;
  if (sel === 'googoo') {
    const v = gooView(), G = (key, val) => () => change(() => gooSet(key, val), 'gk' + key, 'goo');
    const act = { r: G('ry', v.ry + (e.shiftKey ? -15 : 15) * DEG), escape: () => select(null), '+': () => resizeSel(1.05), '=': () => resizeSel(1.05), '-': () => resizeSel(1 / 1.05),
      arrowleft: G('x', v.x - st), arrowright: G('x', v.x + st), arrowup: G('z', v.z - st), arrowdown: G('z', v.z + st) }[k];
    if (act) { e.preventDefault(); act(); } return;
  }
  const p = propOf(sel); if (!p) return; const v = view(p);
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

// ---------- props: add, duplicate, hide, remove ----------
function newId(file) {
  const base = nice(file).toLowerCase().replace(/[^a-z0-9]+/g, '_'), used = new Set([...PRIM, ...ROOMS.flatMap(x => L.rooms[x].props.map(p => p.id))]);
  let id = base, n = 2; while (used.has(id)) id = base + '_' + n++; return id;
}
function addProp(file) {
  const r = room(), info = propsList.find(p => p.name === file) || {}, id = newId(file);
  const k = { S: .3, M: .5, L: .7 }[info.class] || .5; // new pieces start at the back on the right, out of Googoo's way
  change(() => L.rooms[r].props.push({ id, file, k, x: 2.6, z: -3, ry: 0, castShadow: info.class === 'L', hidden: false }), '', 'all');
  select(id); status(`Added ${nice(file)}. Drag it where you want it.`);
}
function duplicate(id) {
  const p = propOf(id), r = room(); if (!p || p.builtin) return; const q = clone(p); q.id = newId(p.file); q.x = r2((view(p).x || 0) + .8); delete q.wall; if (q.z == null) q.z = r2(view(p).z);
  change(() => L.rooms[r].props.push(q), '', 'all'); select(q.id); status(`Added another ${nice(p.file).toLowerCase()}.`);
}
function removeProp(id) {
  const p = propOf(id); if (!p) return;
  if (BUILTIN.includes(id)) { change(() => { p.hidden = true; }, '', 'all'); return status(`${nameOf(p)} is hidden (it stands in for a built-in piece of the room). Use 👁 to show it again.`); }
  change(() => { for (const r of ROOMS) L.rooms[r].props = L.rooms[r].props.filter(q => q.id !== id); }, '', 'all');
  if (sel === id) select(null);
}
function toggleHidden(id) { const p = propOf(id); change(() => { p.hidden = !p.hidden; }, '', 'all'); }

// ---------- buttons mode: drag rail buttons, the top bar and the room tabs (in rows), or anywhere (free placement) ----------
let bdrag = null;
const SAFE = { up: { t: 47, b: 34, l: 0, r: 0 }, side: { t: 0, b: 21, l: 47, r: 47 }, small: { t: 20, b: 0, l: 0, r: 0 }, ipad: { t: 24, b: 20, l: 0, r: 0 } }; // the real devices' notch / home-bar insets
const BTNQ = '.col .rb,#nav .rb,#top>*,#parentBtn,#free>*';
const fidOf = b => b.dataset.r ? 'tab-' + b.dataset.r : b.id;
const freeMap = () => (L.ui.free || {})[camKey()];
const cardsUp = () => ['say', 'book'].includes(W.eval('scr')) || !W.document.getElementById('deck').hidden;
const shownBtns = () => [...W.document.querySelectorAll(BTNQ)].filter(x => !x.hidden && !x.closest('#btns') && x.getBoundingClientRect().width > 0);
// % of the safe area (inside the notch / home bar), anchored to the nearest edges
function freePos(r) { const S = SAFE[device] || {}, Wd = W.innerWidth - S.l - S.r, H = W.innerHeight - S.t - S.b, L0 = r.left - S.l, T0 = r.top - S.t;
  const ax = L0 + r.width / 2 < Wd / 2 ? 'l' : 'r', ay = T0 + r.height / 2 < H / 2 ? 't' : 'b';
  return { ax, ay, x: r2((ax === 'l' ? L0 : Wd - L0 - r.width) / Wd * 100), y: r2((ay === 't' ? T0 : H - T0 - r.height) / H * 100) }; }
function freeStart() { // every button where it is now becomes a free one, so nothing jumps
  if (cardsUp()) return status('Card screens keep their buttons in rows. Pick a room first.', 'dirty');
  // the preview has no notch: buttons that would sit under it (top bar, room tabs) start just inside the safe area, where the phone shows them today
  const S = SAFE[device] || {}, Wd = W.innerWidth, H = W.innerHeight, F = {};
  for (const b of shownBtns()) { const r = b.getBoundingClientRect(), left = Math.min(Math.max(r.left, S.l + 10), Wd - S.r - 10 - r.width), top = Math.min(Math.max(r.top, S.t + 10), H - S.b - 10 - r.height);
    F[fidOf(b)] = freePos({ left, top, width: r.width, height: r.height, right: left + r.width, bottom: top + r.height }); }
  change(() => { (L.ui.free = L.ui.free || {})[camKey()] = F; }, '', 'ui'); renderRight();
}
function freeBack() { change(() => { if (L.ui.free) { delete L.ui.free[camKey()]; if (!Object.keys(L.ui.free).length) delete L.ui.free; } }, '', 'ui'); renderRight(); }
function onBtnDown(e) {
  if (mode !== 'buttons') return;
  const b = e.target.closest && e.target.closest(BTNQ); if (!b) return;
  e.stopImmediatePropagation(); e.preventDefault();
  const g = b.closest('#nav') || b.dataset.r ? 'nav' : b.closest('#top') || ['score', 'bTalk', 'parentBtn'].includes(b.id) ? 'top' : 'rails';
  selBtn = b.id || b.dataset.r; bscr = g === 'rails' ? screenKey() : g; markBtn(); renderRight();
  const F = freeMap();
  if (F && !cardsUp()) { // free placement: drag anywhere
    const id = fidOf(b), r = b.getBoundingClientRect();
    if (!F[id]) change(() => { F[id] = freePos(r); }, '', 'ui');
    bdrag = { b, free: true, id, ox: e.clientX - r.left, oy: e.clientY - r.top }; return;
  }
  if (b.id !== 'parentBtn') bdrag = { b, g, moved: false };
}
// snap to an 8 px grid, the screen edges / safe area, and the other buttons' centres; returns [position, guide line or null]
function snap(v, size, edges, centres) {
  let out = Math.round(v / 8) * 8, guide = null, best = 7;
  for (const t of edges) if (Math.abs(v - t) < best) { best = Math.abs(v - t); out = t; guide = null; }
  for (const c of centres) if (Math.abs(v + size / 2 - c) < best) { best = Math.abs(v + size / 2 - c); out = c - size / 2; guide = c; }
  return [out, guide];
}
function guides(gx, gy) {
  const d = W.document;
  for (const [k, v] of [['edGx', gx], ['edGy', gy]]) {
    let g = d.getElementById(k); if (!g) { g = d.createElement('div'); g.id = k; g.className = 'edG'; d.body.appendChild(g); }
    g.style.display = v == null ? 'none' : 'block';
    Object.assign(g.style, k === 'edGx' ? { left: v + 'px', top: '0', width: '1px', height: '100%' } : { top: v + 'px', left: '0', height: '1px', width: '100%' });
  }
}
function onBtnMove(e) {
  if (!bdrag) return; const d = W.document, b = bdrag.b;
  if (bdrag.free) {
    const r = b.getBoundingClientRect(), Wd = W.innerWidth, H = W.innerHeight, S = SAFE[device] || {}, others = shownBtns().filter(x => x !== b).map(x => x.getBoundingClientRect());
    const [x, gx] = snap(e.clientX - bdrag.ox, r.width, [S.l + 12, Wd - S.r - 12 - r.width], others.map(o => o.left + o.width / 2));
    const [y, gy] = snap(e.clientY - bdrag.oy, r.height, [S.t + 10, H - S.b - 10 - r.height], others.map(o => o.top + o.height / 2));
    const z = parseFloat(W.getComputedStyle(b).zoom) || 1; b.style.left = x / z + 'px'; b.style.top = y / z + 'px'; guides(gx, gy); bdrag.moved = true; return;
  }
  if (bdrag.g === 'rails') {
    const rail = d.getElementById(e.clientX < W.innerWidth / 2 ? 'colL' : 'colR'), others = [...rail.children].filter(x => x !== b && !x.hidden);
    const before = others.find(x => { const r = x.getBoundingClientRect(); return e.clientY < r.top + r.height / 2; });
    if (b.parentNode !== rail || b.nextElementSibling !== (before || null)) { rail.insertBefore(b, before || null); bdrag.moved = true; }
    return;
  }
  const box = b.parentNode, before = [...box.children].filter(x => x !== b).find(x => { const r = x.getBoundingClientRect(); return e.clientX < r.left + r.width / 2; });
  if (b.nextElementSibling !== (before || null)) { box.insertBefore(b, before || null); bdrag.moved = true; }
}
const hit = (a, b, m = 1) => a.left < b.right - m && b.left < a.right - m && a.top < b.bottom - m && b.top < a.bottom - m;
function onBtnUp() {
  if (!bdrag) return; const { moved, g, free, b, id } = bdrag; bdrag = null; if (!moved) return;
  if (free) {
    guides(null, null); const r = b.getBoundingClientRect();
    if (shownBtns().some(x => x !== b && hit(r, x.getBoundingClientRect()))) { W.applyFree(); status("Buttons can't sit on top of each other: it went back to where it was.", 'dirty'); return; }
    change(() => { freeMap()[id] = freePos(r); }, '', 'ui'); markBtn(); renderRight(); return;
  }
  const d = W.document, k = screenKey(), ids = id => [...d.getElementById(id).children].map(x => x.id);
  if (g === 'rails') change(() => { L.ui.screens[k] = { left: ids('colL'), right: ids('colR') }; }, '', 'ui');
  else if (g === 'nav') change(() => { ui('nav').order = [...d.querySelectorAll('#nav .rb')].map(x => x.dataset.r); }, '', 'ui');
  else change(() => { ui('top').order = ids('top'); }, '', 'ui');
  markBtn(); renderRight();
}
// red outline: a free button over Googoo's face, or under a phone's notch / home bar
function freeWarn() {
  if (!W || !X || mode !== 'buttons') return; const d = W.document, S = SAFE[device] || {}, Wd = W.innerWidth, H = W.innerHeight;
  const f = W.eval("(()=>{const v=new THREE.Vector3();headObj().getWorldPosition(v);const s=v.clone().project(camera),e=v.clone().add(new THREE.Vector3(RB.h*HOME.s*.17,0,0)).project(camera);return [(s.x+1)/2*innerWidth,(1-s.y)/2*innerHeight,Math.abs(e.x-s.x)/2*innerWidth]})()");
  const face = { left: f[0] - f[2], right: f[0] + f[2], top: f[1] - f[2], bottom: f[1] + f[2] };
  for (const b of d.querySelectorAll('#free>*')) { const r = b.getBoundingClientRect(); b.classList.toggle('edWarn', hit(r, face) || r.top < S.t || r.bottom > H - S.b || r.left < S.l || r.right > Wd - S.r); }
}
setInterval(freeWarn, 300);
const ui = k => L.ui[k] = L.ui[k] || {};
function markBtn() { if (!W) return; W.document.querySelectorAll('.edSel').forEach(x => x.classList.remove('edSel')); if (mode === 'buttons' && selBtn) (W.document.getElementById(selBtn) || W.document.querySelector(`[data-r="${selBtn}"]`))?.classList.add('edSel'); }
const btnLabel = id => { const b = W && W.document.getElementById(id); return b ? [b.textContent.trim(), b.getAttribute('aria-label')] : ['', id]; };

// ---------- camera ----------
async function loadScript(src) { return new Promise((res, rej) => { const s = W.document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej; W.document.head.appendChild(s); }); }
async function setFree(on) {
  if (on && !orbit) {
    try { await loadScript(CDN + 'OrbitControls.js'); } catch (e) { return status('Could not load the free camera (no internet?)', 'dirty'); }
    orbit = new X.THREE.OrbitControls(X.camera, ov); orbit.enableDamping = false;
    orbit.addEventListener('change', () => { if (free) freeCam = { p: X.camera.position.clone(), q: X.camera.quaternion.clone() }; });
  }
  free = on; $('freeCam').classList.toggle('on', on); $('gameCam').classList.toggle('on', !on);
  if (orbit) orbit.enabled = on;
  if (on) { const H = W.eval('HOME'); orbit.target.set(H.x, 2 * H.s, H.z - 1.5); freeCam = null; X.camera.clearViewOffset(); X.camera.updateProjectionMatrix(); orbit.update(); freeCam = { p: X.camera.position.clone(), q: X.camera.quaternion.clone() }; }
  else W.resize();
}
function restoreFree() { if (!freeCam) return; const c = X.camera; c.clearViewOffset(); c.position.copy(freeCam.p); c.quaternion.copy(freeCam.q); c.updateProjectionMatrix(); c.updateMatrixWorld(); }
// the saved view of this room for this kind of screen (missing = automatic)
const camView = () => (L.rooms[room()].camera || {})[camKey()];
function camVals() { const V = camView() || {}, A = W.eval('CAMAUTO') || { pitch: 10 }; return { zoom: V.zoom ?? 1, height: V.height ?? 0, yaw: V.yaw ?? 0, pitch: V.pitch ?? r100(A.pitch) }; }
function camSet(k, v) { const r = room(), c = L.rooms[r].camera = L.rooms[r].camera || {}, cur = camVals(); c[camKey()] = { ...cur, ...(c[camKey()] || {}), [k]: r2(v) }; }
function camFromFree() { // the free camera's angle, as a saved view around Googoo
  const H = W.eval('HOME'), RB = W.eval('RB'), A = W.eval('CAMAUTO'), V = camVals(), cy = RB.y0 + RB.h / 2, ty = cy + V.height * RB.h;
  const p = X.camera.position.clone().sub(new X.THREE.Vector3(H.x, 0, H.z)).sub(new X.THREE.Vector3(0, ty, 0)), D = p.length();
  change(() => { const r = room(); (L.rooms[r].camera = L.rooms[r].camera || {})[camKey()] = { zoom: r2(D / A.D), height: V.height, yaw: r2(Math.atan2(p.x, p.z) / DEG), pitch: r2(Math.asin(p.y / D) / DEG) }; }, '', 'cam');
  setFree(false); renderRight();
}

// ---------- device size ----------
function setDevice(k) {
  device = k; const [, w, h] = DEVICES[k]; if (W) { W.__safe = SAFE[k]; } frame.style.width = w + 'px'; frame.style.height = h + 'px'; $('device').value = k; fit();
  if (!isPortraitSize(k)) ptMode = false; setTimeout(() => { renderRight(); }, 300);
}
const isPortraitSize = k => DEVICES[k][1] < DEVICES[k][2];
function fit() { const m = $('main'), [, w, h] = DEVICES[device], s = Math.min((m.clientWidth - 40) / w, (m.clientHeight - 40) / h, 1.5); frame.style.transform = `scale(${s})`; Object.assign($('fbox').style, { width: w * s + 'px', height: h * s + 'px' }); }
addEventListener('resize', fit);

// ---------- top bar ----------
$('rooms').onclick = async e => { const r = e.target.dataset.room; if (!r || !X) return; await goRoom(r); };
async function goRoom(r) { select(null); selWall = null; await W.setRoom(r); for (const p of L.rooms[r].props) if (!grp(p.id)) inflight.add(p.id); apply('props'); renderTop(); renderLeft(); renderRight(); }
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
  renderPaint();
  if (m === 'camera' && free) setFree(false);
  sel = null; selWall = null; selBtn = null; bscr = null; showBox(); markBtn(); renderLeft(); renderRight();
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
  if (mode !== 'props') {
    el.innerHTML = {
      walls: `<h2>Walls & floor</h2><p class="hint">Click the back, left or right wall in the picture, then drag it in or out to make the room smaller or bigger. Moving a wall never moves the floor.</p><p class="hint">Click the floor and drag near one of its edges to make the floor bigger or smaller. Numbers and colours are on the right.</p><p class="hint">Pieces standing against a wall move with it.</p>`,
      buttons: `<h2>Buttons</h2><p class="hint">Drag a round button in the picture to change the order: up and down on the sides (or across to the other side), left and right in the top bar and the room tabs.</p><p class="hint">Click a button to change its colour, or to hide it. Size and shape are on the right.</p><p class="hint">Each screen has its own side buttons: pick the screen on the right. The top bar and the room tabs are the same everywhere.</p>`,
      paint: `<h2>Painting</h2><p class="hint">A painted room shows a painting instead of 3D walls and furniture; only Googoo and the toys he plays with stay 3D.</p><p class="hint">Drag the marks on the picture: <b>✛</b> the spot that stays in view when a phone cuts the picture, <b>pink line</b> eye level (where the floor would disappear), <b>blue line</b> where the back wall meets the floor, <b>yellow</b> Googoo's feet (top dot = his height), <b>red box</b> the rug (the ball stays on it), <b>green boxes</b> empty shelf compartments (library: one book in each), <b>green dots</b> the 3D toys, <b>purple boxes</b> tap zones (a painted thing says its word, or the painted bed / lamp does what the real one did).</p><p class="hint">Upright phones and sideways screens each have their own picture and marks: change the screen size at the top for the other one.</p>`,
      camera: `<h2>Camera</h2><p class="hint">Each room can have its own view: one for upright phones and one for everything else (sideways phones, iPads). Change the screen size at the top to set the other one.</p><p class="hint">Rooms without their own view are "automatic": the camera fits Googoo by itself. Card games and stories always use the automatic view.</p>` }[mode];
    return;
  }
  const r = room(), here = propsIn(r), gooOn = sel === 'googoo';
  const files = propsList.length ? propsList : [...new Set(ROOMS.flatMap(x => L.rooms[x].props.filter(p => p.file).map(p => p.file)))].map(name => ({ name }));
  const keepFocus = document.activeElement && document.activeElement.id === 'search';
  if (!el.querySelector('#search')) {
    el.innerHTML = `<h2>Props</h2><input id="search" type="search" placeholder="Search props…"><div class="chips">${[['all', 'All'], ['furniture', 'Furniture'], ['toys', 'Toys'], ['decor', 'Decor'], ['here', 'In this room'], ['hidden', 'Hidden']].map(([k, t]) => `<button class="eb" data-chip="${k}">${t}</button>`).join('')}</div><div id="plist"></div>
    <p class="hint">Click a piece in the picture to select it. Drag = move on the floor · Shift+drag = height · wheel or +/- = size · R = turn · arrows = nudge · Delete = remove.</p>`;
    el.querySelector('#search').oninput = e => { query = e.target.value.toLowerCase(); renderLeft(); };
    el.querySelector('.chips').onclick = e => { if (e.target.dataset.chip) { chip = e.target.dataset.chip; renderLeft(); } };
  }
  el.querySelector('h2').textContent = 'Props in the ' + ROOM_NAME[r].toLowerCase();
  el.querySelectorAll('[data-chip]').forEach(b => b.classList.toggle('on', b.dataset.chip === chip));
  const info = f => propsList.find(x => x.name === f) || {}, okChip = (c, placed, hidden) => chip === 'all' || chip === c || chip === 'here' && placed || chip === 'hidden' && hidden;
  const match = t => !query || t.toLowerCase().includes(query);
  // one row per piece: the ones in this room (select, duplicate, hide, remove), then the ones you can add
  const count = {}, placed = here.map(p => { const n = nameOf(p); count[n] = (count[n] || 0) + 1; return [p, count[n] > 1 ? `${n} ${count[n]}` : n]; }).sort((a, b) => a[1].localeCompare(b[1]));
  const rows = [];
  if (match('googoo') && (chip === 'all' || chip === 'here')) rows.push(`<div class="prow placed${gooOn ? ' sel' : ''}" data-sel="googoo"><span class="ic">🤖</span><span class="nm">Googoo<small>place and size in this room</small></span></div>`);
  for (const [p, n] of placed) {
    const c = cat(p.file), i = info(p.file); if (!match(n) || !okChip(c, true, p.hidden)) continue;
    rows.push(`<div class="prow placed${p.id === sel ? ' sel' : ''}${p.hidden ? ' off' : ''}" data-sel="${p.id}"><span class="ic">${p.builtin ? PRIMS[p.id][2] : ICON[c]}</span><span class="nm">${n}<small>${p.hidden ? 'hidden · ' : ''}${i.class ? i.class + ' · ' + (i.tris / 1000).toFixed(1) + 'k triangles' : p.builtin ? 'built-in piece' : ''}</small></span>${p.builtin ? '' : `<button class="ib" data-dup="${p.id}" title="Add another one">⧉</button>`}<button class="ib" data-eye="${p.id}" title="${p.hidden ? 'Show' : 'Hide'}">${p.hidden ? '🙈' : '👁'}</button><button class="ib" data-del="${p.id}" title="Remove">🗑</button></div>`);
  }
  const unplaced = files.filter(f => !here.some(p => p.file === f.name) && match(nice(f.name)) && okChip(cat(f.name), false, false)).sort((a, b) => nice(a.name).localeCompare(nice(b.name)));
  if (unplaced.length) rows.push(`<div class="sub">Add to this room</div>`);
  for (const f of unplaced) rows.push(`<div class="prow new"><span class="ic">${ICON[cat(f.name)]}</span><span class="nm">${nice(f.name)}<small>${f.class ? f.class + ' · ' + (f.tris / 1000).toFixed(1) + 'k triangles' : ''}</small></span><button class="ib" data-add="${f.name}" title="Add to this room">➕</button></div>`);
  const list = el.querySelector('#plist'); list.innerHTML = rows.join('') || '<p class="hint">Nothing matches.</p>';
  list.onclick = e => { const t = e.target.closest('[data-add],[data-eye],[data-del],[data-dup],[data-sel]'); if (!t) return;
    if (t.dataset.add) addProp(t.dataset.add); else if (t.dataset.eye) toggleHidden(t.dataset.eye); else if (t.dataset.del) removeProp(t.dataset.del); else if (t.dataset.dup) duplicate(t.dataset.dup); else select(t.dataset.sel); };
  if (keepFocus) el.querySelector('#search').focus();
}

// ---------- right panel ----------
function field(label, key, min, max, step, val) {
  return `<div class="field"><label>${label}</label><input type="range" data-k="${key}" min="${min}" max="${max}" step="${step}" value="${val}"><input type="number" data-k="${key}" step="${step}" value="${val}"></div>`;
}
const ptBox = (por, has) => `<label class="check"><input type="checkbox" id="ptOnly" ${usePt() ? 'checked' : ''} ${por ? '' : 'disabled'}><span>Upright phones only<br><small class="hint">${por ? (has ? 'It has its own place on upright phones.' : 'Tick to give it a different place on upright phones.') : 'Pick an upright screen size to use this.'}</small></span></label>`;
function renderRight() {
  const el = $('right'); if (!L || !X) return;
  if (mode === 'walls') return renderWalls(el);
  if (mode === 'buttons') return renderButtons(el);
  if (mode === 'camera') return renderCamera(el);
  if (mode === 'paint') return renderPaintPanel(el);
  if (sel === 'googoo') return renderGoo(el);
  const p = sel && propOf(sel);
  if (!p) { el.innerHTML = `<h2>Nothing selected</h2><p class="hint">Click a piece of furniture, a toy or Googoo in the picture, or pick one in the list on the left.</p>`; return; }
  const v = view(p), por = isPortrait();
  el.innerHTML = `<h2>${nameOf(p)}</h2>
   ${p.builtin ? '' : ptBox(por, p.portrait)}
   ${p.builtin ? '' : pctUnit(p) ? field(p.flatten ? 'Length (% of Googoo)' : 'Height (% of Googoo)', 'pct', 5, 300, 1, Math.round(v.k * pctUnit(p))) : field('Size', 'k', .05, 2.5, .01, r100(v.k))}
   ${p.builtin && p.ry == null ? '' : field('Turn (°)', 'ry', -180, 180, 1, Math.round(v.ry / DEG))}
   <div class="field"><label>Sits on</label><select class="eb" id="on"><option value="">Nothing (stands free)</option>${propsIn(room()).filter(q => q.id !== p.id && !q.flatten).map(q => `<option value="${q.id}">${nameOf(q)}</option>`).join('')}</select><span></span></div>
   ${onOf(p) ? '' : field('Lift (height)', 'y', -.5, 6, .05, r100(v.y))}
   ${field('Left / right', 'x', -10, 10, .05, r100(v.x))}
   ${field('Back / front', 'z', -14, 8, .05, r100(v.z))}
   ${p.builtin ? '' : `<div class="field"><label>Against a wall</label><select class="eb" id="wall" ${usePt() ? 'disabled' : ''}><option value="">No</option><option value="back">Back wall</option><option value="left">Left wall</option></select><span></span></div>
   <label class="check"><input type="checkbox" id="shadow" ${p.castShadow ? 'checked' : ''}><span>Casts a shadow<br><small class="hint">Only for big furniture (each shadow costs speed on phones).</small></span></label>`}
   <div class="row"><button class="eb" id="copy">Copy position</button><button class="eb" id="paste" ${clip ? '' : 'disabled'}>Paste position</button></div>
   ${usePt() && p.portrait ? '<div class="row"><button class="eb" id="ptClear">Use the same place as on other screens</button></div>' : ''}
   <div class="row"><button class="eb" id="hide">${p.hidden ? '👁 Show' : '🙈 Hide'}</button><button class="eb warn" id="del">🗑 Remove</button></div>
   ${SHELVES[p.id] ? '<div id="booksBox"></div>' : ''}`;
  const q = s => el.querySelector(s);
  if (q('#wall')) q('#wall').value = p.wall || ''; q('#on').value = onOf(p) || '';
  q('#on').onchange = e => { change(() => { p.on = e.target.value || null; }, '', 'props'); renderRight(); };
  el.oninput = e => { let k = e.target.dataset.k; if (!k) return; let val = parseFloat(e.target.value); if (isNaN(val)) return; if (k === 'ry') val *= DEG;
    if (k === 'pct') { k = 'k'; val /= pctUnit(p); }
    change(() => setVal(p, k, val, false), 'f' + k + sel); el.querySelectorAll(`[data-k="${k}"]`).forEach(i => { if (i !== e.target) i.value = e.target.value; }); };
  if (q('#ptOnly')) q('#ptOnly').onchange = e => { ptMode = e.target.checked; renderRight(); };
  if (q('#wall')) q('#wall').onchange = e => change(() => { const w = e.target.value, vv = view(p); if (w) p.wall = w; else { p.x = r2(vv.x); p.z = r2(vv.z); delete p.wall; } }, '', 'props');
  if (q('#shadow')) q('#shadow').onchange = e => change(() => { p.castShadow = e.target.checked; });
  q('#copy').onclick = () => { clip = view(p); status('Position copied. Pick another view or piece and press Paste.'); renderRight(); };
  q('#paste').onclick = () => change(() => { for (const k of ['x', 'z', 'y', 'ry', 'k']) setVal(p, k, clip[k], false); }, '');
  if (q('#ptClear')) q('#ptClear').onclick = () => { change(() => { delete p.portrait; }, ''); renderRight(); };
  q('#hide').onclick = () => toggleHidden(p.id);
  q('#del').onclick = () => removeProp(p.id);
  if (q('#booksBox')) renderBooks(q('#booksBox'));
}
// library: which books stand on the big shelf and which on the small shelf (book bin), in order (drag to reorder or across; ⇄ moves to the other shelf)
function renderBooks(el) {
  const items = clone(W.eval('libAll().map(i=>({key:i.key,pic:i.pic,name:i.name}))')), A = clone(L.rooms.library.books || W.eval('libAssign()')), by = Object.fromEntries(items.map(i => [i.key, i]));
  const NAME = { big: 'Big shelf (bookshelf)', small: 'Small shelf (book bin)' };
  const row = k => { const i = by[k]; return i ? `<div class="brow" draggable="true" data-key="${k}" style="cursor:grab"><span class="em">${i.pic}</span><span class="nm">${k.startsWith('story:') ? 'Story: ' : ''}${i.name}</span><button class="ib eb" data-mv="${k}" title="Move to the other shelf">⇄</button></div>` : ''; };
  el.innerHTML = `<h2 style="margin-top:16px">Books on the shelves</h2><p class="hint">Drag a book up or down to change the order, or onto the other list. ⇄ moves it to the other shelf. The books follow the shelf when you move or resize it.</p>` +
    ['big', 'small'].map(sh => `<h2>${NAME[sh]}</h2><div class="blist" data-shelf="${sh}" style="min-height:28px">${A[sh].map(row).join('') || '<p class="hint">none</p>'}</div>`).join('');
  const set = fn => { change(() => { const B = clone(A); fn(B); L.rooms.library.books = B; }, '', 'all'); renderBooks(el); };
  el.onclick = e => { const k = e.target.dataset.mv; if (k) set(B => { const from = B.big.includes(k) ? 'big' : 'small', to = from === 'big' ? 'small' : 'big'; B[from] = B[from].filter(x => x !== k); B[to].push(k); }); };
  let dragKey = null;
  el.ondragstart = e => { dragKey = e.target.dataset.key; e.dataTransfer.effectAllowed = 'move'; };
  el.ondragover = e => { if (dragKey && e.target.closest('[data-shelf]')) e.preventDefault(); };
  el.ondrop = e => { const list = e.target.closest('[data-shelf]'); if (!dragKey || !list) return; e.preventDefault(); const k = dragKey, before = e.target.closest('[data-key]')?.dataset.key; dragKey = null; if (before === k) return;
    set(B => { B.big = B.big.filter(x => x !== k); B.small = B.small.filter(x => x !== k); const L2 = B[list.dataset.shelf], at = before ? L2.indexOf(before) : -1; if (at < 0) L2.push(k); else L2.splice(at, 0, k); }); };
}
function renderGoo(el) {
  const v = gooView(), g = L.rooms[room()].googoo || {};
  el.innerHTML = `<h2>Googoo in the ${ROOM_NAME[room()].toLowerCase()}</h2>${ptBox(isPortrait(), g.portrait)}
   ${field('Size', 's', .3, 3, .01, r100(v.s))}${field('Turn (°)', 'ry', -180, 180, 1, Math.round(v.ry / DEG))}
   ${field('Left / right', 'x', -8, 8, .05, r100(v.x))}${field('Back / front', 'z', -12, 6, .05, r100(v.z))}
   <p class="hint">The camera follows him, so he still fills the screen. This is also where he walks back to after playing ball.</p>
   <div class="row"><button class="eb" id="gooReset">Back to the middle, normal size</button></div>`;
  el.oninput = e => { const k = e.target.dataset.k; if (!k) return; let val = parseFloat(e.target.value); if (isNaN(val)) return; if (k === 'ry') val *= DEG;
    change(() => gooSet(k, val), 'g' + k, 'goo'); el.querySelectorAll(`[data-k="${k}"]`).forEach(i => { if (i !== e.target) i.value = e.target.value; }); };
  el.querySelector('#ptOnly').onchange = e => { ptMode = e.target.checked; renderRight(); };
  el.querySelector('#gooReset').onclick = () => { change(() => { const r = room(), G = L.rooms[r].googoo; if (!G) return; if (usePt()) delete G.portrait; else { for (const k of ['x', 'z', 'ry', 's']) delete G[k]; } }, '', 'goo'); renderRight(); };
}
function renderCamera(el) {
  const V = camView(), v = camVals(), grpName = camKey() === 'phone' ? 'upright phones' : 'sideways phones and iPads';
  el.innerHTML = `<h2>${ROOM_NAME[room()]}: camera</h2><p class="hint">For <b>${grpName}</b> (change the screen size at the top for the other one). Now: <b>${V ? 'your own view' : 'automatic'}</b>.</p>
   ${field('Zoom', 'zoom', .4, 2.5, .01, r100(v.zoom))}${field('Height', 'height', -.6, .8, .01, r100(v.height))}
   ${field('Turn (°)', 'yaw', -70, 70, 1, Math.round(v.yaw))}${field('Tilt (°)', 'pitch', -10, 70, 1, Math.round(v.pitch))}
   <p class="hint">Zoom: bigger number = further away. Height moves the view up or down. Turn and tilt go around Googoo.</p>
   <div class="row"><button class="eb go" id="camSave">📌 Save this view</button><button class="eb" id="camAuto" ${V ? '' : 'disabled'}>Back to automatic</button></div>
   <div class="row"><select class="eb" id="camTo"><option value="all">All rooms</option>${ROOMS.filter(r => r !== room()).map(r => `<option value="${r}">${ROOM_NAME[r]}</option>`).join('')}</select><button class="eb" id="camCopy" title="Give the chosen rooms this room's view (or automatic) for ${grpName}">Copy view to…</button></div>
   <div class="row"><button class="eb" id="camFree" ${free ? '' : 'disabled'} title="Turn on the free camera at the top, turn the room, then press this">Use the free camera's angle</button></div>
   <p class="hint">Card games and stories keep their own automatic framing.</p>`;
  el.oninput = e => { const k = e.target.dataset.k; if (!k) return; const val = parseFloat(e.target.value); if (isNaN(val)) return;
    change(() => camSet(k, val), 'c' + k, 'cam'); el.querySelectorAll(`[data-k="${k}"]`).forEach(i => { if (i !== e.target) i.value = e.target.value; }); };
  el.querySelector('#camSave').onclick = () => { change(() => camSet('zoom', camVals().zoom), '', 'cam'); status(`View kept for the ${ROOM_NAME[room()].toLowerCase()} on ${grpName}. Press Save to keep it for good.`); renderRight(); };
  el.querySelector('#camAuto').onclick = () => { change(() => { const c = L.rooms[room()].camera; if (c) { delete c[camKey()]; if (!Object.keys(c).length) delete L.rooms[room()].camera; } }, '', 'cam'); renderRight(); };
  el.querySelector('#camFree').onclick = camFromFree;
  el.querySelector('#camCopy').onclick = () => { const to = el.querySelector('#camTo').value, key = camKey(), V = camView(), rs = to === 'all' ? ROOMS.filter(r => r !== room()) : [to];
    change(() => { for (const r of rs) { const R = L.rooms[r]; if (V) (R.camera = R.camera || {})[key] = clone(V); else if (R.camera) { delete R.camera[key]; if (!Object.keys(R.camera).length) delete R.camera; } } }, '', 'all');
    status(`${V ? 'This view' : 'Automatic'} copied to ${rs.map(r => ROOM_NAME[r].toLowerCase()).join(' and ')} (${grpName}). Press Save to keep it.`); };
}
// keep the numbers in the right panel live while dragging in the picture (without rebuilding it)
setInterval(() => {
  if (!L || !X) return; let vals;
  if (mode === 'walls') { const f = floorOf(); vals = { ...walls(), 'f.left': f.left, 'f.right': f.right, 'f.back': f.back, 'f.front': f.front }; }
  else if (mode === 'buttons') return;
  else if (mode === 'camera') { const v = camVals(); vals = { zoom: r100(v.zoom), height: r100(v.height), yaw: Math.round(v.yaw), pitch: Math.round(v.pitch) }; }
  else if (sel === 'googoo') { const v = gooView(); vals = { s: r100(v.s), ry: Math.round(v.ry / DEG), x: r100(v.x), z: r100(v.z) }; }
  else { const p = sel && propOf(sel); if (!p) return; const v = view(p), pu = pctUnit(p); vals = { pct: pu && Math.round(v.k * pu), k: r100(v.k), ry: Math.round(v.ry / DEG), y: r100(v.y), x: r100(v.x), z: r100(v.z) }; }
  document.querySelectorAll('#right [data-k]').forEach(i => { if (i !== document.activeElement && vals[i.dataset.k] != null) i.value = vals[i.dataset.k]; });
}, 200);

function renderWalls(el) {
  const r = room(), w = walls(r), f = floorOf(r);
  el.innerHTML = `<h2>${ROOM_NAME[r]}: walls</h2>
   <p class="hint">${selWall ? `Selected: <b>${selWall === 'floor' ? 'the floor' : selWall + ' wall'}</b>. Drag it in the picture, or type a number.` : 'Click a wall or the floor in the picture to select it.'}</p>
   ${field('Back wall', 'back', -14, -1.5, .05, r100(w.back))}${field('Left wall', 'left', -16, -2, .05, r100(w.left))}${field('Right wall', 'right', 2, 16, .05, r100(w.right))}
   <div class="field"><label>Wall colour</label><input type="color" id="wcol" value="${w.color}"><span></span></div>
   <h2 style="margin-top:16px">Floor</h2>
   ${field('Left edge', 'f.left', -20, -1, .05, r100(f.left))}${field('Right edge', 'f.right', 1, 20, .05, r100(f.right))}${field('Back edge', 'f.back', -20, 0, .05, r100(f.back))}${field('Front edge', 'f.front', 1, 14, .05, r100(f.front))}
   <div class="field"><label>Floor colour</label><input type="color" id="fcol" value="${w.floor}"><span></span></div>
   <p class="hint">The floor keeps its wood pattern (the planks stay the same size); the colour tints it. White = as it is now.</p>`;
  el.oninput = e => { const k = e.target.dataset.k, t = e.target;
    if (k) { const val = parseFloat(t.value); if (isNaN(val)) return;
      change(() => { const ww = walls(r); ww.floorRect = { ...floorOf(r) }; if (k.startsWith('f.')) ww.floorRect[k.slice(2)] = val; else ww[k] = val; }, 'w' + k, 'walls');
      el.querySelectorAll(`[data-k="${k}"]`).forEach(i => { if (i !== t) i.value = t.value; }); }
    if (t.id === 'wcol') change(() => { walls(r).color = t.value; }, 'wcol', 'ui');
    if (t.id === 'fcol') change(() => { walls(r).floor = t.value; }, 'fcol', 'walls'); };
}
function renderButtons(el) {
  const k = bscr || screenKey(), d = W.document;
  const opts = `<div class="field"><label>Edit</label><select class="eb" id="scr">${Object.keys(SCREEN_NAME).map(s => `<option value="${s}">${SCREEN_NAME[s]}</option>`).join('')}</select><span></span></div>`;
  const shapeRow = (cur, key) => `<div class="field"><label>Shape</label><div class="grp"><button class="eb${cur !== 'square' ? ' on' : ''}" data-shape="round" data-sk="${key}">● Round</button><button class="eb${cur === 'square' ? ' on' : ''}" data-shape="square" data-sk="${key}">■ Square</button></div><span></span></div>`;
  let body;
  if (k === 'top') {
    const T = L.ui.top || {}, order = [...d.getElementById('top').children].map(x => x.id).concat('parentBtn');
    body = field('Size', 'tsize', .7, 1.6, .05, T.size ?? 1) + shapeRow(T.shape, 'top') + `<div class="blist">${order.map(id => `<div class="brow${id === selBtn ? ' sel' : ''}"><span class="em">${TOPS[id][0]}</span><span class="nm">${TOPS[id][1]}</span>
      <input type="color" data-tcol="${id}" value="${(T.colors || {})[id] || hex(W.getComputedStyle(d.getElementById(id)).backgroundColor)}" title="Colour">
      ${id === 'parentBtn' ? '<span style="width:22px"></span>' : `<input type="checkbox" data-thide="${id}" ${(T.hide || []).includes(id) ? '' : 'checked'} title="Show">`}</div>`).join('')}</div>
      <p class="hint">Drag the stars and the microphone in the picture to swap them. Untick to hide. The gear is the parent corner and always stays.</p>`;
  } else if (k === 'nav') {
    const N = L.ui.nav || {}, order = [...d.querySelectorAll('#nav .rb')].map(x => x.dataset.r);
    body = field('Size', 'nsize', .7, 1.6, .05, N.size ?? L.ui.size) + shapeRow(N.shape ?? L.ui.shape, 'nav') + `<div class="blist">${order.map(r => `<div class="brow${r === selBtn ? ' sel' : ''}"><span class="em">${TABS[r][0]}</span><span class="nm">${TABS[r][1]}</span>
      <input type="color" data-ncol="${r}" value="${(N.colors || {})[r] || '#ffffff'}" title="Colour (the tab of the room you are in stays yellow)">
      <input type="checkbox" data-nhide="${r}" ${(N.hide || []).includes(r) ? '' : 'checked'} ${['home', 'play', 'bed', 'library'].includes(r) ? 'disabled title="Room tabs always stay: they are the only way into the rooms"' : 'title="Show"'}></div>`).join('')}</div>
      <p class="hint">Drag the tabs in the picture to change the order. The room tabs always stay (they are the only way into the rooms); Say it and the book can be hidden.</p>`;
  } else {
    const S = L.ui.screens[k] || { left: [], right: [] }, all = Object.keys(L.ui.buttons), on = new Set([...S.left, ...S.right]);
    const row = id => { const [em, nm] = btnLabel(id); return `<div class="brow${id === selBtn ? ' sel' : ''}"><span class="em">${em}</span><span class="nm">${nm}</span><input type="color" data-col="${id}" value="${L.ui.buttons[id].color}" title="Colour"><button class="ib eb" data-rm="${id}" title="Take off this screen">✕</button></div>`; };
    body = field('Size (sides)', 'size', .7, 1.4, .05, L.ui.size) + shapeRow(L.ui.shape, 'rails') +
      `<h2 style="margin-top:14px">Left side</h2><div class="blist">${S.left.map(row).join('') || '<p class="hint">none</p>'}</div>
      <h2>Right side</h2><div class="blist">${S.right.map(row).join('') || '<p class="hint">none</p>'}</div>
      <div class="field"><label>Add a button</label><select class="eb" id="addb"><option value="">Choose…</option>${all.filter(id => !on.has(id)).map(id => `<option value="${id}">${btnLabel(id).join(' ')}</option>`).join('')}</select><span></span></div>`;
  }
  const st = L.ui.style || 'jelly', F = freeMap(), grpName = camKey() === 'phone' ? 'upright phones' : 'sideways phones and iPads';
  const head = `<div class="field"><label>Style (all)</label><div class="grp"><button class="eb${st === 'jelly' ? ' on' : ''}" data-style="jelly">🍬 Jelly</button><button class="eb${st === 'classic' ? ' on' : ''}" data-style="classic">● Classic</button></div><span></span></div>
   <div class="field"><label>Placement</label><span class="hint" style="margin:0">${F ? '<b>free</b>' : 'in rows'} on ${grpName}</span><span></span></div>
   <div class="row">${F ? '<button class="eb" id="freeBack">↩ Back to rows</button>' : '<button class="eb" id="freeOn">✋ Place buttons freely</button>'}</div>
   <p class="hint">${F ? "Drag any button anywhere. It snaps to a grid, the edges and the other buttons (red lines). A red outline means it is over Googoo's face or under the phone's notch or home bar. Buttons can't overlap. Card games and stories keep their rows." : 'Free placement lets you drag every button anywhere (separately for upright phones and for the rest).'}</p>`;
  el.innerHTML = `<h2>Buttons</h2>${head}${opts}${body}<p class="hint">Changing a button size never changes the camera.${st === 'jelly' ? ' Shapes only apply to the classic style.' : ''}</p>`;
  if (el.querySelector('#freeOn')) el.querySelector('#freeOn').onclick = freeStart;
  if (el.querySelector('#freeBack')) el.querySelector('#freeBack').onclick = freeBack;
  el.querySelector('#scr').value = k;
  el.querySelector('#scr').onchange = async e => { const s = e.target.value; selBtn = null; bscr = s; markBtn();
    if (s !== 'top' && s !== 'nav') { if (s === 'night') { await W.setRoom('bed'); W.setLights(false); } else { if (s === 'bed' && !W.eval('lightsOn')) W.setLights(true); await W.setRoom(s); } renderTop(); }
    renderButtons(el); };
  const toggle = (arr, v, on) => on ? arr.filter(x => x !== v) : [...new Set([...arr, v])];
  el.oninput = e => { const t = e.target, ds = t.dataset, v = parseFloat(t.value);
    const live = key => el.querySelectorAll(`[data-k=${key}]`).forEach(i => { if (i !== t) i.value = t.value; });
    if (ds.k === 'size' && !isNaN(v)) { change(() => { L.ui.size = v; }, 'bsize', 'ui'); live('size'); }
    if (ds.k === 'tsize' && !isNaN(v)) { change(() => { ui('top').size = v; }, 'tsize', 'ui'); live('tsize'); }
    if (ds.k === 'nsize' && !isNaN(v)) { change(() => { ui('nav').size = v; }, 'nsize', 'ui'); live('nsize'); }
    if (ds.col) { const id = ds.col; selBtn = id; markBtn(); change(() => { L.ui.buttons[id].color = t.value; }, 'bc' + id, 'ui'); }
    if (ds.tcol) change(() => { const T = ui('top'); (T.colors = T.colors || {})[ds.tcol] = t.value; }, 'tc' + ds.tcol, 'ui');
    if (ds.ncol) change(() => { const N = ui('nav'); (N.colors = N.colors || {})[ds.ncol] = t.value; }, 'nc' + ds.ncol, 'ui'); };
  el.onchange = e => { const ds = e.target.dataset;
    if (ds.thide) change(() => { const T = ui('top'); T.hide = toggle(T.hide || [], ds.thide, e.target.checked); }, '', 'ui');
    if (ds.nhide) change(() => { const N = ui('nav'); N.hide = toggle(N.hide || [], ds.nhide, e.target.checked); }, '', 'ui'); };
  el.onclick = e => { const t = e.target;
    if (t.dataset.style) { change(() => { L.ui.style = t.dataset.style; }, '', 'ui'); renderButtons(el); }
    if (t.dataset.shape) { const sk = t.dataset.sk; change(() => { if (sk === 'rails') L.ui.shape = t.dataset.shape; else ui(sk).shape = t.dataset.shape; }, '', 'ui'); renderButtons(el); }
    if (t.dataset.rm) { change(() => { const s = L.ui.screens[k]; s.left = s.left.filter(x => x !== t.dataset.rm); s.right = s.right.filter(x => x !== t.dataset.rm); }, '', 'ui'); renderButtons(el); } };
  const ab = el.querySelector('#addb'); if (ab) ab.onchange = e => { const id = e.target.value; if (id) { change(() => { (L.ui.screens[k] = L.ui.screens[k] || { left: [], right: [] }).left.push(id); }, '', 'ui'); renderButtons(el); } };
  markBtn();
}

// ---------- painted rooms (🖼️ Painting tab): the picture per orientation, calibration marks dragged on the picture ----------
let roomPics = [], pSel = -1, pDrag = null, pLayer = null;
fetch('rooms').then(r => r.json()).then(l => { roomPics = l; }).catch(() => {});
const bd = (r = room()) => L && L.rooms[r] && L.rooms[r].backdrop || null;
const oKey = () => isPortrait() ? 'portrait' : 'landscape';
const ori = () => { const b = bd(); return b && b[oKey()]; };
const pmap = () => { const m = W.eval('pU.uM.value'); return { ox: m.x, oy: m.y, pw: m.z, ph: m.w }; };
const cl01 = v => Math.max(0, Math.min(1, r2(v)));
function renderPaint() {
  if (!W) return; const d = W.document;
  if (!pLayer) { pLayer = d.createElement('div'); pLayer.id = 'edPaint'; pLayer.style.cssText = 'position:fixed;inset:0;z-index:70;pointer-events:none'; d.body.appendChild(pLayer);
    pLayer.addEventListener('pointerdown', pDown); W.addEventListener('pointermove', pMove); W.addEventListener('pointerup', () => { if (pDrag) { pDrag = null; renderRight(); } }); }
  const P = mode === 'paint' && ori(); pLayer.innerHTML = ''; if (!P || !W.eval('PNT')) return;
  const m = pmap(), X0 = u => m.ox + u * m.pw, Y0 = v => m.oy + v * m.ph, Wd = W.innerWidth, h = [];
  const el = (k, css, txt = '') => h.push(`<div data-k="${k}" style="position:absolute;pointer-events:auto;box-sizing:border-box;${css}">${txt}</div>`);
  const line = (k, v, c, t) => el(k, `left:0;width:${Wd}px;top:${Y0(v) - 6}px;height:12px;cursor:ns-resize;background:linear-gradient(transparent 5px,${c} 5px,${c} 7px,transparent 7px)`, `<span style="position:absolute;right:6px;top:-16px;font:700 11px system-ui;color:${c};background:#fffd;padding:0 4px;border-radius:4px">${t}</span>`);
  const box = (k, a, c, sel) => { el(k, `left:${X0(a[0])}px;top:${Y0(a[1])}px;width:${X0(a[2]) - X0(a[0])}px;height:${Y0(a[3]) - Y0(a[1])}px;border:${sel ? 3 : 2}px solid ${c};cursor:move;background:${sel ? c + '40' : 'transparent'}`);
    for (const [cn, u, v] of [['br', a[2], a[3]], ['tl', a[0], a[1]]]) el(k + ':' + cn, `left:${X0(u) - 7}px;top:${Y0(v) - 7}px;width:14px;height:14px;background:${c};border-radius:3px;cursor:nwse-resize`); };
  const dot = (k, u, v, c, t) => el(k, `left:${X0(u) - 9}px;top:${Y0(v) - 9}px;width:18px;height:18px;border-radius:50%;background:${c};border:2px solid #fff;cursor:move;box-shadow:0 1px 4px #0006`, `<span style="position:absolute;left:20px;top:-2px;font:700 11px system-ui;white-space:nowrap;color:#fff;text-shadow:0 1px 2px #000">${t}</span>`);
  line('horizon', P.horizon, '#e11d9b', 'eye level'); if (P.wall != null) line('wall', P.wall, '#0ea5e9', 'wall meets floor');
  if (P.rug) { const [u, v, a, b] = P.rug; box('rug', [u - a, v - b, u + a, v + b], '#ef4444'); }
  (P.cells || []).forEach((c, i) => box('cell' + i, c, '#22c55e', i === pSel));
  (P.taps || []).forEach((t, i) => box('tap' + i, t.r, '#a855f7')); // tap zones: a painted thing says its word (w) or does the bed / lamp action (f)
  for (const [id, pl] of Object.entries(P.place || {})) dot('place:' + id, pl[0], pl[1], '#22c55e', id);
  const g = P.goo; dot('goo', g[0], g[1], '#facc15', 'Googoo'); dot('gooh', g[0], g[1] - g[2], '#facc15', 'height');
  el('focus', `left:${X0(P.focus[0]) - 13}px;top:${Y0(P.focus[1]) - 13}px;width:26px;height:26px;cursor:move;font:900 26px/26px system-ui;color:#fff;text-align:center;text-shadow:0 0 3px #000`, '✛');
  pLayer.innerHTML = h.join('');
}
function pDown(e) {
  const t = e.target.closest('[data-k]'); if (!t) return; e.stopPropagation(); e.preventDefault();
  const k = t.dataset.k, k0 = k.split(':')[0]; if (/^cell\d+$/.test(k0)) pSel = +k0.slice(4);
  pDrag = { k, x: e.clientX, y: e.clientY, m: pmap(), P0: clone(ori()), key: 'p' + Date.now() }; renderPaint();
}
function pMove(e) {
  if (!pDrag) return; const { k, m, P0 } = pDrag, du = (e.clientX - pDrag.x) / m.pw, dv = (e.clientY - pDrag.y) / m.ph, u = (e.clientX - m.ox) / m.pw, v = (e.clientY - m.oy) / m.ph;
  change(() => { const P = ori(), [k0, part] = k.split(':');
    if (k === 'horizon') P.horizon = Math.max(-1, Math.min(2, r2(P0.horizon + dv)));
    else if (k === 'wall') P.wall = cl01(P0.wall + dv);
    else if (k === 'focus') P.focus = [cl01(P0.focus[0] + du), cl01(P0.focus[1] + dv)];
    else if (k === 'goo') P.goo = [cl01(u), cl01(v), P0.goo[2]];
    else if (k === 'gooh') P.goo = [P0.goo[0], P0.goo[1], Math.max(.05, Math.min(.9, r2(P0.goo[2] - dv)))];
    else if (k0 === 'place') P.place[part] = [cl01(u), cl01(v)];
    else { const tp = /^tap\d+$/.test(k0), a = k0 === 'rug' ? [P0.rug[0] - P0.rug[2], P0.rug[1] - P0.rug[3], P0.rug[0] + P0.rug[2], P0.rug[1] + P0.rug[3]] : tp ? P0.taps[+k0.slice(3)].r.slice() : P0.cells[+k0.slice(4)].slice(), b = a.slice();
      if (!part) { b[0] += du; b[2] += du; b[1] += dv; b[3] += dv; } else if (part === 'br') { b[2] = Math.max(a[0] + .02, a[2] + du); b[3] = Math.max(a[1] + .02, a[3] + dv); } else { b[0] = Math.min(a[2] - .02, a[0] + du); b[1] = Math.min(a[3] - .02, a[1] + dv); }
      const n = b.map(cl01); if (k0 === 'rug') P.rug = [r2((n[0] + n[2]) / 2), r2((n[1] + n[3]) / 2), r2((n[2] - n[0]) / 2), r2((n[3] - n[1]) / 2)]; else if (tp) P.taps[+k0.slice(3)].r = n; else P.cells[+k0.slice(4)] = n; }
  }, pDrag.key, 'paint');
}
// right panel: painted on/off, the picture for this kind of screen, a few numbers, compartments
function renderPaintPanel(el) {
  const r = room(), B = bd(), P = ori(), def = W.eval('PAINT0')[r], kname = isPortrait() ? 'upright phones' : 'sideways phones and iPads', base = f => f.replace(/^assets\/rooms\//, '');
  const pics = [...new Set([...roomPics, ...(P ? [base(P.img)] : [])])];
  let html = `<h2>${ROOM_NAME[r]}: painting</h2><label class="check"><input type="checkbox" id="pOn" ${B ? 'checked' : ''}><span>Painted room<br><small class="hint">Off = the normal 3D room with its walls and furniture.</small></span></label>`;
  if (B) {
    html += `<div class="field"><label>Picture for ${kname}</label><select class="eb" id="pImg">${P ? '' : '<option value="">Choose…</option>'}${pics.map(f => `<option value="${f}">${f}</option>`).join('')}</select><span></span></div>
      <p class="hint">Pictures are the files in assets/rooms (WebP, at most 1440 px on the long side).</p>`;
    if (P) html += field('Googoo height (% of the picture)', 'gh', 5, 80, 1, Math.round(P.goo[2] * 100)) + field('Field of view (°)', 'fov', 20, 90, 1, P.fov || 50) + field('Shadow strength', 'sh', 0, 1, .05, (P.light || {}).shadow ?? .35) + field('Sunbeam', 'beam', 0, .3, .01, (P.beam || [])[5] ?? 0) +
      (r === 'library' ? `<div class="row"><button class="eb" id="pAdd">➕ Add a compartment</button><button class="eb warn" id="pDel" ${pSel >= 0 && (P.cells || [])[pSel] ? '' : 'disabled'}>🗑 Remove the selected one</button></div><p class="hint">${(P.cells || []).length} compartments = ${(P.cells || []).length} books per page. Only mark empty ones (no painted books in them). Click a green box to select it.</p>` : '') +
      `<p class="hint">3D pieces that stay in this room: ${(B.keep || []).join(', ') || 'none (only Googoo)'}.</p>` + (def && def[oKey()] ? `<div class="row"><button class="eb" id="pDef">↩ Back to the built-in marks</button></div>` : '');
    else html += '<p class="hint">No picture for this kind of screen yet: the other one is used (cut to fit). Pick one above to give it its own.</p>';
  }
  el.innerHTML = html; const q = s => el.querySelector(s);
  q('#pOn').onchange = e => { change(() => { L.rooms[r].backdrop = e.target.checked ? clone(def || { keep: [] }) : null; }, '', 'paint'); renderRight(); };
  if (q('#pImg')) { q('#pImg').value = P ? base(P.img) : ''; q('#pImg').onchange = e => { const f = e.target.value; if (!f) return; const im = new Image();
    im.onload = () => { change(() => { const k = oKey(), o = B[k] || clone((def || {})[k] || { focus: [.5, .6], fov: 50, horizon: .5, wall: .65, goo: [.5, .85, .25], rug: [.5, .85, .3, .07] });
      o.img = 'assets/rooms/' + f; o.size = [im.naturalWidth, im.naturalHeight]; B[k] = o; }, '', 'paint'); renderRight(); status(`Picture ${f}: now drag the marks so the floor and the shelf match.`); }; im.src = 'assets/rooms/' + f; }; }
  el.oninput = e => { const k = e.target.dataset.k, v = parseFloat(e.target.value); if (!k || isNaN(v) || !P) return;
    change(() => { if (k === 'gh') P.goo = [P.goo[0], P.goo[1], r2(v / 100)]; if (k === 'fov') P.fov = v; if (k === 'sh') P.light = { ...(P.light || {}), shadow: v }; if (k === 'beam') { P.beam = (P.beam || [.1, .2, 45, .05, .8, 0]).slice(); P.beam[5] = v; } }, 'pf' + k, 'paint');
    el.querySelectorAll(`[data-k="${k}"]`).forEach(i => { if (i !== e.target) i.value = e.target.value; }); };
  if (q('#pAdd')) q('#pAdd').onclick = () => { change(() => { (P.cells = P.cells || []).push([.45, .45, .55, .52]); }, '', 'paint'); pSel = P.cells.length - 1; renderRight(); };
  if (q('#pDel')) q('#pDel').onclick = () => { change(() => { P.cells.splice(pSel, 1); }, '', 'paint'); pSel = -1; renderRight(); };
  if (q('#pDef')) q('#pDef').onclick = () => { change(() => { B[oKey()] = clone(def[oKey()]); }, '', 'paint'); renderRight(); };
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

window.ED = { get L() { return L; }, get sel() { return sel; }, select, setMode, setDevice, setFree, goRoom, doSave, doUndo, doRedo, addProp, removeProp, toggleHidden, duplicate, get saved() { return saved; } }; // for tests
})();

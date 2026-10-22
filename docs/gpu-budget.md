# Googoo Robo: GPU budget (2026-10-21)

Phones and iPads first. Target devices: **iPhone 11 (A13)**, a **4-year-old mid Android** (Snapdragon 7xx / Mali-G7x class, 4 GB), **iPad 9 (A13)**. Everything below applies to both engines (web three.js r128 and Unity); engine notes follow. Checked automatically by three tools (end of this page).

## 1. Per area (one room or outdoor screen on screen at once)

| Budget | Target | Hard limit | Notes |
|---|---|---|---|
| Draw calls per frame | ≤ 80 | **100** | Counts the shadow pass too (every shadow caster = +1 call). |
| Triangles per frame | ≤ 150k | **200k** | Incl. Googoo 34k (x2 while he casts a shadow) and the shadow pass. |
| Texture GPU memory (everything resident) | ≤ 64 MB | **96 MB** | iOS Safari kills the tab well below device RAM; the web game keeps every room loaded. |
| Shadow maps | 1 directional, 1024² | 2048² only on desktop | No point/spot light shadows (6 or 1 extra passes each). |
| Lights | 1 directional + hemi/ambient | +1-2 point lights, no shadows | |
| Canvas pixels (DPR cap) | phone 1.5, tablet 1.5 | 2 | iPad 9 at DPR 2 = 3.5 MP per frame; 1.5 = 2 MP. LOW devices 1.0-1.25. |
| Frame rate | 60 while interacting, **30 when idle** (no touch, no game, Googoo idling for >4 s) | | Pause rendering + audio when the page/app is hidden (web already does). Cap 120 Hz iPads at 60. |

## 2. Per prop (Tripo GLB, real size)

| Class | Use | Triangles | Max texture side | Texture GPU memory | Draws |
|---|---|---|---|---|---|
| **S** small | toys, food, pillow, frame | 1-3k | 512 | ≤ 1.5 MB | 1 |
| **M** medium | chair, lamp, animal, door | 3-8k | 1024 | ≤ 4.5 MB | 1 |
| **L** large | bed, sofa, wardrobe, room-size pieces | 8-15k | 1024 | ≤ 4.5 MB | 1 |
| **H** hero | Googoo | ≤ 40k (now 34k) | 2048 | ≤ 24 MB | ≤ 2 (body + face) |

Class comes from the `S small / M medium / L large` column in `docs/tripo-props.md` (else from the model's longest side: < 0.5 m S, < 1.2 m M, else L).

Texture memory is what the GPU holds, not the file size: a 1024² JPEG/PNG/WebP decodes to RGBA8 = **4 MB, 5.3 MB with mipmaps**. A Tripo prop has 3 maps (base colour, normal, roughness/metal), so a 1024 prop = **16 MB** as loaded. The same maps in KTX2 (transcoded to ASTC/ETC2/BC on the GPU) ≈ 1 byte/px = 4 MB. That is why the per-prop memory budget is met by **either** KTX2 at full size **or** WebP/JPEG at half size (512 for M/L, 256 for S).

## 3. Rules

- **Shadows:** only Googoo and big furniture (bed, sofa, wardrobe, bookshelf, TV cabinet, korsi, fridge) cast. Small props, rugs, carpets, wall pieces, frames and everything flat **receive only**, or get a soft blob/baked AO under them. Room shells receive only.
- **Materials:** one material and one mesh per prop (Tripo already exports this). Small props that always appear together (toy shelf, kitchen counter food) share one atlas texture and one material.
- **Repeats:** the same prop shown 3+ times (books, blocks, fence posts, trees, food) = instancing (three `InstancedMesh`, Unity GPU instancing / SRP Batcher), never copies.
- **Static merging:** furniture that never moves in a room is merged per room per material (three `BufferGeometryUtils.mergeBufferGeometries`, Unity static batching). Tappable/animated pieces stay separate.
- **No mesh decimation in the pipeline:** props must never change shape. If a prop is over its triangle budget, re-export it from Tripo at a lower face count (or fix it by hand in Blender); the optimizer only does lossless steps plus texture resize/compression.
- **LOD:** not needed for indoor props (≤ 15k, small on a phone screen). Use LOD groups only for L pieces seen far away outdoors (street, park, farm).

## 4. Web (three.js r128, no bundler)

- **Count:** `renderer.info.render.calls / triangles`, `renderer.info.memory.textures / geometries`. In r128 `info` is reset *after* the shadow pass, so the per-frame numbers miss shadows; set `renderer.info.autoReset=false`, `reset()`, render one frame, read, then set it back (tools/gpu_runtime_check.py does this).
- **WebP textures work today** with the plain `GLTFLoader` (r128 supports `EXT_texture_webp`; iOS 14+). This is what the optimizer outputs now.
- **KTX2:** r128 has `KTX2Loader` only as an ES module (`examples/jsm`), not in `examples/js`. It works next to the global `THREE` with an import map and a 1-line shim (verified headless in r128 by tools/optimize_props.py):
  ```html
  <script type="importmap">{"imports":{"three":"./three-global.js"}}</script>
  <script type="module">
  import {KTX2Loader} from 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/loaders/KTX2Loader.js';
  const ktx2=new KTX2Loader().setTranscoderPath('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/libs/basis/').detectSupport(renderer);
  gltfLoader.setKTX2Loader(ktx2);   // and, only if props are meshopt-compressed:
  gltfLoader.setMeshoptDecoder(MeshoptDecoder); // <script src=".../three@0.128.0/examples/js/libs/meshopt_decoder.js">
  </script>
  ```
  `three-global.js`: `const T=window.THREE;export const {CompressedTexture,CompressedTextureLoader,FileLoader,LinearEncoding,sRGBEncoding,LinearFilter,LinearMipmapLinearFilter,Loader,RGBAFormat,RGBA_ASTC_4x4_Format,RGBA_BPTC_Format,RGBA_ETC2_EAC_Format,RGBA_PVRTC_4BPPV1_Format,RGBA_S3TC_DXT5_Format,RGB_ETC1_Format,RGB_ETC2_Format,RGB_PVRTC_4BPPV1_Format,RGB_S3TC_DXT1_Format,UnsignedByteType}=T;` (import maps need iOS 16.4+). Not wired into the game yet.
- **Repeats / merging:** `new THREE.InstancedMesh(geo, mat, n)`; static furniture: `THREE.BufferGeometryUtils.mergeBufferGeometries(geos)` (`examples/js/utils/BufferGeometryUtils.js`, r128).
- **Shadows:** `castShadow` only on the list in section 3; `receiveShadow` on floors/rugs. Today `loadProps()` sets both on every prop and the procedural rooms cast from **91 of 135 visible meshes**.
- **Frame-rate policy** (not in the game yet): in `loop()`, skip a frame when idle, e.g. `const idle=st.mode==='idle'&&!game.type&&performance.now()-st.lastPoke>4000; if(t-lastT<(idle?30:15))return; lastT=t;` (the 15 ms floor caps 120 Hz iPads at 60). The `say` and `book` screens can use the idle rate too.
- **DPR:** `Math.min(devicePixelRatio, 1.5)` on phones (already) and on tablets (today 2); shadow map 1024 on tablets too (today 2048 = 16 MB).

## 5. Unity (URP 17, 6000.6.7f1)

Applied by `Assets/Editor/GoogooPerf.cs` (menu **Googoo > Apply Mobile Perf Settings**, or `-executeMethod GoogooPerf.Apply`; re-run after `Setup.MakeScene`, which recreates the materials):

- SRP Batcher on (both URP assets; it already was).
- **Mobile_RPAsset** (the quality level WebGL, Android and iPhone use): additional-light shadows **off** (the lamp's soft point-light shadow cost 6 extra shadow passes), additional lights per object 4 → 2, additional shadow atlas 2048 → 512, soft shadow quality Low, light cookies / light layers / terrain holes / reflection-probe blending and box projection off (unused; fewer shader variants). Render scale 0.8, 1 shadow cascade, 8 m shadow distance, HDR (bloom needs it) and MSAA off + FXAA were already right. PC asset untouched.
- Static batching **on** for WebGL, Android, iPhone (Standalone left as it was). Mark room shells and fixed furniture *Batching Static*.
- GPU instancing on all shared materials in `Assets/Materials` (SRP Batcher still wins for URP Lit; instancing helps where it can't).
- Texture import rules (`GoogooTextureRules`, runs on every import, never touches a platform that is already overridden, e.g. by Setup.cs): Android/iPhone **ASTC 6x6** colour, **ASTC 4x4** normal maps, UI and the face atlas; max 2048 for Googoo/face, 1024 for everything else; WebGL max size per budget, format left to the build's texture subtarget. (Android/iOS modules are not installed yet; the settings are stored for when they are. ETC2 is Unity's automatic fallback for non-ASTC Android.)
- Checked: compiles, and a WebGL test build (`GOOGOO_DEV_OUT=<temp> -executeMethod Setup.BuildWebGL`) succeeded (data 6.69 → 6.65 MB) and renders correctly on the GPU at 60 fps. `Pash-dev/proto-unity` was not rebuilt.

Still to do in Unity (needs scene/game code, not settings):
- **glTFast keeps GLB textures uncompressed** (RGBA32, 16 MB per Tripo prop). Either add `com.unity.cloud.ktx` and import the KTX2 props (same files as the web), or extract the textures to normal TextureImporters as Setup.cs already does for Googoo.
- WebGL for phones: build with texture subtarget **ASTC** (desktop browsers then decompress on the CPU; ship a DXT build for desktop if needed).
- Rooms: bake lightmaps for the static room + furniture (Mixed lighting, Subtractive is the cheapest on mobile), light probes for Googoo; realtime shadow only from Googoo and big furniture.
- Frame rate: keep `Application.targetFrameRate = 60` (Room.cs) and use `OnDemandRendering.renderFrameInterval = 2` (30 fps) when idle; input stays at 60.

## 6. Tools (Pash-dev/tools, stdlib + numpy/PIL/Playwright)

| Command | What it does |
|---|---|
| `python tools/gpu_check.py "C:/Users/ahmma/Downloads/Pash 3D/props" assets/googoo/googoo.glb` | Offline: per GLB tris, verts, materials, draws, textures (size/format), texture MB as loaded and as KTX2, file size; flags budget breaks by class. Folders are not recursed (skips raw/, old/, optimized/). Exit 1 on a hard break. `--selftest` checks itself. |
| `python tools/optimize_props.py [src] [--out DIR] [--webp\|--ktx2] [--meshopt] [--verify] [--only NAME ...]` | glTF-Transform 4 (`npx @gltf-transform/cli@4`): dedup, prune, lossless weld, flatten/join, **no simplify**, all vertex attributes kept, textures resized to the class max, then KTX2 (UASTC normal/ORM + ETC1S colour, needs `toktx`) or WebP at half size. Writes to `<src>/optimized/`, never over the sources. `--verify` renders before/after from 3 angles in three.js r128 (GLTFLoader + KTX2Loader + MeshoptDecoder, real GPU) into `optimized/_verify/*.png` and flags any silhouette change > 1% or colour change > 4%. |
| `python tools/gpu_runtime_check.py [--port 8770] [--props DIR]` | Serves Pash-dev, opens the game as iPhone 11 and iPad 9 on the real GPU (tools/browser.py; `GOOGOO_SWIFTSHADER=1` = software), visits every screen, prints calls / tris (full frame incl. shadows) / textures / texture MB / fps vs budget. Texture MB = the textures really live on the GPU (the WebGL texture calls are wrapped and live textures' bytes summed, mipmaps, shadow map and PMREM included); before 2026-10-22 it estimated every texture still referenced in the scene, incl. rooms already left (disposed on the GPU), which read ~2x too high. Measured 2026-10-22 after home→play→bed→library→home→library, phone: 54 / 52 / 43 / 42 / 55 / 42 MB (all ≤ 64). Biggest: Googoo body 1024 (5.3), wood floor canvas 1024 (5.3), rug canvas 1024 (5.3), shadow map 1024 (4.0), face screen 1024x731 (3.8), PMREM 2.3; each Tripo prop 3 x 512 maps = 4 MB. `--props DIR` swaps `models/*.glb` for DIR's files without touching the repo. |

## 7. Results (2026-10-21)

### Props checker: 28 sized GLBs in `Downloads\Pash 3D\props\` + Googoo

- **Triangles: all 28 within budget** (largest: room_living_shell 9.9k L, bedroom_bed 9.6k L, living_sofa 9.3k L, toy_kite 7.9k M = 99% of M, farm_cow 7.7k M). 1 material, 1 draw each. No NPOT textures.
- **All 28 are over on texture memory, and only on that:** 3 JPEG maps each (base colour, normal, roughness/metal); 1024 maps = 16 MB per M/L prop as loaded (budget 4.5), 512 maps = 4 MB per S prop (budget 1.5). The 28 together = **340 MB** of GPU textures (10.9 MB of files). A furnished living room of ~11 of these would be ~185 MB and very likely crash iOS Safari.
- Googoo (`assets/googoo/googoo.glb`): 34.1k tris, 2 materials, one 1024 JPEG = 5.3 MB: ok. `googoo_anims_web.glb` is animation only.

### Optimizer (WebP mode: `toktx` is not installed, so no KTX2 yet; Node 25 + gltf-transform 4.5.1 work)

Visual check: all 28 **same** (shape difference 0.00% from 3 angles, colour difference 0.2-0.8%, triangle counts unchanged). Sheets in `Downloads\Pash 3D\props\optimized\_verify\`. A deliberately decimated teddy (480 tris) was flagged (6.3% shape), so the check works. Total **340 → 85 MB texture memory, 10.9 → 4.4 MB files**, 0 over budget.

| file | class | tris | file KB | tex MB as loaded |
|---|---|---|---|---|
| bedroom_bed | L | 9,632 | 630 → 310 | 16.0 → 4.0 |
| bedroom_blanket | S | 2,222 | 178 → 88 | 4.0 → 1.0 |
| bedroom_lamp | S | 2,890 | 184 → 90 | 4.0 → 1.0 |
| bedroom_nightstand | M | 2,905 | 329 → 99 | 16.0 → 4.0 |
| bedroom_pillow | S | 1,458 | 151 → 56 | 4.0 → 1.0 |
| bedroom_rug | S | 948 | 115 → 42 | 4.0 → 1.0 |
| bedroom_wardrobe | L | 6,358 | 492 → 212 | 16.0 → 4.0 |
| farm_cow | M | 7,698 | 578 → 237 | 16.0 → 4.0 |
| living_armchair | M | 5,872 | 365 → 167 | 16.0 → 4.0 |
| living_bookshelf | M | 6,794 | 573 → 263 | 16.0 → 4.0 |
| living_carpet_persian | M | 2,748 | 575 → 142 | 16.0 → 4.0 |
| living_coffee_table | M | 2,864 | 346 → 108 | 16.0 → 4.0 |
| living_door | M | 3,510 | 362 → 127 | 16.0 → 4.0 |
| living_floor_lamp | M | 3,664 | 391 → 133 | 16.0 → 4.0 |
| living_korsi | M | 5,606 | 495 → 187 | 16.0 → 4.0 |
| living_picture_frame | S | 1,312 | 178 → 62 | 4.0 → 1.0 |
| living_sofa | L | 9,300 | 636 → 291 | 16.0 → 4.0 |
| living_tv_cabinet | L | 7,020 | 492 → 226 | 16.0 → 4.0 |
| living_window_curtains | M | 5,097 | 496 → 196 | 16.0 → 4.0 |
| room_living_shell | L | 9,854 | 642 → 346 | 16.0 → 4.0 |
| toy_ball | S | 1,482 | 129 → 52 | 4.0 → 1.0 |
| toy_blocks | S | 2,720 | 199 → 101 | 4.0 → 1.0 |
| toy_box | M | 3,392 | 514 → 152 | 16.0 → 4.0 |
| toy_doll | S | 2,854 | 222 → 96 | 4.0 → 1.0 |
| toy_drum | S | 2,412 | 178 → 84 | 4.0 → 1.0 |
| toy_kite | M | 7,930 | 670 → 265 | 16.0 → 4.0 |
| toy_piano | M | 4,430 | 430 → 158 | 16.0 → 4.0 |
| toy_teddy_bear | M | 4,836 | 368 → 142 | 16.0 → 4.0 |

`--meshopt` (tested on sofa, cow, ball) shrinks files a further ~60% (sofa 291 → 109 KB) with the same look, but needs `MeshoptDecoder` in the page and quantizes positions (don't call `computeBoundingBox` on them yourself). KTX2 would give the **full** 1024/512 resolution at the same ~85 MB: install KTX-Software (`toktx`, github.com/KhronosGroup/KTX-Software/releases) and run with `--ktx2`, once the loader in section 4 is wired.

### Runtime, current dev build (index.html, 4 Tripo props in models/), RTX 3060 Ti headless (fps = desktop best case, vsync-capped)

| screen | draw calls (≤ 100) | triangles (≤ 200k) | textures / geometries / programs | tex MB, phone / iPad | tex MB with optimized props, phone / iPad | fps |
|---|---|---|---|---|---|---|
| home | 67 | 77.6k | 12 / 87 / 11 | 80.9 / 92.9 | 41.9 / 53.9 | 60 |
| play | **91** | 103.0k | 18 / 123 / 12 | 80.9 / 92.9 | 41.9 / 53.9 | 60 |
| bed | 61 | 92.9k | 24 / 138 / 13 | 80.9 / 92.9 | 41.9 / 53.9 | 60 |
| bed, lights off | 61 | 92.9k | 25 / 138 / 20 | 78.6 / 90.6 | 39.6 / 51.6 | 60 |
| say (3D bedroom behind cards) | 61 | 92.9k | 25 / 138 / 26 | 80.9 / 92.9 | 41.9 / 53.9 | 60 |
| book | 61 | 92.9k | 25 / 138 / 26 | 80.9 / 92.9 | 41.9 / 53.9 | 60 |

Phone canvas 621x1344 (DPR 1.5), iPad 1620x2160 (DPR 2). Calls and tris include the shadow pass (40-50% of both). Texture memory already at 81-93 MB with only 4 Tripo props: those 4 (bed, lamp, teddy, cow) are 52 MB; Googoo 9 MB (body + face); iPad's 2048 shadow map 16 MB. Swapping in the optimized props halves it. The play room is already at 91 of 100 draw calls before any more props: its procedural toys all cast shadows.

## 8. For the props session

1. Keep exporting from Tripo at the class size (S 512, M/L 1024) and 1 material: tris are all fine.
2. After `resize_props.py`, run `python tools/optimize_props.py --verify` and place the files from `props\optimized\` (not the raw-size JPEG ones) in `models/` / Unity. Re-check with `python tools/gpu_check.py <folder>`; it must exit 0.
3. When placing in `loadProps()`/`addF()`: `castShadow` only for big furniture (bed, sofa, wardrobe, bookshelf, TV cabinet, korsi); everything else `receiveShadow` only. Each new prop that **replaces** a procedural group frees its draw calls; a prop that is **added** costs 1 call (+1 if it casts). Keep each room ≤ 100 calls with `tools/gpu_runtime_check.py`.
4. Repeated small things (books, blocks, fruit) = one prop instanced, not several props.
5. `toy_kite` is at 99% of the M tri budget: if it is redone, aim for ≤ 6k.
6. Room shells are built in-engine, so `room_living_shell.glb` should not be placed.

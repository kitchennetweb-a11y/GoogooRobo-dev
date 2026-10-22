# Googoo Robo: Tripo prop plan (2026-10-21)

Replaces the rough list in `docs/tripo-objects.md`. Goal: every 3D prop and world piece for the house, the courtyard, the street, the shops, the park, the farm, the school, the beach and the moon, built with Tripo (free text-to-image first, then image-to-3D) as engine-neutral GLB files (Unity is the leaning engine, not final). Nothing here changes code.

> **Style locked (owner, 2026-10-21):** the plain style prompt above is the base for everything. **Light sci-fi touch** only on hero house pieces (sofa, samovar, lamps, TV, fridge, bed, and similar "Googoo's home" tech); food, animals and most other props stay plain. Sci-fi line, inserted before "Object:": *"Playful friendly sci-fi twist, as if it belongs in a cheerful robot's home of the future: smooth rounded retro-futuristic shell, thin soft glowing cyan light strips, small rounded robot-style details, gently floating parts held by soft light."* Chosen images (docs/style-tests/): apple = right of anchor-apple.png; sofa = left of scifi-sofa.png (hovering, curved cyan side glow); samovar = right of scifi-samovar.png (round, floating teapot). Floating parts (teapot, sofa pads) must be made with Generate in Parts so they can bob in the engine.

> **Real size and room shells (2026-10-21):** Tripo normalises every model to ~1 unit, so run `python tools/resize_props.py` after each export (drop Tripo files in `props/raw/`; it reads the size column below and writes real-size copies to `props/`). **Room shells, floors, ground and sky are NOT made in Tripo any more:** both the web app (three.js, already code-built rooms) and Unity build them as simple pieces in our colours; Tripo makes furniture, toys, food, animals and vehicles only. The same GLBs go into both the web app and Unity. Skip the `*_shell`, ground and sky rows when making batches.

> **Pilot done (2026-10-21):** 5 GLBs in `Downloads\Pash 3D\props\` (bedroom_lamp 2.9k tris/512, toy_teddy_bear 4.8k/1k, bedroom_bed 9.6k/1k, farm_cow 7.7k/1k, room_living_shell 9.9k/1k; 0.2-0.7 MB each). Previews: docs/style-tests/3d-*.png. Findings: **45 credits per model** at H3.1 + Ultra + AI Complete + 2K texture + PBR + Remove Lighting + Triangle (120 props = about 5,400 credits); **Generate in Parts cannot be combined with Texture** (turning one on turns the other off), so floating parts come out as separate pieces in one mesh, to split in Blender/Unity if they must move; export lets you pick GLB and 512/1k texture. Room shell: the painted window view came out garbled, so make windows plain openings and put a sky behind them in the engine.

> **Pilot picks (owner, 2026-10-21, docs/style-tests/pilot-*.png):** lamp = left (floating shade, Generate in Parts), teddy = left (sitting), bed = right (floating side pods, glowing floor: watch the 3D for loose pieces), cow = right, living room shell = right (painted window view).

> **Tested 2026-10-21 in Tripo (Nano Banana, 1:1, 2 images, free):** the first version of the style prompt said "with cream and royal-blue accents where they fit" and painted blue stripes on the apple; it was removed. The 3 anchors (apple, sofa, samovar) then came out clean.

## 0. Rules for every model

- Look: soft, rounded "premium toy" 3D, like a modern kids' animated film or toy line. Chunky simple shapes, soft bevelled edges, no grime or wear, matte or satin painted materials. Googoo's palette: warm cream shell, satin royal blue accents, dark grey matte metal joints, glossy black face screen, soft cyan glow. Props keep their own natural colours in the same soft pastel toy look. No text, letters or logos on anything.
- Units: metres, Y up. Googoo is about 1.0 m tall; props are "toddler-real" relative to him (bed 1.6-2 m long, chair seat about 0.45 m). Pivot at bottom centre on y=0, front facing +Z. One prop per file, snake_case names. Props have no rig; animals flagged "rig later" may get a Tripo auto-rig later.
- Budgets: **S small** (cup, fruit, toys) 1-3k tris, 512 px texture. **M medium** (chair, lamp, bike, animals) 3-8k tris, 1024 px. **L large** (bed, counter, tree, car, room shells) 8-15k tris, 1024 px. **H hero** (rocket only) up to 15k tris, 2048 px. Target about 150-250k visible tris per area including Googoo (35k).
- Tripo settings for every model: image to 3D, model H3.1, Texture on, PBR on, Remove Lighting on, Triangle topology, Private, polycount slider set to the budget in the list (the tris column x 1000), export GLB.
- Interactive parts (lamp shade and switch, doors, drawers, TV screen, fridge door, rocket hatch, curtains, lids) need Tripo "Generate in Parts" (column Parts = Y).
- World pieces (room shells, ground, sky): Tripo makes one chunk, not a tileable kit. Build rooms as open cut-away shells (front wall and ceiling removed), ground pieces as one terrain slab, and keep their texture flat and simple. Sky domes may be better as a skybox or gradient in the engine; try Tripo once, drop it if the result is noisy.

## 1. Shared style prompt

Used as the start of every image prompt. Then add the object text from the lists below (the prompt column), ending with a full stop.

> Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object:

Negative prompt (paste only if Tripo's text-to-image shows a negative field):

> text, letters, numbers, logos, watermark, people, hands, multiple objects, background scene, floor, table, cast shadow, harsh lighting, realistic grime, dirt, rust, scratches, thin spindly parts, transparent glass, mirror reflections, chrome, blurry, cropped, dark background

If the first image is not on a plain grey background or shows more than one object, add "plain light grey seamless background, nothing else in the frame" and regenerate; do not go on to 3D with a messy image.

## 2. Style test: 3 style anchors (make these first)

Different sizes and materials. When you approve their images, save them as `C:\Users\ahmma\Downloads\Pash 3D\props\_style\anchor_<name>.png`. For every later prop, if Tripo allows an image reference, attach the matching anchor (organic for fruit and animals, fabric for furniture and soft toys, metal for appliances and vehicles). If it does not, paste the shared style prompt only. Do all three before anything else; redo until they look like Googoo's world.

| # | File | Why it anchors | Size class | Prompt |
|---|---|---|---|---|
| A1 | `food_apple.glb` | organic, glossy-satin small piece (fruit, food, animals) | S small, 1.5k tris, 512 px | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: a single plump toy-like red apple with a little brown stem and one soft green leaf, smooth satin finish. |
| A2 | `living_sofa.glb` | large soft fabric and rounded wood (furniture, soft toys) | L large, 10k tris, 1024 px | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: a chunky rounded two-seat sofa in soft dusty-blue fabric with plump cream cushions, thick rounded arms, short round wooden feet. |
| A3 | `kitchen_samovar.glb` | satin painted metal, medium (appliances, vehicles, lamps) | M medium, 5k tris, 1024 px | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: a Persian samovar tea urn with a rounded body in soft satin pastel gold-cream, a small chunky tap, two curved handles, a rounded lid with a little teapot on top, gentle cheerful toy look. |

## 3. Pilot: 5 props to run the whole pipeline first

Run these after the anchors, start to finish (prompt, image, 3D, check, GLB, drop into the engine next to Googoo) to find problems with scale, pivot, textures and parts before the other batches. They cover every size and the hard cases.

| # | File | What it tests | Size class | Parts | Prompt |
|---|---|---|---|---|---|
| P1 | `bedroom_lamp.glb` | small, interactive (Generate in Parts: shade and switch) | S small, 3k tris, 512 px | Y (shade, switch) | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: a small bedside table lamp with a round cream ceramic base and a rounded pastel-blue lampshade glowing softly, one small chunky switch on the base. |
| P2 | `toy_teddy_bear.glb` | medium soft toy (plush texture) | M medium, 5k tris, 1024 px | N | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: a soft round teddy bear sitting, warm honey-brown plush with a cream muzzle and belly, round ears, little pastel-blue bow tie, simple dot eyes, friendly smile. |
| P3 | `bedroom_bed.glb` | large furniture with several materials | L large, 10k tris, 1024 px | N | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: a cosy child's bed with a chunky rounded cream wooden frame and a soft headboard with satin-blue trim, a thick pastel-blue mattress, a plump pillow and a folded blanket on top. |
| P4 | `farm_cow.glb` | medium animal, tests the rig-later step (try Tripo auto-rig once) | M medium, 8k tris, 1024 px | N | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: a chubby friendly cow standing, white with soft black patches, pink nose, rounded horns and a small bell, simple dot eyes. |
| P5 | `room_living_shell.glb` | world piece: the room shell that replaces the web room | L large, 12k tris, 1024 px | N | Soft, rounded premium-toy 3D render in the style of a modern kids' animated film or toy line: one single object, the whole object in frame, centred, seen from a three-quarter front view slightly from above, on a plain light grey seamless background, soft even studio lighting with no hard cast shadows. Chunky simple shapes, soft bevelled edges, clean smooth surfaces with no grime, wear, scratches or fine clutter, matte or satin painted materials in gentle pastel versions of the object's own natural colours, no added patterns or stripes. Friendly and toddler-safe, no text, letters, numbers or logos, no other objects, no people, no hands. Object: an empty cut-away dollhouse view of a cosy living room shell: warm light-wood floor, soft pastel peach-cream walls with rounded bevelled skirting, one big arched window opening and one door opening, the front wall and ceiling removed so we see inside, completely empty of furniture. |

The pilot is passed when: the five GLBs load in the engine at the right scale (lamp about 0.4 m, bed about 1.9 m, room 4.5 m wide), Googoo looks like he belongs next to them, the lamp shade and switch move as separate parts, and the cow auto-rigs without wrecking its shape. Fix the shared prompt now, not after 118 props.

## 4. The full list (118 items)

Columns: **Voice** = whether the Farsi word is already in `vocab/words_v2.json` or the starter words in `index.html` (if not, it needs voice lines: word, where is, this is, say it). **Size** = real width x depth x height in metres. **Parts** = Generate in Parts. **Rig** = a Tripo auto-rig may be wanted later. **Pri** = M must-have, N nice-to-have. **B** = batch. "Shown" copies are used for the triangle totals (food counts 0.4 because only about 4 of the 10 are on screen at once). Tris = polycount slider value in thousands.

### House: living room (batch 1, 12 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `room_living_shell.glb` | — | no word (world/furniture piece) | 4.5x4x2.8 | L large, 12k, 1024 px | N | N | M | 1 | 1 | an empty cut-away dollhouse view of a cosy living room shell: warm light-wood floor, soft pastel peach-cream walls with rounded bevelled skirting, one big arched window opening and one door opening, the front wall and ceiling removed so we see inside, completely empty of furniture. |
| `living_sofa.glb` | مبل | **NOT in words_v2: voice line needed** | 1.8x0.85x0.8 | L large, 10k, 1024 px | N | N | M | 1 | 1 | a chunky rounded two-seat sofa in soft dusty-blue fabric with plump cream cushions, thick rounded arms, short round wooden feet. |
| `living_armchair.glb` | مبل | **NOT in words_v2: voice line needed** | 0.8x0.8x0.8 | M medium, 6k, 1024 px | N | N | M | 1 | 1 | a chunky rounded armchair in soft mustard-yellow fabric with one cream cushion, thick rounded arms, short round wooden feet. |
| `living_coffee_table.glb` | میز | starter word (index.html) | 1.0x0.6x0.4 | M medium, 3k, 1024 px | N | N | M | 1 | 1 | a low rounded oval coffee table in light pastel wood with a thick soft-edged top and four chunky tapered legs. |
| `living_tv_cabinet.glb` | تلویزیون | in words_v2 | 1.4x0.45x1.2 | L large, 8k, 1024 px | Y (screen, doors) | N | M | 1 | 1 | a low pastel-mint wooden TV cabinet with two rounded doors and a chunky flat-screen TV on top whose screen is a plain glossy dark grey, no picture. |
| `living_floor_lamp.glb` | چراغ | starter word (index.html) | 0.4x0.4x1.5 | M medium, 4k, 1024 px | Y (shade, switch) | N | M | 1 | 1 | a tall floor lamp with a slim cream pole, round soft base and a big rounded drum lampshade in warm cream with a soft glow, one small chunky switch on the pole. |
| `living_bookshelf.glb` | کتابخونه | **NOT in words_v2: voice line needed** | 1.0x0.35x1.6 | M medium, 8k, 1024 px | N | N | M | 1 | 1 | a chunky rounded wooden bookshelf with four open shelves holding a few plain pastel-coloured books with blank spines and two small plain decorations. |
| `living_picture_frame.glb` | عکس | **NOT in words_v2: voice line needed** | 0.5x0.04x0.4 | S small, 1.5k, 512 px | N | N | M | 1 | 1 | a rounded wooden picture frame with a thick soft border, hanging flat, showing a simple pastel picture of a sun over green hills, no text. |
| `living_door.glb` | در | in words_v2 | 1.0x0.1x2.1 | M medium, 4k, 1024 px | Y (door, handle) | N | M | 1 | 1 | a rounded wooden room door in warm pastel wood with a thick soft frame, two soft panels and a chunky round satin-blue door knob. |
| `living_window_curtains.glb` | پنجره | in words_v2 | 1.6x0.2x1.6 | M medium, 6k, 1024 px | Y (curtains) | N | M | 1 | 1 | a big arched window with a thick cream frame and four soft panes, with soft rounded pastel-blue curtains tied back at both sides and a small windowsill. |
| `living_korsi.glb` | کرسی | **NOT in words_v2: voice line needed** | 1.4x1.4x0.6 | M medium, 6k, 1024 px | N | N | M | 1 | 1 | a Persian korsi: a low square wooden table covered by a thick quilted blanket in soft pastel red and cream, draping to the floor, with two plump cushions around it. |
| `living_carpet_persian.glb` | فرش | **NOT in words_v2: voice line needed** | 2.4x1.6x0.02 | M medium, 3k, 1024 px | N | N | M | 1 | 1 | a flat rectangular Persian carpet, seen from above at an angle, soft pastel red, cream and blue geometric medallion pattern with a fringed edge, very thin, abstract pattern with no text. |

### House: play room (batch 1, 9 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `room_play_shell.glb` | — | no word (world/furniture piece) | 4x4x2.8 | L large, 12k, 1024 px | N | N | M | 1 | 1 | an empty cut-away dollhouse view of a playroom shell: bright soft-wood floor, pastel sunny-yellow and cream walls with a rounded skirting, one big window opening and one door opening, front wall and ceiling removed, completely empty. |
| `toy_box.glb` | جعبه اسباب‌بازی | **NOT in words_v2: voice line needed** | 0.8x0.5x0.5 | M medium, 4k, 1024 px | Y (lid) | N | M | 1 | 1 | a chunky rounded toy chest in pastel sky blue with a lid slightly open and a soft cream trim, round satin-blue handles on the sides, no pictures or text. |
| `toy_ball.glb` | توپ | starter word (index.html) | 0.3x0.3x0.3 | S small, 1.5k, 512 px | N | N | M | 1 | 1 | a big smooth bouncy ball with soft pastel red, yellow and blue panels, matte rubbery finish. |
| `toy_teddy_bear.glb` | خرس | starter word (index.html) | 0.45x0.35x0.6 | M medium, 5k, 1024 px | N | N (nice: rig) | M | 1 | 1 | a soft round teddy bear sitting, warm honey-brown plush with a cream muzzle and belly, round ears, little pastel-blue bow tie, simple dot eyes, friendly smile. |
| `toy_drum.glb` | طبل | in words_v2 | 0.4x0.4x0.35 | S small, 2.5k, 512 px | N | N | M | 1 | 1 | a small toy drum with a soft cream drum skin, a pastel red rounded body with a chunky blue stripe, and two chunky wooden drumsticks resting on top. |
| `toy_blocks.glb` | مکعب | **NOT in words_v2: voice line needed** | 0.5x0.4x0.3 | S small, 3k, 512 px | N | N | M | 1 | 1 | a small neat stack of six chunky wooden toy blocks in pastel red, yellow, blue, green and orange, rounded edges, blank sides with no letters or numbers. |
| `toy_kite.glb` | بادبادک | in words_v2 | 0.7x0.1x1.0 | M medium, 3k, 1024 px | N | N | N | 1 | 1 | a diamond-shaped kite in soft pastel blue, yellow and pink panels with a short rounded tail of three bows, no strings, seen flat. |
| `toy_piano.glb` | پیانو | in words_v2 | 0.6x0.4x0.3 | M medium, 5k, 1024 px | Y (keys) | N | N | 1 | 1 | a small toy piano with a pastel pink rounded body, chunky cream keys and a few chunky blue keys, short round legs, no text. |
| `toy_doll.glb` | عروسک | in words_v2 | 0.3x0.15x0.5 | S small, 3k, 512 px | N | N | N | 1 | 1 | a soft rag doll with a round cream face, simple dot eyes, yarn-brown pigtails, a pastel blue dress and little red shoes. |

### House: bedroom (batch 1, 8 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `room_bedroom_shell.glb` | — | no word (world/furniture piece) | 4x3.6x2.8 | L large, 12k, 1024 px | N | N | M | 1 | 1 | an empty cut-away dollhouse view of a child's bedroom shell: warm light-wood floor, soft pastel blue and cream walls with a rounded skirting, one round-topped window opening and one door opening, front wall and ceiling removed, completely empty. |
| `bedroom_bed.glb` | تخت | starter word (index.html) | 1.9x1.0x0.9 | L large, 10k, 1024 px | N | N | M | 1 | 1 | a cosy child's bed with a chunky rounded cream wooden frame and a soft headboard with satin-blue trim, a thick pastel-blue mattress, a plump pillow and a folded blanket on top. |
| `bedroom_pillow.glb` | بالش | **NOT in words_v2: voice line needed** | 0.6x0.4x0.15 | S small, 1.5k, 512 px | N | N | M | 1 | 1 | a single plump rounded rectangular pillow in soft cream with a pastel-blue piped edge. |
| `bedroom_blanket.glb` | پتو | **NOT in words_v2: voice line needed** | 1.4x1.0x0.12 | S small, 2.5k, 512 px | N | N | M | 1 | 1 | a soft thick blanket folded neatly, pastel blue with a cream border and gentle rounded folds, plain with no text. |
| `bedroom_wardrobe.glb` | کمد | **NOT in words_v2: voice line needed** | 1.2x0.55x1.9 | L large, 8k, 1024 px | Y (two doors) | N | M | 1 | 1 | a chunky rounded wardrobe in soft cream wood with two big doors with round satin-blue knobs, a small rounded crown top and short round feet. |
| `bedroom_nightstand.glb` | — | no word (world/furniture piece) | 0.5x0.4x0.5 | M medium, 3k, 1024 px | Y (drawer) | N | N | 1 | 1 | a small rounded bedside table in pastel blue wood with one drawer and a round satin knob, short round legs. |
| `bedroom_lamp.glb` | چراغ | starter word (index.html) | 0.25x0.25x0.4 | S small, 3k, 512 px | Y (shade, switch) | N | M | 1 | 1 | a small bedside table lamp with a round cream ceramic base and a rounded pastel-blue lampshade glowing softly, one small chunky switch on the base. |
| `bedroom_rug.glb` | فرش | **NOT in words_v2: voice line needed** | 1.6x1.2x0.02 | S small, 1k, 512 px | N | N | N | 1 | 1 | a flat round woolly bedroom rug in soft cream with a pastel-blue border ring, seen from above at an angle, very thin, no text. |

### House: kitchen (batch 2, 12 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `room_kitchen_shell.glb` | — | no word (world/furniture piece) | 4x3.6x2.8 | L large, 12k, 1024 px | N | N | M | 2 | 1 | an empty cut-away dollhouse view of a kitchen shell: pastel mint and cream tiled floor, soft sunny walls with a rounded skirting, one window opening and one door opening, front wall and ceiling removed, completely empty. |
| `kitchen_fridge.glb` | یخچال | **NOT in words_v2: voice line needed** | 0.7x0.7x1.7 | L large, 8k, 1024 px | Y (door) | N | M | 2 | 1 | a chunky rounded fridge in pastel mint with a big top door and a small bottom door, thick soft round satin handles, blank doors with no magnets. |
| `kitchen_stove.glb` | — | no word (world/furniture piece) | 0.6x0.6x0.9 | M medium, 6k, 1024 px | Y (oven door) | N | N | 2 | 1 | a chunky rounded cream stove with four soft round burners on top, a rounded oven door with a satin-blue handle and two chunky knobs, no numbers. |
| `kitchen_table.glb` | میز | starter word (index.html) | 1.2x0.8x0.65 | M medium, 4k, 1024 px | N | N | M | 2 | 1 | a rounded family dining table in light pastel wood with a thick soft-edged round-cornered top and four chunky tapered legs. |
| `kitchen_chair.glb` | صندلی | starter word (index.html) | 0.4x0.4x0.8 | M medium, 3k, 1024 px | N | N | M | 2 | 1 | a chunky rounded wooden kitchen chair in pastel mint with a round seat, a soft rounded backrest and four chunky legs, seat height about 0.45 m. |
| `kitchen_samovar.glb` | سماور | **NOT in words_v2: voice line needed** | 0.35x0.35x0.5 | M medium, 5k, 1024 px | Y (lid, tap) | N | M | 2 | 1 | a Persian samovar tea urn with a rounded body in soft satin pastel gold-cream, a small chunky tap, two curved handles, a rounded lid with a little teapot on top, gentle cheerful toy look. |
| `kitchen_tea_glass.glb` | استکان | **NOT in words_v2: voice line needed** | 0.07x0.07x0.1 | S small, 1.5k, 512 px | N | N | M | 2 | 1 | a small Persian tea glass shaped like a rounded tulip with a gentle waist, filled with warm amber tea, on a small cream saucer with a pastel-blue rim, one sugar cube beside it. |
| `kitchen_fruit_bowl.glb` | میوه | **NOT in words_v2: voice line needed** | 0.35x0.35x0.2 | S small, 3k, 512 px | N | N | N | 2 | 1 | a wide pastel-blue rounded bowl filled with plump toy-like apples, oranges and pears in soft pastel colours. |
| `kitchen_pot.glb` | قابلمه | **NOT in words_v2: voice line needed** | 0.3x0.3x0.2 | S small, 2k, 512 px | N | N | N | 2 | 1 | a chunky rounded cooking pot in pastel cream with a satin-blue rim, a rounded lid and two thick round handles. |
| `kitchen_bowl.glb` | کاسه | **NOT in words_v2: voice line needed** | 0.2x0.2x0.1 | S small, 1k, 512 px | N | N | N | 2 | 1 | a simple deep rounded soup bowl in soft cream with a pastel-blue rim. |
| `kitchen_plate_spoon.glb` | بشقاب | in words_v2 | 0.25x0.25x0.05 | S small, 1.5k, 512 px | N | N | M | 2 | 1 | a round pastel-blue plate with a cream rim and a chunky rounded spoon lying next to it. |
| `kitchen_cup.glb` | لیوان | in words_v2 | 0.08x0.08x0.1 | S small, 1k, 512 px | N | N | M | 2 | 1 | a chunky rounded drinking cup in soft pastel yellow with a thick round handle, plain, no print. |

### House: food pool (used by kitchen, shops, farm) (batch 2, 10 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `food_apple.glb` | سیب | starter word (index.html) | 0.08x0.08x0.08 | S small, 1.5k, 512 px | N | N | M | 2 | 0.4 | a single plump toy-like red apple with a little brown stem and one soft green leaf, smooth satin finish. |
| `food_banana.glb` | موز | starter word (index.html) | 0.2x0.05x0.08 | S small, 1.5k, 512 px | N | N | M | 2 | 0.4 | a single plump toy-like yellow banana, softly curved, rounded brown tips, smooth satin finish. |
| `food_grapes.glb` | انگور | in words_v2 | 0.12x0.1x0.12 | S small, 2.5k, 512 px | N | N | N | 2 | 0.4 | a bunch of plump round purple-pastel grapes with a short green stem and one leaf, smooth satin finish. |
| `food_strawberry.glb` | توت‌فرنگی | in words_v2 | 0.05x0.05x0.06 | S small, 1.5k, 512 px | N | N | N | 2 | 0.4 | a single plump toy-like red strawberry with a green leafy top and a few large soft cream dots instead of tiny seeds. |
| `food_watermelon_slice.glb` | هندونه | in words_v2 | 0.2x0.08x0.12 | S small, 2k, 512 px | N | N | M | 2 | 0.4 | one big wedge slice of watermelon, bright pink-red flesh, a few large black seeds, a soft green rind, rounded edges. |
| `food_carrot.glb` | هویج | in words_v2 | 0.15x0.04x0.04 | S small, 1.5k, 512 px | N | N | M | 2 | 0.4 | a single plump toy-like orange carrot with a tuft of soft green leaves, rounded tip. |
| `food_egg.glb` | تخم‌مرغ | in words_v2 | 0.06x0.045x0.045 | S small, 1k, 512 px | N | N | M | 2 | 0.4 | a single smooth cream-white egg standing upright in a tiny pastel-blue egg cup. |
| `food_cake.glb` | کیک | in words_v2 | 0.25x0.25x0.15 | S small, 3k, 512 px | N | N | M | 2 | 0.4 | a round birthday cake with soft pink icing, a cream swirl border, three plump candles with little soft flames and a cherry on top, no writing. |
| `food_icecream.glb` | بستنی | in words_v2 | 0.08x0.08x0.2 | S small, 2k, 512 px | N | N | N | 2 | 0.4 | an ice cream cone with two chunky scoops, pastel pink and cream, a golden waffle cone, a tiny cherry on top. |
| `drink_milk_bottle.glb` | شیر | starter word (index.html) | 0.07x0.07x0.2 | S small, 1.5k, 512 px | N | N | M | 2 | 0.4 | a chunky rounded milk bottle in soft white with a pastel-blue cap and a small plain blank label. |

### House: bathroom (batch 3, 8 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `room_bathroom_shell.glb` | — | no word (world/furniture piece) | 3x3x2.8 | L large, 12k, 1024 px | N | N | M | 3 | 1 | an empty cut-away dollhouse view of a bathroom shell: pastel aqua tiled floor and half-tiled cream walls with rounded corners, one small round window opening and one door opening, front wall and ceiling removed, completely empty. |
| `bath_tub.glb` | حموم | in words_v2 | 1.5x0.75x0.55 | L large, 8k, 1024 px | N | N | M | 3 | 1 | a chunky rounded bathtub in glossy-satin cream with short round feet and a thick soft rim, a chunky satin-blue tap, empty and clean. |
| `bath_sink.glb` | روشویی | **NOT in words_v2: voice line needed** | 0.6x0.45x0.85 | M medium, 5k, 1024 px | N | N | M | 3 | 1 | a rounded pedestal washbasin in cream with a chunky satin-blue tap and a soft round pedestal. |
| `bath_potty.glb` | دستشویی | in words_v2 | 0.3x0.35x0.3 | S small, 2.5k, 512 px | Y (lid) | N | M | 3 | 1 | a small child's potty chair in pastel blue with a soft round seat, a rounded backrest and a lid, friendly and clean. |
| `bath_toothbrush.glb` | مسواک | in words_v2 | 0.18x0.03x0.03 | S small, 1.2k, 512 px | N | N | M | 3 | 1 | a chunky child's toothbrush with a fat pastel-blue handle and a soft cream rounded head with short rounded bristles. |
| `bath_soap.glb` | صابون | in words_v2 | 0.1x0.07x0.04 | S small, 1k, 512 px | N | N | M | 3 | 1 | a rounded bar of soap in pastel pink with a soft round edge and a few small soft bubbles on it. |
| `bath_towel.glb` | حوله | **NOT in words_v2: voice line needed** | 0.5x0.3x0.1 | S small, 2k, 512 px | N | N | N | 3 | 1 | a thick folded bath towel in soft pastel cream with a blue stripe, neatly folded, fluffy and rounded. |
| `bath_rubber_duck.glb` | اردک | in words_v2 | 0.12x0.1x0.1 | S small, 2k, 512 px | N | N | M | 3 | 1 | a classic chubby rubber duck in bright pastel yellow with an orange beak and simple dot eyes, glossy smooth. |

### Courtyard حیاط (with shared sky pieces) (batch 4, 10 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `courtyard_ground.glb` | حیاط | **NOT in words_v2: voice line needed** | 10x8x0.2 | L large, 10k, 1024 px | N | N | M | 4 | 1 | a Persian courtyard floor piece seen from above at an angle: pastel cream and terracotta tiled paving with a rectangular cut-out for a pool, raised soft green flower beds along the edges, low rounded cream walls on three sides with a soft blue tile pattern, empty. |
| `courtyard_wall_gate.glb` | در | in words_v2 | 3x0.3x2.4 | L large, 8k, 1024 px | Y (gate) | N | M | 4 | 1 | a chunky blue-tiled courtyard wall section with an arched wooden gate in pastel turquoise and cream, rounded top, soft round satin knobs. |
| `courtyard_hoz_pool.glb` | حوض | **NOT in words_v2: voice line needed** | 3x2x0.6 | L large, 9k, 1024 px | N | N | M | 4 | 1 | a Persian hoz: a rectangular shallow pool with a thick rounded cream stone rim, clear pastel-turquoise water with a small fountain jet in the middle, empty of fish. |
| `courtyard_goldfish.glb` | ماهی قرمز | **NOT in words_v2: voice line needed** | 0.12x0.05x0.06 | S small, 1.5k, 512 px | N | Y (simple swim, nice) | M | 4 | 3 | a chubby friendly orange-red goldfish with soft flowing fins and a round dot eye, smooth glossy-satin. |
| `courtyard_pomegranate_tree.glb` | درخت | in words_v2 | 2x2x3 | L large, 12k, 1024 px | N | N | M | 4 | 1 | a small pomegranate tree with a thick rounded brown trunk and a big soft round canopy of glossy light-green leaves with several plump red pomegranates and a few orange blossoms. |
| `courtyard_pomegranate.glb` | انار | **NOT in words_v2: voice line needed** | 0.1x0.1x0.1 | S small, 1.5k, 512 px | N | N | M | 4 | 0.5 | a single plump toy-like red pomegranate with a rounded crown on top, smooth satin finish, one small leaf. |
| `courtyard_geranium_pots.glb` | گلدون | **NOT in words_v2: voice line needed** | 0.5x0.5x0.5 | M medium, 5k, 1024 px | N | N | M | 4 | 3 | three chunky rounded terracotta-pastel flowerpots with bright pink and red geraniums and soft green leaves, grouped together. |
| `courtyard_takht.glb` | تخت | starter word (index.html) | 2x1.4x0.7 | L large, 8k, 1024 px | N | N | N | 4 | 1 | a Persian takht: a raised wooden platform in light pastel wood with a thick soft edge and a little rail, covered with a soft red and cream carpet and two plump cushions. |
| `sky_dome_day.glb` | آسمون | **NOT in words_v2: voice line needed** | 50x50x25 | M medium, 3k, 1024 px | N | N | M | 4 | 1 | a gentle half-dome sky in soft pastel blue fading to cream at the horizon, with a few faint pastel clouds painted on, seen as a smooth dome, no sun disc, no text (may be better as a skybox in the engine). |
| `sky_cloud_set.glb` | ابر | in words_v2 | 3x1x1 | M medium, 4k, 1024 px | N | N | M | 4 | 2 | three fluffy rounded white clouds of different sizes in a row, soft pastel cream-white matte. |

### Street کوچه (batch 5, 8 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `street_ground.glb` | کوچه | **NOT in words_v2: voice line needed** | 12x6x0.2 | L large, 8k, 1024 px | N | N | M | 5 | 1 | a short child-friendly street piece seen from above at an angle: soft grey-blue road with a pastel cream dashed centre line, a raised rounded pavement on both sides in warm cream tiles, a crossing with soft white stripes, empty. |
| `street_house_row.glb` | خونه | **NOT in words_v2: voice line needed** | 8x1x4 | L large, 14k, 1024 px | Y (doors) | N | M | 5 | 1 | a row of three chunky rounded townhouse fronts in pastel peach, mint and sky-blue with big arched wooden doors, round windows with flower boxes and soft flat roofs, no signs or numbers. |
| `street_lamp_post.glb` | چراغ | starter word (index.html) | 0.3x0.3x3 | M medium, 3k, 1024 px | N | N | M | 5 | 2 | a slim rounded street lamp post in dark satin-blue with a soft round warm-glowing lamp head and a chunky round base. |
| `street_traffic_light.glb` | چراغ راهنما | **NOT in words_v2: voice line needed** | 0.3x0.3x2.5 | M medium, 4k, 1024 px | Y (3 lights) | N | M | 5 | 1 | a chunky rounded traffic light on a satin dark-grey pole with a rounded rectangular head holding three big round lamps in soft red, yellow and green. |
| `street_taxi.glb` | تاکسی | in words_v2 | 3.4x1.5x1.3 | L large, 12k, 1024 px | N | N | M | 5 | 1 | a chunky rounded toy-like taxi car in soft pastel yellow with rounded wheels, big friendly windows and a plain blank roof light, no writing. |
| `street_bus.glb` | اتوبوس | in words_v2 | 6x1.8x2 | L large, 14k, 1024 px | N | N | M | 5 | 1 | a chunky rounded toy-like city bus in pastel blue and cream with big square windows, round wheels and a friendly flat front, no writing or numbers. |
| `street_bike.glb` | دوچرخه | in words_v2 | 1.0x0.4x0.6 | M medium, 6k, 1024 px | N | N | M | 5 | 1 | a small child's bicycle with a rounded pastel red frame, chunky wheels, a basket, a satin-blue seat and handlebars, simple thick tubes. |
| `street_cat.glb` | گربه | in words_v2 | 0.5x0.2x0.35 | M medium, 5k, 1024 px | N | Y | M | 5 | 1 | a chubby friendly sitting cat, soft orange-and-cream tabby with big round ears, simple dot eyes and a curled tail. |

### Bakery and fruit shop نونوایی، میوه‌فروشی (batch 6, 7 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `shop_bakery_building.glb` | نونوایی | **NOT in words_v2: voice line needed** | 5x3x3.5 | L large, 14k, 1024 px | N | N | M | 6 | 1 | a chunky rounded little bakery shop front in warm cream and pastel orange with a big open arched window counter, a striped pastel awning with no text, a round chimney and a wooden door. |
| `shop_bakery_oven.glb` | تنور | **NOT in words_v2: voice line needed** | 1.2x1.2x1.1 | M medium, 6k, 1024 px | Y (hatch, door) | N | M | 6 | 1 | a Persian bakery clay oven with a rounded terracotta-pastel dome, a glowing soft orange opening and a thick rounded stone base, clean and friendly. |
| `shop_bread_lavash.glb` | نون | starter word (index.html) | 0.5x0.35x0.02 | S small, 1.5k, 512 px | N | N | M | 6 | 3 | a big thin flat lavash flatbread, soft golden-brown with a few gentle toasty spots, slightly wavy, seen lying flat. |
| `shop_bread_sangak.glb` | سنگک | **NOT in words_v2: voice line needed** | 0.8x0.35x0.03 | S small, 2k, 512 px | N | N | M | 6 | 1 | a long oval Persian sangak flatbread, golden-brown with small soft dimples, slightly curled edge, lying flat. |
| `shop_fruit_stall.glb` | میوه‌فروشی | **NOT in words_v2: voice line needed** | 3x1.5x2.4 | L large, 12k, 1024 px | N | N | M | 6 | 1 | a chunky rounded wooden fruit stall with a striped pastel green-and-cream awning with no text, two sloped display trays filled with plump toy-like apples, oranges, pears and watermelons. |
| `shop_basket.glb` | سبد | **NOT in words_v2: voice line needed** | 0.4x0.3x0.3 | S small, 2.5k, 512 px | N | N | M | 6 | 1 | a woven round shopping basket in warm pastel straw colour with a thick curved handle and a soft blue ribbon, empty. |
| `shop_counter.glb` | پیشخون | **NOT in words_v2: voice line needed** | 2x0.7x1.1 | L large, 8k, 1024 px | N | N | N | 6 | 1 | a chunky rounded wooden shop counter in pastel cream with a soft blue top, a rounded front panel and a small toy-like cash register with blank buttons. |

### Park پارک (batch 7, 8 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `park_ground.glb` | پارک | **NOT in words_v2: voice line needed** | 14x12x0.3 | L large, 10k, 1024 px | N | N | M | 7 | 1 | a park terrain piece seen from above at an angle: soft green grass with gentle hills, a cream gravel path, a small round pastel-blue duck pond in one corner and a rounded sandy patch in another, empty. |
| `park_slide.glb` | سرسره | in words_v2 | 1.2x2x1.6 | L large, 8k, 1024 px | N | N | M | 7 | 1 | a chunky rounded playground slide with a pastel yellow slide chute, a satin-blue ladder, soft round rails and a red rounded platform. |
| `park_swing.glb` | تاب | **NOT in words_v2: voice line needed** | 2x1.2x1.8 | L large, 8k, 1024 px | Y (seat) | N | M | 7 | 1 | a chunky rounded playground swing set with a pastel-blue A-frame, thick red ropes and two soft rounded seats in pastel yellow. |
| `park_bench.glb` | نیمکت | **NOT in words_v2: voice line needed** | 1.5x0.5x0.85 | M medium, 4k, 1024 px | N | N | M | 7 | 2 | a chunky rounded park bench in light pastel wood with a thick curved backrest and rounded satin-blue legs. |
| `park_tree.glb` | درخت | in words_v2 | 2.5x2.5x4 | L large, 10k, 1024 px | N | N | M | 7 | 4 | a big friendly park tree with a thick rounded trunk and a big soft round fluffy canopy of pastel green leaves, simple and chunky. |
| `park_duck.glb` | اردک | in words_v2 | 0.3x0.2x0.25 | M medium, 4k, 1024 px | N | Y | M | 7 | 3 | a chubby white duck with an orange rounded beak and simple dot eyes, floating pose, smooth glossy-satin. |
| `park_sandbox.glb` | شن | **NOT in words_v2: voice line needed** | 1.4x1.4x0.3 | M medium, 4k, 1024 px | N | N | N | 7 | 1 | a square sandbox with thick rounded pastel-blue wooden sides filled with soft pale sand, a small bucket and spade lying in it. |
| `park_picnic_set.glb` | پیک‌نیک | **NOT in words_v2: voice line needed** | 1.2x1.2x0.3 | M medium, 6k, 1024 px | N | N | N | 7 | 1 | a picnic set: a flat pastel red-and-cream checked picnic blanket with a rounded wicker basket on it holding bread and an apple, no text. |

### Farm مزرعه (batch 8, 9 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `farm_ground.glb` | مزرعه | **NOT in words_v2: voice line needed** | 16x12x0.3 | L large, 10k, 1024 px | N | N | M | 8 | 1 | a farm terrain piece seen from above at an angle: gentle green meadow, a packed pale-brown dirt yard, a small ploughed field with soft rows and a sandy path, empty. |
| `farm_barn.glb` | طویله | **NOT in words_v2: voice line needed** | 5x4x4 | L large, 14k, 1024 px | Y (big doors) | N | M | 8 | 1 | a chunky rounded red barn with white trim, a rounded gambrel roof, big double doors and a round hay-loft window, no text. |
| `farm_fence.glb` | نرده | **NOT in words_v2: voice line needed** | 2x0.1x0.9 | M medium, 3k, 1024 px | N | N | M | 8 | 6 | a short section of a chunky rounded white wooden farm fence with three thick horizontal rails and round-topped posts. |
| `farm_tractor.glb` | تراکتور | in words_v2 | 2.6x1.4x1.6 | L large, 12k, 1024 px | N | N | M | 8 | 1 | a chunky rounded toy-like farm tractor in pastel green with big rounded black-grey rear wheels, a small yellow cab and a satin-blue seat. |
| `farm_cow.glb` | گاو | in words_v2 | 1.4x0.5x1.0 | M medium, 8k, 1024 px | N | Y | M | 8 | 1 | a chubby friendly cow standing, white with soft black patches, pink nose, rounded horns and a small bell, simple dot eyes. |
| `farm_sheep.glb` | گوسفند | in words_v2 | 1.0x0.5x0.7 | M medium, 6k, 1024 px | N | Y | M | 8 | 1 | a chubby fluffy sheep standing, a rounded cream woolly body with a small dark-grey face, ears and legs, simple dot eyes. |
| `farm_chicken.glb` | مرغ | in words_v2 | 0.35x0.2x0.35 | M medium, 3k, 1024 px | N | Y | M | 8 | 2 | a chubby hen standing, soft white-cream feathers, a small red comb, an orange beak and simple dot eyes. |
| `farm_horse.glb` | اسب | in words_v2 | 1.8x0.5x1.5 | M medium, 8k, 1024 px | N | Y | M | 8 | 1 | a friendly toy-like chestnut-brown horse standing, a soft cream mane and tail, chunky rounded legs and simple dot eyes. |
| `farm_donkey.glb` | الاغ | **NOT in words_v2: voice line needed** | 1.3x0.45x1.1 | M medium, 7k, 1024 px | N | Y | N | 8 | 1 | a chubby friendly grey donkey standing with big rounded ears, a cream muzzle, a short tufted tail and simple dot eyes. |

### School مدرسه (batch 9, 5 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `room_school_shell.glb` | مدرسه | **NOT in words_v2: voice line needed** | 6x5x3 | L large, 12k, 1024 px | N | N | M | 9 | 1 | an empty cut-away dollhouse view of a classroom shell: warm light-wood floor, soft pastel green and cream walls with a rounded skirting, two big window openings and one door opening, front wall and ceiling removed, completely empty. |
| `school_blackboard.glb` | تخته | **NOT in words_v2: voice line needed** | 2.4x0.1x1.2 | M medium, 3k, 1024 px | N | N | M | 9 | 1 | a wide rounded blackboard in a thick pastel light-wood frame, a plain dark green-grey surface with a small chalk ledge holding two chunky chalks, completely blank. |
| `school_desk.glb` | میز | starter word (index.html) | 0.8x0.5x0.6 | M medium, 4k, 1024 px | N | N | M | 9 | 3 | a small child's desk with a chair attached: a rounded pastel-blue top and seat on chunky light-wood legs, soft round edges, blank. |
| `school_easel.glb` | رنگ | **NOT in words_v2: voice line needed** | 0.7x0.6x1.3 | M medium, 5k, 1024 px | N | N | N | 9 | 1 | a child's painting easel in light pastel wood with a blank canvas and a tray holding three chunky round paint pots in red, yellow and blue and one fat brush. |
| `school_pencil_giant.glb` | مداد | in words_v2 | 0.1x0.1x0.8 | S small, 1.5k, 512 px | N | N | N | 9 | 2 | a giant chunky decorative pencil in pastel yellow with a rounded pink eraser top and a soft sharpened tip, standing upright. |

### Beach ساحل (batch 10, 6 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `beach_ground.glb` | ساحل | **NOT in words_v2: voice line needed** | 14x12x0.3 | L large, 10k, 1024 px | N | N | M | 10 | 1 | a beach terrain piece seen from above at an angle: soft pale-gold sand with gentle ripples, a curved shoreline with pastel turquoise shallow water and tiny soft rounded foam, a few smooth rounded rocks at one corner, empty. |
| `beach_sandcastle.glb` | قلعه شنی | **NOT in words_v2: voice line needed** | 0.8x0.8x0.6 | M medium, 5k, 1024 px | N | N | M | 10 | 1 | a chunky rounded sandcastle in pale-gold sand with four round towers, a gate arch and a small red flag with no emblem. |
| `beach_crab.glb` | خرچنگ | **NOT in words_v2: voice line needed** | 0.3x0.2x0.15 | M medium, 3k, 1024 px | N | Y | M | 10 | 1 | a chubby friendly red-orange crab with two big round claws, short rounded legs and two tiny round eyes on stalks. |
| `beach_boat.glb` | قایق | in words_v2 | 2x0.9x1.5 | L large, 8k, 1024 px | N | N | M | 10 | 1 | a small chunky rounded wooden sailboat in pastel blue and cream with a plain white triangular sail and a small red flag. |
| `beach_shell.glb` | صدف | in words_v2 | 0.15x0.12x0.06 | S small, 1.5k, 512 px | N | N | M | 10 | 3 | a chunky rounded scallop seashell in soft pastel pink and cream with gentle thick ridges. |
| `beach_bucket_spade.glb` | سطل | in words_v2 | 0.3x0.25x0.25 | S small, 2k, 512 px | N | N | M | 10 | 1 | a chunky rounded child's beach bucket in pastel red with a thick yellow handle and a matching chunky blue spade leaning on it. |

### Moon ماه and rocket موشک (batch 11, 6 items)

| File | Farsi | Voice | Size (m) | Class / tris / texture | Parts | Rig | Pri | B | Shown | Prompt (after the shared style prompt) |
|---|---|---|---|---|---|---|---|---|---|---|
| `moon_rocket.glb` | موشک | in words_v2 | 1.8x1.8x4.5 | H hero, 15k, 2048 px | Y (hatch) | N | M | 11 | 1 | a big chunky rounded toy rocket in cream and satin royal blue with a round porthole window and a rounded cyan-glow nose cone, a round openable hatch, three chunky rounded fins and a soft cyan-glow nozzle, same look as a friendly robot, no text or flag. |
| `moon_launch_pad.glb` | سکوی پرتاب | **NOT in words_v2: voice line needed** | 3x3x0.8 | L large, 8k, 1024 px | N | N | M | 11 | 1 | a chunky rounded rocket launch pad: a round cream platform with a thick satin-blue ring, a short rounded access tower and a soft grey base, clean and friendly. |
| `moon_ground.glb` | ماه | in words_v2 | 14x12x0.5 | L large, 10k, 1024 px | N | N | M | 11 | 1 | a moon surface terrain piece seen from above at an angle: soft pale-grey and cream rounded dusty ground with several smooth rounded craters of different sizes, no sharp rocks, empty. |
| `moon_rocks.glb` | سنگ | in words_v2 | 0.6x0.5x0.4 | M medium, 4k, 1024 px | N | N | N | 11 | 4 | three chunky smooth rounded moon rocks of different sizes in soft pale-grey, grouped together. |
| `moon_earth_planet.glb` | زمین | **NOT in words_v2: voice line needed** | 2x2x2 | M medium, 3k, 1024 px | N | N | M | 11 | 1 | a cute round planet Earth with soft pastel blue seas, gentle green continents and soft white swirling clouds, matte. |
| `sky_dome_night.glb` | ستاره | in words_v2 | 50x50x25 | M medium, 3k, 1024 px | N | N | M | 11 | 1 | a gentle half-dome starry sky in deep soft indigo fading to dark blue at the horizon with plump pastel-yellow stars and a few tiny planets, smooth dome, no text (may be better as a skybox in the engine). |

## 5. Batches and triangle totals

Batch 1 = the three rooms that exist today (living room, play room, bedroom). Then the game-plan order: kitchen, bathroom, courtyard, street, shops, park, farm, school, beach, moon. Anchors and pilot (section 2 and 3) are made before batch 1 and count inside their own batches.

### Per batch

| Batch | Content | Items | Must | Nice | Sum of tris (one of each) |
|---|---|---|---|---|---|
| 1 | Living room, play room, bedroom | 29 | 24 | 5 | 151.5k |
| 2 | Kitchen and food pool | 22 | 15 | 7 | 66k |
| 3 | Bathroom | 8 | 7 | 1 | 33.7k |
| 4 | Courtyard and shared sky | 10 | 9 | 1 | 62k |
| 5 | Street | 8 | 8 | 0 | 66k |
| 6 | Bakery and fruit shop | 7 | 6 | 1 | 46k |
| 7 | Park | 8 | 6 | 2 | 54k |
| 8 | Farm | 9 | 8 | 1 | 71k |
| 9 | School | 5 | 3 | 2 | 25.5k |
| 10 | Beach | 6 | 6 | 0 | 29.5k |
| 11 | Moon and rocket | 6 | 5 | 1 | 43k |
| **Total** | | **118** | **97** | **21** | **648.2k** |

### Visible triangles per area (all copies shown, plus Googoo 35k)

| Area | Props and world pieces | Googoo | Total | Over 250k? |
|---|---|---|---|---|
| Living room (batch 1, 12 items) | 71.5k | 35k | **106.5k** | no |
| Play room (batch 1, 9 items) | 39k | 35k | **74k** | no |
| Bedroom (batch 1, 8 items) | 41k | 35k | **76k** | no |
| Kitchen (+ food pool) (batch 2, 22 items) | 55.2k | 35k | **90.2k** | no |
| Bathroom (batch 3, 8 items) | 33.7k | 35k | **68.7k** | no |
| Courtyard (batch 4, 10 items) | 78.25k | 35k | **113.25k** | no |
| Street (batch 5, 8 items) | 69k | 35k | **104k** | no |
| Bakery and fruit shop (batch 6, 7 items) | 57k (incl. 8k of reused fruit) | 35k | **92k** | no |
| Park (batch 7, 8 items) | 96k | 35k | **131k** | no |
| Farm (batch 8, 9 items) | 89k | 35k | **124k** | no |
| School (batch 9, 5 items) | 35k | 35k | **70k** | no |
| Beach (batch 10, 6 items) | 32.5k | 35k | **67.5k** | no |
| Moon + rocket (batch 11, 6 items) | 55k | 35k | **90k** | no |

Result: no area is over 250k; the busiest (park, farm) are about 125-130k, below the 150-250k target, so there is 100k+ headroom per area for extra copies, richer shells or a few more props. Watch the street (bus, taxi, house row) and the farm (barn, tractor, animals) most; if a scene feels heavy on a phone, lower the polycount slider on repeated pieces (fence, trees) first.

Voice lines: 50 distinct Farsi words in this list are not in words_v2 or the starter words (marked NOT in words_v2 above); they need voice lines before the matching prop is tappable.

## 6. Checklist per prop (for the person running Tripo)

1. Open the row for the prop. Paste the shared style prompt (section 1) and then the row's prompt text. Add the negative prompt if there is a field for it. Attach the matching style anchor image if Tripo allows it.
2. Run free text-to-image. Generate a few; pick the one with ONE object, whole object in frame, centred, 3/4 view from slightly above, plain light grey background, no text, soft pastel toy look like Googoo. If none fits, edit the prompt and run again.
3. Image to 3D with: model H3.1, Texture on, PBR on, Remove Lighting on, Triangle topology, Private, polycount slider = the tris value in the row. If the row says Parts = Y, use Generate in Parts and name the movable parts.
4. Check the result in Tripo's viewer: shape matches the image, soft rounded edges, no holes or spikes, clean textures with no baked shadows or text, scale looks right. Redo with another image if not.
5. Export GLB.
6. Save as `C:\Users\ahmma\Downloads\Pash 3D\props\<file>.glb` using the exact file name in the row (for example `bedroom_lamp.glb`). Tick it off in your list; note any prop that needed a redo and why.

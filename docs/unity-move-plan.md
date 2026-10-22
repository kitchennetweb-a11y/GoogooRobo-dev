# Googoo Robo: plan for moving the game to Unity

Written 2026-10-22. This is a plan, not code. Nothing is built until you approve it.
Decision behind it: "Engine DECIDED: Unity" (docs/decisions.md). This is step **C** ("the full Unity move") from that decision.

## In short

- **Almost all of the content moves over unchanged:** about 1,360 voice clips and their manifest, the words, stories and lines files, the face kit, the Tripo props, Googoo and his Mixamo clips. Only the **game code** is rewritten: about 1,700 lines of web code become C#.
- **The Unity prototype already has a good start:** Googoo imports correctly (Generic rig), plus the procedural dance, the head guard, the face kit, a bedroom, phone GPU settings and picture checks run on the GPU.
- **Use Unity 6.3 LTS (6000.3.27f1).** It is already installed with Android support. Build for Android first, then iOS.
- **The first version your son can play is about 1–2 weeks away:** an Android test build of the home room with Googoo, taps, dance, voice and talk-back.
- **It matches the web game in about 6–10 weeks** of part-time work, most of it testing. Then the web version is frozen and stays the free demo.
- **The biggest risks are the mic on iOS, the Kids-store rules and running fast on cheap Android phones.** Each one gets an early small test, not a late surprise.
- **One urgent fix: the Unity project has no version control (git).** One mistake could lose work. That is the first thing to fix.

---

## 1. Feature by feature: web to Unity

**Legend:** **Reuse** = the same files go in as they are. **Port** = the logic is copied over, rewritten in C#. **New** = Unity needs something the web didn't.

### Content (mostly reused)

| Web | Unity | Type | Notes |
|---|---|---|---|
| `audio/*.mp3` (1,361 clips, 31 MB) + `audio/manifest.json` | Same files, loaded on demand by name (Addressables, stored in the app, no server) | Reuse | The key stays the file name, so `say('w_cat')` works the same. Unity re-packs the clips into a smaller format. **`name.mp3` (your son's name) goes into a "personal" group that never ships to the stores.** |
| `vocab/words_v2.json`, `stories.json`, `lines_*.csv` | Read as text files at start | Reuse | Same files. One tool keeps both engines' copies in sync. |
| Face kit (PNG layers + `face_kit.json`) | Already in Unity (`FaceKit.cs`, atlas, shader) | Reuse | Missing: the **picture on the face screen** (`face='pic'`, the word's picture when he says it). Small addition. |
| Emoji picture cards (the 🐮 🍎 pictures on cards and the face) | **New:** a set of picture images (free Noto Emoji pictures, or your own later) | New | Unity can't draw emoji the way a browser does. About 250 pictures in one sheet, the same on every phone. |
| Tripo props (`models/*.glb`, optimized) | Imported with glTFast (already installed), then the textures are pulled out into normal compressed textures | Reuse + small tool | Without that step, each prop uses 16 MB of phone memory (gpu-budget.md section 5). `Setup.cs` already does this for Googoo; reuse it. |
| Googoo + 19 Mixamo clips | Already in Unity (Generic import, clips cleaned onto the Tripo skeleton) | Reuse | — |
| Procedural moves: dance styles, arm IK, head guard | Already ported (`ProceduralDance.cs`, `HeadGuard.cs`) | Done | — |
| Newer web moves: fully still idle and sitting poses, procedural waves, head kept level, hands kept off the face | Port | Port | The web moved ahead on 2026-10-22; the Unity copy is older. |
| Synthesised sounds (beeps, boing, toot, giggle) | Recorded once from the web into short clips | Reuse | Easier than rebuilding the synth. |
| Song bed `song_bed.mp3` + folk chants | Same clips, played in sync | Reuse | The licence still needs replacing with a paid Suno track (section 5). |

### Game features (ported to C#)

| Feature | In Unity | Effort |
|---|---|---|
| Rooms home / play / bed, room tabs | One small scene per room (section 2) | M |
| Taps on body parts (with the Farsi word), springs, idle routines, peekaboo, jump/rocket/fly, ball (physics), bubbles, feed, moves, disco, lamp day/night | Port; Unity physics and particles replace the hand-made ones | M–L |
| Say it screen | Port | S |
| Book + 4 stories (he sits, the camera re-frames) | Port | S |
| Games: card Find, 3D Find, colour hunt, counting, animal sounds, star counting, dark-room torch Find | Port. The shared card helpers (`showDeck`, `cardAsk`, `answer`) are written once, then each game is short | M |
| Songs / folk chants over the instrumental bed, 4 dance styles | Port (the dance is already in Unity) | S |
| Night stars, bedtime invite (after 3 games or 6 minutes), hidden surprises in other rooms | Port | S |
| **Talk-back:** mic always on, voice detection, squeaky playback, wake from sleep | **Rewrite** with Unity's `Microphone` (section 5, risk 2). Same rules as the web: only listen when idle, ignore the mic while Googoo talks, about 0.75 s of quiet ends a clip, playback 1.65× faster | M, plus device testing |
| Stars + parent corner stats (`pash-stats-v1`) | The same data saved in one small file on the device | S |
| Parent corner behind the gear | Port, plus a **real parent gate** (an adult task, as monetization-plan.md asks) | S |
| "Show words" Farsi caption, Persian text in the parent corner | TextMeshPro + **RTLTMPro** (free) for Persian letter joining, plus the Vazirmatn font | S, plus a test |
| Phone-first layout: rails, mic + star counter top left, gear top right, tabs at the bottom, auto-fit camera (`measureRobot`) | Port with Unity's UI (uGUI), keeping clear of the notch and rounded corners on every phone | M |
| Design mode (`data/layout.json`, being built in another session) | See below | S |
| PWA (installable web app, offline cache) | **Not needed:** a store app is installed and works offline already | — |

**Design mode in Unity.** The Unity Editor *is* a design mode: you drag props, walls and buttons in the Scene view and change colours in the Inspector, with no extra code. **Recommended:** a one-time importer reads the web's `layout.json` into the Unity rooms, so nothing laid out on the web is lost; after that, the Unity rooms are the master copy. Keeping `layout.json` as a live shared file for both engines is possible, but it means two sources of truth and extra code in both engines.

---

## 2. How the Unity game is built

- **Scenes:** one always-loaded **Main** scene (Googoo, camera, UI, sound, saving), plus **one scene per room or place**, loaded on top of it. The three house rooms stay loaded so the tabs switch instantly. Outside places (courtyard, street, ...) load one at a time later. This matches gpu-budget.md: one area on screen at once.
- **Data-driven:** words, lines, stories, which games each room has, and the free/paid split live in data files, not in code. Adding a word = adding a row and a clip.
- **On-demand loading (Addressables):** voice clips and props load when they're needed and unload when they're not. Everything is inside the app; nothing is downloaded, which keeps it Kids-store safe and lets it work in airplane mode.
- **Toddler input:** only the first finger counts; tapping with the whole palm or several fingers is ignored; there is a short cooldown after each tap ("gently!" after 6 fast taps, as today); hit areas are big. The phone's back button and home gesture need the parent gate. In the parent corner, tell parents about Android screen pinning and iOS Guided Access.
- **Parent gate:** an adult task (for example "tap **seven**" written as a word under shuffled digits). It sits in front of the parent corner, the purchase screen and any links.
- **UI:** uGUI, which the prototype already uses, plus TextMeshPro. Keep one UI system, not two.
- **Platforms:** **Android first** (built on this PC). **iOS** as an Xcode project exported on this PC, then compiled on a cloud Mac (Codemagic: 500 free minutes a month) and sent to TestFlight. Unity's own Build Automation is the simpler but paid alternative.
- **Editor version: Unity 6.3 LTS (6000.3.27f1).** It is a long-term-support version (about two years of fixes), Android support is already installed, and it's a safer base for a store app.
  - The prototype is on 6000.6.7f1, which is not LTS and has only WebGL and Windows installed. Moving down a version isn't officially supported, but `Setup.MakeScene` rebuilds the scene from scripts anyway, so the plan is a **fresh 6.3 project, copy the scripts and assets in, and run Setup**: about half a day.
  - The Unity WebGL build isn't needed any more, because the web demo stays three.js.

---

## 3. How Claude agents work on Unity (and what you do)

**Agents can:**
- **Build without opening Unity:** batch mode builds the Android APK (`Setup.BuildAndroid`, to be added) on the RTX GPU, without `-nographics`, as HANDOFF.md says. Then `adb` installs it on your phone over USB and takes phone screenshots and logs.
- **Check their own work with pictures and numbers:**
  - The RigTest-style contact sheets already exist (rig, face, legs).
  - The Windows player's `-autoshot` screenshots exist.
  - To add, all small and automatic:
    - a budget check per room (draw calls, triangles, texture memory, against gpu-budget.md);
    - a content check ("every word has a clip and a picture", "no `name.mp3` in the store build");
    - a phone size check.
- **Unity's official Claude plugin** (in the Claude plugin directory, version 0.1.2 beta) adds Unity game-development, monetization and performance skills. It is **not installed yet**, and it is unclear whether it can drive the open editor. Plan: install it in phase 0 and test it for one hour. If it can't drive the editor, agents keep using batch mode, which already works.
- **Work in parallel, with care:**
  - Only **one Unity instance can open a project at a time**. Batch builds fail while you have the editor open on the same project, so builds go one at a time.
  - Scene files merge badly. One agent owns the scenes and prefabs; other agents write C# and data.
  - A second copy of the project lets two agents build at once, but each copy needs its own multi-GB `Library` folder and a long first import.

**What you do:**
1. **Once (about 1 hour):**
   - In Unity Hub, add **iOS Build Support** to 6000.3.27f1 (Android is already there).
   - Turn on **Developer options + USB debugging** on your Android phone and plug it in once to allow this PC.
   - Install the Unity plugin (`/plugin`, "Unity").
2. **Every milestone (15–30 minutes):** install the test build, then watch your son play and tell the agent what felt wrong. The things only a real phone and a real child show are the mic, speed, and whether the buttons are easy for him.
3. **Before iOS:** the Apple Developer account (US$99/yr) and a Codemagic account (free).
4. **Later:** the Google Play account (US$25 once) and 12 test families for the 14-day closed test (monetization-plan.md).

---

## 4. Roadmap

Effort: **agent days** = about one day of agent sessions with your quick reviews. Testing time is separate. The time on the calendar depends mostly on testing.

| Phase | What | Effort | Son can play |
|---|---|---|---|
| **0. Set up** | Git for the Unity project (urgent: today it has none); fresh 6.3 LTS project; Android build and install-to-phone in one command; perf settings; test the Unity plugin; copy in the content (clips, manifest, words, face kit); text test: Persian caption with RTLTMPro | 1–2 agent days; you: 1 hour | — |
| **1. First playable** | Home room; Googoo with the newest moves (still idle, waves, head level); taps with Farsi body-part words; dance; lamp; voice clips with pictures on the face; **talk-back**; feed | 4–6 agent days + 2–3 short test sessions | **M1: Android test build, home room + talk-back** |
| **2. Learning games + layout** | Phone layout (rails, tabs, mic, stars, gear); picture sheet; card Find, colour, counting, animals, Say it; stars saved; parent corner + real parent gate | 6–9 agent days + testing | **M2: home room with all 4 learning games** |
| **3. All rooms** | Play room (ball, bubbles, disco, peekaboo) and bedroom (sleep, night stars, night story, torch Find); Tripo props in all rooms (import tool + `layout.json` importer); book + stories; songs; 3D Find; moves; bedtime invite; surprises; lightmaps | 8–12 agent days + testing | **M3: the whole house** |
| **4. Match the web + speed** | Side-by-side check against the web game (every button, game and line); 30 fps when idle; app size; battery; test on the oldest phone you can borrow; son plays it for a week | 3–5 agent days + 1–2 weeks of play | **M4: Unity = the main game** |
| **5. iOS** | Xcode export, then Codemagic, then TestFlight; mic and sound on iPad and iPhone | 2–4 agent days + Apple waiting | M5: on the iPad |
| **6. Store** | Purchase (trial + lifetime unlock), privacy policy, Kids checklist, voice re-record (Googoo, not پاش), Play closed test | 4–6 agent days + about 2 weeks of waiting | Store release |

- **Total to match the web: about 22–34 agent days, roughly 6–10 calendar weeks part-time.** The stores come 3–5 weeks after that.
- New places (kitchen, courtyard, map) come after phase 4, built only in Unity.
- **Recommended early iOS check:** during phase 2, a one-screen iOS test build with only talk-back. The iOS mic is the riskiest unknown, so it's better to find out early. It needs the Apple account at that point.

**When the web version is frozen.**
- **Now:** no new features on the web. The in-progress work (Design mode, new Googoo in the web game) gets finished, and bugs get fixed.
- **At M4**, when your son has played the Unity build for a week and prefers it: the web is fully frozen. It stays at its current address as the free demo, with a store badge behind the parent gate once the app is out.

---

## 5. Risks and how to reduce them

| # | Risk | How likely | What we do |
|---|---|---|---|
| 1 | **Persian text shaping:** Unity's normal text doesn't join Persian letters | Certain without help, but the impact is small (your son sees no text, only the parent caption and parent corner do) | RTLTMPro + Vazirmatn, tested in phase 0. Unity 6's newer UI Toolkit text may handle Persian itself, but we don't depend on it. |
| 2 | **The mic on iOS:** Unity switches the iPhone's sound mode while recording. Sound can drop to the quiet earpiece speaker, and there is no built-in echo removal. | Likely to need fixing | Turn on the Unity settings "Prepare iOS for Recording" and "Force iOS Speakers when Recording", keep the web rule "ignore the mic while Googoo talks", and make the early iOS talk-back test build (phase 2). Plan B: a small native iOS mic add-on. |
| 3 | **The mic on Android:** phones differ in loudness and noise | Medium | A sensitivity knob (`MIC_FLOOR`, as on the web) in the parent corner; test on 2–3 phones. Ask for mic permission only after the "Wake up" tap, with a parent-friendly message. |
| 4 | **App size** | Low | Estimate 80–120 MB (Unity itself about 30 MB, clips about 25–30 MB, models about 10 MB). Store limits are 200 MB+. 64-bit ARM only, mono voice clips, compressed textures. |
| 5 | **Slow on cheap Android phones** | Medium | The budgets in gpu-budget.md, the mobile settings already in Unity (`GoogooPerf.cs`), only Googoo and big furniture cast shadows, baked room lighting, 30 fps when idle, and a test on an old phone in phase 4. |
| 6 | **Kids Category / Families rules.** Unity adds its own data collection by default. | Medium | Turn off Unity Analytics, Cloud Diagnostics and "hardware statistics"; no ads and no Unity online services; check that the app sends nothing (watch its network traffic); real parent gate; privacy policy; mic explained in the review notes; `name.mp3` never in the store build. |
| 7 | **Licences** (from decisions.md) | Known | ElevenLabs speech clips are OK on the paid plan. Check whether `eleven_v4` was marked beta when the clips were made, and keep the invoices. The Setareh voice has a 365-day notice period, so generate everything needed and keep the files. **`song_bed.mp3` (Eleven Music) is not confirmed for a paid app:** replace it with a track made on the paid Suno plan. Free Suno songs are for personal use only. Folk chants stay our own chanted recordings. Also check whether the first Tripo pilot props were made on the free (public) plan; if so, remake them as Private or credit the source. Unity Personal is free under US$200k a year; Mixamo, RTLTMPro and Noto Emoji are free for commercial use. |
| 8 | **Two games drifting apart** while both are worked on | High if the web keeps growing | Web feature freeze now (section 4). |
| 9 | **Losing Unity work** (no git today), agents blocking each other in the editor | High until fixed | Git in phase 0 (large files kept out); one agent owns the scenes; builds go one at a time. |

---

## 6. Decisions for you (one recommended option each)

1. **Unity version:** **A) 6.3 LTS, a fresh project with the prototype copied in (recommended)** · B) stay on 6000.6 and add Android to it.
2. **First thing your son tests:** **A) Android build of the home room with taps, dance, voice and talk-back after 1–2 weeks (recommended)** · B) wait until the whole house is done.
3. **Test phone:** **A) your own Android phone now, plus an older borrowed or cheap one (about US$100) for the speed test in phase 4 (recommended)** · B) only your own phone.
4. **Web Design mode and `layout.json`:** **A) import it into Unity once, then design in the Unity Editor (recommended)** · B) keep `layout.json` as a shared live file for both engines · C) don't carry it over.
5. **Web version:** **A) no new web features from now; finish the in-progress work and fix bugs; full freeze at M4 (recommended)** · B) keep adding features to both until Unity matches · C) freeze everything today.
6. **When to start iOS:** **A) a small talk-back test on iOS during phase 2, which means buying the Apple account then (recommended)** · B) iOS only after Android matches the web.
7. **How iOS gets built:** **A) export the Xcode project on this PC and build it on Codemagic, free tier (recommended)** · B) Unity Build Automation (simpler, paid per minute).
8. **Picture cards:** **A) free Noto Emoji pictures now, swapped for your own pictures later if you want (recommended)** · B) make your own pictures before Unity has cards.
9. **Unity Claude plugin:** **A) install it and test it for one hour in phase 0 (recommended)** · B) skip it; agents use batch mode only.
10. **Stats from the web game:** **A) start fresh in the app; the web stats stay on the web (recommended)** · B) build a transfer (not worth it for one child).
11. **Purchases (decide at phase 6):** **A) Unity IAP: no extra company sees the purchase data, which is enough for one lifetime unlock (recommended)** · B) RevenueCat for Unity (easier dashboards; one more outside service to declare).

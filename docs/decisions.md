# Pash: decisions log

Pash is a Farsi-learning virtual pet for my 3-year-old son, with a possible future as an App Store and Google Play product.
Newest decisions are at the bottom of each section.

## Product
- **Name: Googoo Robo; the robot is "Googoo" for short** (2026-10-21). Existing voice lines and stories still say پاش; keep them for now and only add new lines for new words. A full rewrite and re-record comes later with the vocabulary overhaul.
- **Two copies:** `Pash/` (branch `main`) is the live game he plays: https://kitchennetweb-a11y.github.io/Pash/ . `Pash-dev/` (branch `dev`, a git worktree) is where new work happens; it's published to the test site https://kitchennetweb-a11y.github.io/GoogooRobo-dev/ (repo `GoogooRobo-dev`, remote `devsite`). Merge `dev` into `main` only when the user approves.
- **Fun first, learning hidden inside play.** About 70% silly and reactive, 30% structured learning. Wrong answers are never punished: Pash names what was tapped, then asks again.
- **The character is a robot, not a Persian cat.** My son loves robots, and a rigid robot can be built well in code without an art or rigging pipeline. The original plan (Persian cat, Meshy/Tripo, Blender, rigging) was dropped.
- **Talking-Tom-style talk-back is core.** Pash listens hands-free (voice detection) whenever he's idle and repeats the child's words in a squeaky voice. Talking wakes him when he's asleep. The Talk button is now only a mic on/off switch for parents.
- **Say it praises any attempt.** There's no pronunciation grading for a toddler: any detected speech counts.
- **The child can't read.** Buttons must have no text: big round icon buttons on the left and right edges of the screen (requested 2026-10-08, not built yet).
- **Three rooms plus a dedicated Say it screen**, switched with buttons at the bottom of the screen: home, play room and bedroom (requested 2026-10-08, not built yet).
- **Sing (🎵, home) uses traditional folk rhymes only, never modern songs** (2026-10-08): Setareh chants them rhythmically (`song_*` in lines_existing_v2.csv) twice over an instrumental bed made with Eleven Music (`audio/song_bed.mp3`). Eleven Music's sung Persian wasn't good enough; Traditional/folk songs stay as rhythmic chants for good (Suno flags اتل متل as copyrighted). Sung songs will be new original lyrics made in Suno, in a separate session.
- **Vocabulary grows by 200 words** with emoji picture cards. The list is in `vocab/words.py` and `vocab/words.json`.
- **Parent corner** sits behind a press-and-hold (2 seconds) on the gear icon. Stats are stored on the device in localStorage.

- **Business model (2026-10-21): free 7-day trial, then US$59 lifetime unlock.** Sold via App Store / Google Play (Capacitor wrap, Android first); the web version stays a free demo (GitHub Pages forbids selling). Trial = in-app 7-day timer started by a free trial item (store-native trials are subscription-only). Claude's note: $59 is high for kids apps (typ. $5-20); consider an early-family launch price. Full plan: docs/monetization-plan.md.
- **Engine upgrade (three.js r128 → current) comes after the phone layout is approved.** The user will specify their own phone layout; the agent-built one is only a first draft.

## Voice
- **ElevenLabs Persian voice.** Use one voice ID for everything, with no filters or effects; the user found effects worse. The first 21 clips had a robot effect baked in from the ElevenLabs website, so they are being re-recorded clean.
- **Clips must not end early.** Trim only the leading silence, keep the natural ending, then pad about 0.35 s of silence at the end. Browsers drop about 50 ms from the end of short MP3s, which caused cut-off words.
- **Loudness is matched across all clips** (about -9 LUFS after light compression; see `tools/process_robo_clips.py`). Robo-set clips get a 1.12× playback boost in code (`g.gain.value` in `playVoice`).
- **11 Robo source clips are truncated at the source** and must be regenerated: ab_mikham, nan_mikham, shir_khordam, ser_shodam, gorosnam, ghelghelaki, in_chi_bood, dobare, dahan, akh, boo_mide.
- **Clips are generated on the user's PC.** This cloud workspace can't reach api.elevenlabs.io (blocked by the network allowlist), so generation runs via Claude Code on the PC using `vocab/PROMPT_for_Claude_Code.md` and `vocab/pash_voice_lines.csv` (892 lines). The API key stays in a local environment variable and is never pasted into chat.
- **`name.mp3` is the personal greeting with my son's name.** Keep it; don't regenerate it.
- **v2 voice (2026-10-08): ElevenLabs `eleven_v4`, voice "Setareh" (`8Ebkg5uUcbSbeqGucAoR`), with English emotion tags** in the text ([excited], [whispers], [yawns], ...). Lines are in `vocab/lines_existing_v2.csv` (Pash's lines + 57 longer `p_` phrases) and `vocab/lines_words_v2.csv` (200 reviewed words, `vocab/words_v2.json`). Bubble text comes from the CSV `display_text` via `audio/manifest.json`.
- **Pitch +2 semitones, formants shifted ("up2 cute")**, applied in `tools/process_robo_clips.py`. This is the one effect the user approved after listening.
- **Generation is budgeted:** 15,000 characters were used first; remaining words wait for a top-up (see `vocab/voice_status.md`).

- **Licence check (2026-10-21):** speech clips are OK for a paid app with conditions: the account is paid (payg), you own the output, no attribution, and Setareh is an ElevenLabs-generated Library voice with a 365-day notice period (clips already made stay valid; generate everything needed and keep the files). Eleven v4 appears to be a production model (re-check the Beta addendum). **Music (`music_v1`, only `song_bed.mp3`) is unconfirmed for paid apps**: decided: replace it later with a backing track made on the paid Suno plan. Keep invoices as proof.

## Tech
- **Platform: web for now (three.js r128 from cdnjs).** One page; the hosted build is `index.html` on GitHub Pages: https://kitchennetweb-a11y.github.io/Pash/ (capital P). A Claude artifact copy also exists, but the microphone is blocked there, so GitHub Pages is the real version.
- **Native or App Store packaging is deferred.** Likely path: wrap the web app with Capacitor, or move to native later. Decide in a separate brainstorming session.
- **Audio is currently base64-embedded in the HTML**, which is about 1.1 MB. With 890+ clips this must change to separate `audio/<key>.mp3` files loaded on demand, plus a manifest. This was in progress when the session moved.
- **Visuals:** a realistic playroom (walls, window, oak floor, woven rug, ACES tone mapping, PMREM reflections) and a lamp that switches between day and night.
- **Layout must work on iPad (landscape and portrait) and phones.**

## Git and hosting
- Repo: `kitchennetweb-a11y/Pash` (`main` branch). GitHub Pages serves `main` from `/` (root).
- Commits are authored as `Claude <noreply@anthropic.com>`.

## Navigation (2026-10-21)
- Phone layout: left rail = this room's actions, right rail = the four learning games (same in every room), small mic + star counter top left (away from the bottom so frustrated taps miss it), gear alone top right, room tabs along the bottom.
- Later: house rooms stay as tabs; outside places (courtyard, street, shop, park, farm) are reached by a map tab/button plus doors in the scene, and unlock with stars. Not built yet.

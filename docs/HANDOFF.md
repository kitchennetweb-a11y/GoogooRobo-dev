# Pash handoff (moving from a cloud session to Claude Code)

## What Pash is
A 3D robot virtual pet that teaches a 3-year-old Farsi through play. My son played with it for hours on day one. Live: https://kitchennetweb-a11y.github.io/Pash/

## Repo layout
| Path | What |
|---|---|
| `index.html` | Hosted build that GitHub Pages serves. It's `src_pash-robot.html` wrapped in a doctype/head (see Build), with all audio embedded as base64. |
| `src_pash-robot.html` | Source page, written as an artifact fragment: no `<html>`/`<head>`, starts with `<title>` and `<style>`. Edit this one. |
| `audio/*.mp3` | The 104 processed voice clips currently in use (same as what's embedded). Key = file name. |
| `vocab/words.py`, `vocab/words.json` | The 200 new words: id, Farsi, transliteration, English, emoji picture, category, kind (n = noun, a = action/feeling). |
| `vocab/pash_voice_lines.csv` | All 892 lines to generate with ElevenLabs: existing lines re-recorded clean, plus w_/where_/this_/say_ lines for the new words. |
| `vocab/PROMPT_for_Claude_Code.md` | Prompt for generating the clips with the ElevenLabs API on the PC. |
| `tools/process_robo_clips.py` | Audio pipeline: trim leading silence, compress, level-match, pad the tail. Needs ffmpeg and numpy; paths inside need updating. |
| `tools/test_*_playwright.py` | Headless browser tests used during development. They expect a local copy of three.js; adjust paths. |
| `docs/decisions.md` | Product, voice and tech decisions. Read it first. |

### Build (how index.html is made)
`index.html` = `<!doctype html><html lang="en"><head>` + the meta tags (charset, viewport with viewport-fit=cover, apple-mobile-web-app-capable, apple-mobile-web-app-title "Pash", theme-color) + `</head><body>` + the contents of `src_pash-robot.html` + `</body></html>`.
Audio is currently embedded: `const VOICE_B64={key: base64mp3,...}` in the source. Rebuild it from `audio/` with a small Python script (base64-encode each mp3, keyed by file name).

## How the code is organised (inside src_pash-robot.html)
- **Sound:** `SFX` (synthesised), `music()`, `hush()` (pauses the mic while Pash makes sounds).
- **Voice:** `VOICE_B64`, `VOICE` (decoded buffers), `playVoice(k)` (with the gain boost for Robo keys), `LINES` (key → [Farsi, transliteration (English)]), `VARIANTS` + `pickVar` (random alternative lines), `say(k)` (bubble + voice + stats), `sayAsync(k)`, `fallbackFor(k)` (where_/this_/say_ → word clip if missing).
- **Scene:** three.js r128, robot built from primitives (`rbox`), face drawn on a canvas texture (`drawFace`, faces: happy, laugh, shock, dizzy, sleep, hidden, listen), particles (`emit`).
- **Room:** walls, window, floor and rug textures, lighting; `setLights(on)` switches day/night; `ROOM_DAY` / `ROOM_NIGHT`.
- **Furniture:** `furnGroup`, `tapFurniture` (lamp, bed, chair, table, book).
- **Behaviour:** `st.mode` (idle, dance, sleep, chase, eat, peek, fly, listen, game), `poke(part)`, springs, idle routines.
- **Games:** `WORDS`, `BODY`, `FURN`, `MAKE` (3D toys and food), `playFind`, `playFeed`, `playSay`, `playMoves`, `answer()`, `ask()`, `endGame()`.
- **Talk-back:** `talk` object, `micOn`, `onMic` (voice activity detection), `finishClip`, `playBack` (pitch 1.65).
- **Parent corner:** `stats` in localStorage key `pash-stats-v1`; `statAdd`, `renderParent`; opened by holding the gear for 1.8 s.
- **UI:** `#bar` (text+icon buttons along the bottom; being replaced), `onBtn()`, `#start` overlay, `#micHelp`, `#parent`.

## Status
Done and live: everything listed in decisions.md under Product, apart from the items marked "not built yet".

### Done on 2026-10-08 (Claude Code on the PC)
- Audio split out: `audio/<key>.mp3` + `audio/manifest.json` (key → bubble text), loaded on demand (`HAS`, `loadVoice`, `loadCore`). Build with `python tools/build.py` (writes manifest + index.html).
- v2 voices: Eleven v4, voice Setareh, emotion tags, +2 semitone pitch. `tools/gen_voices.py` (resumable, `--budget=N`), `tools/process_robo_clips.py`. Status in `vocab/voice_status.md`.
- Icon-only round buttons (left/right columns, `SCREENS`), rooms home/play/bed with bottom nav (`setRoom`, `showScreen`, `WALL`, furniture `add(id,g,x,z,ry,room)`), Say it screen (`sayRound`, `SAY_WORDS`).
- v2 phrases wired as `VARIANTS` and `ROOM_HI` (room greetings).

- Vocabulary games (2026-10-08): card Find (🔍, every 3rd press the old 3D Find), colour hunt (🎨), counting (🔢), animal sounds (🐮), picture book + 4 stories (📖 screen), parent progress summary. Shared helpers: `showDeck`, `cardAsk`, `hear`, `sayIf`. Content: `vocab/lines_games_v2.csv`, `vocab/stories.json`, `col` field in `words_v2.json`.

- Phone-first draft (2026-10-21, dev only): portrait puts the room tabs and the screen's action buttons in rows at the bottom (`resize()` sizes them); landscape keeps side columns. Perf: DPR cap 1.5 phones / 2 else, lighter or no shadows on phones, face canvas redrawn only on change, render + audio pause when hidden, `loadCore` preloads only reaction clips. PWA: `manifest.webmanifest`, `sw.js` (versioned caches written by build.py; network-first for page/data, cache-first for audio), `icons/`. The user wants a different phone layout; this is a first draft.

### Next
1. (done: all 200 words generated)
2. Phone portrait: bed and toy shelf are mostly off-screen; iPad portrait bedroom: mic button overlaps the bed.
3. Colour hunt skips pink/purple/black (fewer than 2 tagged words); tag more words to enable them. Unused phrases: food (p_nam_nam..., p_ah_ino...), say-it prompts (p_hala_to_begu, p_chi_gofti_nashenidam), goodbye, countdown.

### Known gotchas
- Mic and volume on iOS: echo cancellation/AGC are off, because they put iOS in "voice chat" mode, which ducks all app sound. `audioSession('play-and-record')` is used only while the mic is on, `'playback'` otherwise. The mic is ignored while Pash's voice or the song bed plays (`voiceEnd`, `bedSrc`). Sensitivity knob: `MIC_FLOOR`.
- iPad and Safari need one tap before audio or the mic will start (the "Wake up" button does both).
- The mic only works over https on GitHub Pages; it's blocked inside the Claude artifact viewer.
- Clip timings: `sayAsync` waits for the decoded duration plus 250 ms. Padded clips make games slightly slower; that's acceptable.
- Large single HTML files load slowly on iPad, which is another reason to split the audio out.
- Stray `[hidden]` CSS: the page sets `[hidden]{display:none!important}` itself, because the hosted build has no artifact skeleton reset.

## Connectors (Claude Code MCP, set up for your whole PC)

Check status any time: open a terminal and type `claude mcp list`.

| Connector | Status |
|---|---|
| Playwright (browser control) | Working. Nothing to do. |
| GitHub | Added, needs a step (1 below). |
| ElevenLabs (voice/audio) | Added, needs `uv` installed (2 below). Your API key is already on the PC; it is not stored in any config file. |
| Blender | Blender 5.2 is installed. Added, needs `uv` (2) plus the addon (3). |
| Penpot | Added, only works while Penpot's MCP is running (4). |

Steps for you:
1. GitHub: GitHub's server does not support automatic sign-in from Claude Code. Create a Personal Access Token at github.com/settings/tokens, then run:
   `claude mcp remove github --scope user` then
   `claude mcp add --scope user --transport http github https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer YOUR_TOKEN"`
   (The `gh` command line tool is already signed in and keeps working without this.)
2. Install uv (one line, in PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` then restart Claude Code.
3. Blender: download the addon file `addon.py` from github.com/ahujasid/blender-mcp. In Blender: Edit > Preferences > Add-ons > Install from Disk, pick the file, tick it on. In the 3D view press N, open the "BlenderMCP" tab, click "Connect to Claude".
4. Penpot: in a terminal run `npx -y @penpot/mcp@latest` and leave it open. In Penpot, load the plugin from `http://localhost:4400/manifest.json`, open it and click "Connect to MCP server". Penpot desktop app is not installed (it is a web app); use design.penpot.app or your own instance.
5. Restart Claude Code, then run `claude mcp list` to confirm.

**Status 2026-10-21 (after setup):** uv installed (winget), Unity Hub installed (winget). Connected: Playwright, Blender: official Blender Lab extension installed from the Claude app (follow its add-on instructions at lab.blender.org); the community `uvx blender-mcp` was removed, ElevenLabs (`uvx --python 3.12 elevenlabs-mcp`, key from the user env var). GitHub MCP skipped by decision (the `gh` CLI already has access). Penpot: set up when layout design starts. New connectors appear in new sessions.
- **Pending:** add Unity's official Claude Code plugin (Anthropic Directory, "Unity", 0.1.2-beta, 31 skills) after the Unity editor is installed; then check whether it can drive the Unity editor (would let Claude test the Unity prototype itself).

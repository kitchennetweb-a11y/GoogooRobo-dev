# Design mode: arrange the rooms yourself

Design mode lets you move the furniture and toys, change the walls and the room colours, and rearrange the round buttons, on your PC, inside the real game.

## Start
1. Double-click **`tools\design_mode.bat`** (in the Pash-dev folder). A black window opens and the editor opens in your browser.
2. Keep the black window open while you work. Close it when you are done.
3. After Design mode has been updated, close the black window and double-click the file again, so the new version runs. If it says "Design mode is already running", use the browser tab that is already open (or close the other black window first).

The editor has a list on the left, the game in the middle and the settings on the right.

## What you can do
- **Pick a room:** Living room / Play room / Bedroom at the top.
- **Pick a screen size:** the box at the top (iPhone upright, iPhone sideways, small phone, iPad). The game in the middle changes size to match.
- **Look around:** "Free camera" lets you turn around the room with the mouse (drag, wheel to zoom). "Game camera" goes back to what your son sees.
- **Props tab:**
  - Click a piece in the picture to select it (a blue box shows around it).
  - Drag it to move it on the floor. Hold **Shift** and drag to move it up or down.
  - Mouse wheel or **+ / -** = bigger / smaller. **R** = turn it (Shift+R turns the other way). Arrow keys = small nudges. **Delete** = remove it.
  - The right side shows the same as numbers you can type: **height as a % of Googoo's height** (100 = as tall as Googoo; rugs show their length), turn, lift, left/right, back/front, "against a wall", and "casts a shadow" (only for big furniture: each shadow makes phones slower).
  - **Sits on:** pick another piece and this one stands on its top, even when you move or resize the other one (the bedside lamp sits on the nightstand).
  - **Upright phones only:** tick it to give a piece a different place, size or turn on upright phones (other screens keep theirs). "Use the same place as on other screens" removes that.
  - **Copy position / Paste position:** copies where a piece is, so you can paste it in the other view or onto another piece.
  - The list on the left shows every piece once: first the ones in this room (click to select, ⧉ to add another one, 👁 to hide or show, 🗑 to remove), then "Add to this room" with ➕. Search and the filter chips (All, Furniture, Toys, Decor, In this room, Hidden) narrow it. Pieces that stand in for a built-in piece of the room (bed, lamp, window...) are hidden instead of removed. The book and the star mobile can be moved too (not resized). The ball can't be moved: it only appears when he plays ball.
- **Googoo:** click him (or "Googoo" at the top of the list) to move, turn and resize him for this room, like a prop (tick "Upright phones only" for a different place on upright phones). The camera follows him, so he still fills the screen; after playing ball he walks back to this place.
- **Walls & floor tab:** click the back, left or right wall in the picture and drag it in or out to make the room smaller or bigger (or type the numbers). Moving a wall never moves the floor. Click the floor and drag near one of its edges to make it bigger or smaller (or type its four edges). Pieces standing against a wall move with it. Wall colour and floor colour are on the right.
- **Buttons tab:** drag a round button up or down to change the order, or across to the other side. Click a button to change its colour. On the right: what you are editing (each screen has its own side buttons; the **top bar** and the **room tabs** at the bottom are the same everywhere), size and shape, ✕ to take a button off a screen, "Add a button", and for the top bar and the tabs a tick box to show or hide each one. The gear (parent corner) and the three room tabs always stay. Changing a button size never moves the camera.
- **Camera tab:** zoom, height, turn and tilt for this room. There is one view for upright phones and one for everything else (sideways phones, iPads): change the screen size at the top to set the other one. "Save this view" keeps it, "Back to automatic" lets the camera fit Googoo by itself again. With the free camera on you can also turn the room with the mouse and press "Use the free camera's angle". Card games and stories always keep their automatic framing.
- **Speed meter (bottom right):** draw calls, triangles and texture memory for the room on screen. Green = fine, orange = getting heavy, red = too much for phones.

## Undo
**Undo / Redo** at the top, or **Ctrl+Z / Ctrl+Y**. It remembers every change since you opened the editor. **Reset room** puts the room you are in back to how it was at the last Save.

## Save vs Publish
- **Save** (or **Ctrl+S**) keeps your changes on this PC only (`data\layout.json`). If you close the browser with unsaved changes it warns you.
- **Publish to test site** saves, then puts the layout on the **test site** (https://kitchennetweb-a11y.github.io/GoogooRobo-dev/, ready in about a minute). It shows what happened; if something goes wrong it shows the message and changes nothing else.
- **The live game only changes when you approve a merge.** Publishing never touches it.

## Backups
Every Save keeps the previous layout as `data\layout.backup-<date-time>.json` (the last 20). To go back to one, ask Claude to restore it (or copy it over `data\layout.json`).

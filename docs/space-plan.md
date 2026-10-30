# Space trip (owner's decisions, 2026-10-29)

## The game
- **Getting there:** tap the toy rocket on the bedroom shelf, or (later) the rocket on the outside map. The screen flashes, then the **countdown**: Googoo counts ۵، ۴، ۳، ۲، ۱ (5 to 1) in Farsi and says "boro!" (go!).
- **Flying:** Googoo flies like Iron Man, with **blue rocket flames from his boots and hands** (not the ear propellers).
- **At each planet:** he hovers next to it and says the name **in English, then in Farsi**, then its colour **in Farsi only** (one main colour per planet). The planet's colour stays on screen: his face screen fills with it, and the colour word shows under it.
- **Next:** a big rocket button flies him to the next planet. During the 3–4 second whoosh, stars stream past. Ryan taps them (**catch the stars**) and Googoo counts them in Farsi.
- **Order:** all 10 stops in the real order, plus a "fly home" button back to the bedroom.

| Stop | English | Farsi | Colour (Farsi) |
|---|---|---|---|
| 1 | Sun | خورشید khorshid | زرد zard (yellow) |
| 2 | Mercury | عطارد otârod | طوسی tusi (grey) |
| 3 | Venus | زهره zohre | نارنجی nâranji (orange) |
| 4 | Earth | زمین zamin | آبی âbi (blue) |
| 5 | Moon | ماه mâh | سفید sefid (white) |
| 6 | Mars | مریخ merrikh | قرمز ghermez (red) |
| 7 | Jupiter | مشتری moshtari | قهوه‌ای ghahve'i (brown) |
| 8 | Saturn | زحل zohal | زرد zard (yellow) |
| 9 | Uranus | اورانوس urânus | آبی روشن âbi-ye roshan (light blue) |
| 10 | Neptune | نپتون neptun | آبی âbi (blue) |

- **Voice:** English names are spoken in Googoo's own ElevenLabs voice (option A). If that sounds wrong, we switch to a separate English voice (option B).
- **Look (mix):** a painted space backdrop (upright and sideways); the planets are painted pictures that float and turn slowly; the starfield, the glow around each planet, Googoo and the flames are 3D.
- **Later:** a quiz with the existing card game ("where's the red planet?").

## Pictures to make (ChatGPT / Gemini)

### 1. Space backdrop: two pictures (upright 9:16 and wide 16:9)
Attach `assets/rooms/bed_portrait.webp` (or any finished room) as the style reference and say "Match the style of this picture:". Then paste:

> Soft rounded premium 3D animated-film style children's game background, toy-like world, gentle depth. Deep outer space seen from a spaceship window, no window frame. Tall portrait image, 9:16. A rich deep navy-to-indigo sky with soft purple and teal nebula clouds drifting at the edges, a few soft glowing distant stars, a faint sparkle of the Milky Way across the top. NO planets, NO moon, NO sun, NO rockets, NO characters, NO text. Keep the centre of the picture calm and darker so things can float in front of it. Colours mid-tone and rich: NOT neon, NOT pastel.

Then, in the same chat: "Now make the exact same space as a wide 16:9 landscape picture, keep everything the same, no planets, calm centre."

### 2. Planet sheet: one 3x3 sheet plus one single picture
Attach `Sister.png` (or one of the word sheets) as the style reference, so the planets match the word pictures.

> Match the style of the attached picture. A 3x3 grid of nine separate pictures on a plain white background, evenly spaced, nothing touching the edges of its square, no text, no numbers, no labels. Each one is a cute, simple, rounded toy-like planet for a children's learning game, soft 3D look, no faces. In this order, left to right, top to bottom:
> 1. the Sun: a glowing warm yellow ball with soft orange flames around its edge
> 2. Mercury: a small grey rocky planet with a few round craters
> 3. Venus: a soft orange-yellow planet with swirly creamy clouds
> 4. Earth: blue oceans with green continents and a few white clouds
> 5. the Moon: a pale white-grey moon with soft round craters
> 6. Mars: a red-orange rocky planet with a few craters and a small white ice cap
> 7. Jupiter: a big brown, tan and cream striped planet with a red oval spot
> 8. Saturn: a pale golden-yellow planet with wide tilted rings
> 9. Uranus: a smooth light blue-teal planet with thin faint rings, standing on its side

Then a single picture in the same chat: "Now one more picture in the exact same style, on its own on a white background: Neptune, a deep blue planet with soft darker blue swirls and one dark spot."

Put the three pictures (space upright, space wide, planet sheet) and Neptune into `Downloads\GooGoo Robo background\space\`.

- **Launch rocket:** `models/space_rocket.glb` (rebuilt cleanly in Blender to the Tripo rocket's proportions: `tools/rocket_blender.py`). In the game it stands a little shorter than Googoo (about 3.6 units to his 4).
- **Bedroom launch (built 2026-10-29):** tap the toy rocket on the bedroom shelf. The rocket grows on the rug, Googoo jets into its window, counts down ۵..۱ (clips cd_5..cd_1, cd_go), and it blasts off (assets/sounds/launch.mp3, ElevenLabs paid). Until the space scene exists, a white flash brings him back down (cd_back). Code: launchRocket / launchTick / launchEnd in src.
- **Space trip (built 2026-10-29, mock-up on the test site):** after the launch flash the bedroom painting swaps to the space painting (assets/rooms/space_*.webp, same sizes), room buttons hide, Googoo hovers on his jets. Planets from Planets V2 (owner pick; assets/space/*.webp; Neptune = Tripo A until the ChatGPT one is compared). Each stop: the planet slides in with a glow, his face shows it, a chip shows the Farsi colour, he says pl_<id> ("Mars! مریخ! قرمزه!", his own voice: owner picked option A in the end). Rocket button = next planet: stars stream past, tap = he counts (cd_1..5, cnt_6..10). House button = flash, back in the bedroom, cd_back. Code: spaceOn/spaceOff/spArrive/spWhoosh/spaceTick/spaceTrip.
- **2026-10-29 update:** lines are now split: pn_<id> (English + Farsi name), a short pause, sp_whatcol ("چه رنگیه؟"); planet names say "کره‌ی" joined to the Farsi name (not the Sun and the Moon) ("Mars! کره‌ی مریخ!", koreh-ye merrikh), a longer pause for Ryan, then col_<colour> (plain word: قرمز، آبی…, said excitedly: eleven_v4 with "[happily] [excited]" tags, which it does not read aloud); the colour chip appears with the colour. Between planets Googoo flies flat (head first to the right, arms open, rolling a little; jets follow his body). After Neptune the rocket button opens the solar system on black (planets orbit the sun, the Moon orbits the Earth; tap a planet = its line; sp_all = "همه‌ی سیاره‌ها! به یکی دست بزن!"). Taps on Googoo are ignored during the trip.

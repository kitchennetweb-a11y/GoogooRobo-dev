# Googoo Robo: game plan

Written 2026-10-21. This is a plan, not code. Nothing here is built yet unless it says "today".
Next step after you approve it: the full Tripo prop list (one line per prop, with its prompt).

## 1. Pitch and core loop

**Pitch.** Googoo is a big, friendly robot who lives in a house and loves going out. Your child plays with him the way kids play with Talking Tom: poke him, feed him, dress him, make him dance, talk to him and hear him squeak it back. Every touch is a Farsi word. Googoo's world is any child's world (home, park, shops, farm, beach, school), with Persian touches where they feel natural: a courtyard with a حوض, a korsi in winter, نون from the bakery, a fruit shop, Nowruz. There is no text for the child, no losing, no timers and no ads. Parents get a quiet corner that shows what their child is learning.

**Core loop.**

| Step | What happens |
|---|---|
| 1. Play with Googoo | Touch, feed, dress, talk. He reacts and says the word. |
| 2. Games teach words | Short games (Find, Feed, Colour, Count, Animals, Say it, stories) in each place. |
| 3. Earn stars | Every right answer and every finished game gives a star. Stars never go down. |
| 4. Unlock | Star totals open new places on the map; new words give stickers. |
| 5. New words | Each new place brings 10-20 new words and 2-3 new games. Back to step 1. |

## 2. The world

**How you move.** The house is home base. Its five rooms are tabs at the bottom. A picture map button (next to the tabs) shows the outside places; later, doors in the scene (front door → courtyard) do the same. Outside, the child taps the ground and Googoo walks there. No joystick. Locked places show on the map as a grey picture with a padlock and a star pile; tapping one makes Googoo say "soon!" (no numbers for the child).

**Words.** Most words already exist in `vocab/words_v2.json` (200 words) plus the 20 starter words in the code (ball, apple, bread, milk, head, hand...). "New" below means not in the vocab yet. Every new word needs voice lines (word, "where is", "this is", "say it").

### Inside the house (always open, no stars needed)

| Room | What it is | What the child does with Googoo | Word groups | New words needed | Props |
|---|---|---|---|---|---|
| **Living room** (home, today) | Sofa, carpet, TV, window. Winter: a korsi. | Feed (today), dance, sing, lamp on/off (today); Find the thing; "where is the window?"; korsi in winter: Googoo hides under it | home, people, colours, shapes | sofa مبل, carpet فرش, korsi کرسی, picture/photo عکس | 10 |
| **Play room** (today) | Toys everywhere | Ball, bubbles, disco, peek (today); toy box: tap a toy, Googoo plays with it; Colour hunt and Count with toys; music toys (drum, piano) | home (toys), colours, numbers, shapes | blocks مکعب, teddy (have خرس) | 7 |
| **Bedroom** (today) | Bed, lamp, wardrobe | Sleep, lamp, star counting, night story (today); **wardrobe = dress-up**; pick pyjamas, tuck in | clothes, feelings, nature (moon, star) | pillow بالش, blanket پتو, wardrobe کمد, pyjamas لباس خواب | 4 |
| **Kitchen** (new) | Fridge, stove, table, samovar, fruit bowl | Feed moves here (drag food to his mouth); open the fridge and Find; "make" soup or a salad by adding 2-3 things (count them); tea time with the samovar | food, numbers, colours, home (spoon, fork, plate, cup) | fridge یخچال, pot قابلمه, bowl کاسه, pomegranate انار, dates خرما, آش (Persian soup) | 10 + food pool |
| **Bathroom** (new) | Bath, sink, mirror, potty | Bath time: tap to scrub, bubbles pop; brush teeth (body words: teeth, tongue); "wash your hands / face / feet"; rubber duck; potty (like Tom's toilet button, kept silly) | body, home (bath, soap, toothbrush, potty), actions | towel حوله, mirror آینه, bubbles حباب, hair مو, toothpaste خمیردندون, wash بشور | 6 |

### Outside places (on the map, unlock with stars)

| # | Place | What it is | What the child does with Googoo | Word groups | New words needed | Stars (total reached) | Props |
|---|---|---|---|---|---|---|---|
| 1 | **Courtyard** حیاط | Persian courtyard: a حوض pool with goldfish, pomegranate tree, flower pots, a takht | Feed the goldfish (count them); splash in the pool (Googoo gets wet, shakes); pick pomegranates; Find (cat, bird, butterfly, flower); weather: rain → umbrella (uses the rain story) | nature, animals (small), colours, numbers | hoz حوض, goldfish ماهی قرمز, fountain فواره, pomegranate انار | 15 | 7 |
| 2 | **Street** کوچه | Our street: front doors, lamp post, cars passing | Vehicles drive by: "which one is the bus?"; traffic light: red stop, green go (colours); vehicle sounds game (like animal sounds); wave bye-bye to the taxi | vehicles, colours, actions | street خیابون, traffic light چراغ راهنما, stop/go وایسا / برو | 40 | 6 |
| 3 | **Bakery and fruit shop** نونوایی، میوه‌فروشی | Two little shops side by side | Shopkeeper asks for 2-3 things, child puts them in Googoo's basket (Find + Count); watch نون come out of the oven (warm, smells good, Googoo eats it); fruit colours | food, numbers, colours, people | bakery نونوایی, fruit shop میوه‌فروشی, baker نونوا, basket سبد, money پول, give بده | 75 | 6 + food pool |
| 4 | **Park** پارک | Slide, swing, sandbox, duck pond | Push Googoo on the swing (count the pushes); slide down; feed the ducks; kick the ball; picnic (uses the park story); hide and seek behind trees | nature, actions, animals, numbers | swing تاب, sand شن, bench نیمکت, jump بپر, picnic پیک‌نیک | 120 | 7 |
| 5 | **Farm** مزرعه | Barn, fence, tractor, animals | Animal sounds game moves here; collect eggs (count); milk time; ride the tractor; feed each animal its food (carrot to the rabbit); uses the farm story | animals (farm), food, vehicles, numbers | barn طویله, farmer کشاورز, donkey الاغ, fence نرده | 175 | 8 |
| 6 | **School** مدرسه (reading and writing classroom) | Blackboard, little desks, teacher | Letter of the day (sound + 3 pictures on Googoo's face); trace the letter right to left with a finger; letter hunt (reuses Find); shapes and colours on the board; sticker book letters page | letters, shapes, colours, people | teacher معلم, blackboard تخته, letter حرف, paint رنگ | 240 (parent can open it early) | 6 |
| 7 | **Beach** ساحل / دریا | Sand, sea, sun, boats | Build a sandcastle (stack 3-5 pieces, count); find shells and crabs; sun hat and glasses (dress-up + hot); boat and ship go by; swim | nature, vehicles (boat, ship), clothes, feelings (hot) | sand شن, crab خرچنگ, sandcastle قلعه شنی, spade بیل | 320 | 6 |
| 8 | **Zoo** باغ‌وحش | Big animals behind low fences | Animal sounds (wild); "who is tallest?" (giraffe) and big/small; feed the elephant; copy the animal moves (reuses Moves) | animals (wild), actions, numbers | lion شیر (same word as milk: fun to teach!), bear خرس, crocodile تمساح, big بزرگ, small کوچیک | 420 | 7 |

**Persian flavour without making it only Persian.** The courtyard, korsi, samovar, نون bakery and Haft-sin are the Persian touches. The park, farm, beach, zoo, school and shops look like anywhere. Seasonal extras (Nowruz Haft-sin, Yalda watermelon and pomegranate, snow) are dressings on existing places, not new places.

**Honest flag:** 5 rooms + 8 places = 13 scenes. That is a lot for one person. Each place needs props, a floor you can walk on, 10-20 new voice clips per word set, and testing on phones. See the build phases: the store version should ship with fewer places, and the rest come as free updates.

## 3. Progression

**Stars.**
- One star per right answer (today's counter) and a bonus star when a game ends. Saying a word in Say it counts as right (any attempt counts).
- Stars are a **total that only grows**. Unlocking a place does not spend stars. Nothing can be lost.
- Rough pace: a 10-15 minute session gives about 15-25 stars, so a new place opens every 2-4 sessions at first and every week or so later.

**Sticker book.**
- One page per place (and one for letters). Each word the child gets right for the first time adds its sticker (the word's picture) to that place's page. Tapping a sticker says the word.
- A full page gives Googoo a small treat: a new hat, a dance, a colour for his face screen. No new currency.
- Letters page: each letter traced in the school adds a letter sticker.

**Map unlocks.** The map is one picture of the neighbourhood, house in the middle. When the star total passes a place's number, Googoo runs to the map, the padlock pops, confetti, and he says the place's name. The first visit to a new place has a short "hello" tour (Googoo walks to 3 things and names them).

**Daily routine (matches real life).**

| Time of day (device clock) | Googoo's gentle hint (a picture on his face) | Where it leads |
|---|---|---|
| Morning | Yawns, stretches, sun picture | Bathroom: wash face, brush teeth; then kitchen: breakfast (نون، پنیر، چایی) |
| Day | Ball or tree picture | Play room or an outside place |
| Evening | Food picture | Kitchen: dinner; then bath |
| Night | Moon picture, sleepy face | Bedroom: pyjamas, story, lamp off, sleep |

Hints are only suggestions. The child can ignore them and nothing bad happens. Googoo is never sick, sad or dirty for long, and nothing changes while the app is closed (no "Googoo missed you" guilt).

**A 10-15 minute session.**

| Minutes | What happens |
|---|---|
| 0-1 | Googoo wakes up, greets the child, shows his routine hint. |
| 1-4 | Free play: poke, talk-back, feed, dress. |
| 4-10 | 2-3 short games in the room or place the child picked (each game about 1-2 minutes, 5-6 questions). |
| 10-12 | A new sticker or an unlock, if one is due. A story or a song. |
| 12-15 | If the parent set a time limit, Googoo gets sleepy, asks for a bedtime story and falls asleep. The child can wake him, but he yawns again after a minute. |

**Rules that keep it gentle:** no fail states (a wrong tap = Googoo names what was tapped and asks again), no timers inside games, no streaks or daily rewards, no lives, no red crosses, no sad sounds for wrong answers.

## 4. Googoo's interactions (work in every place)

| Interaction | How | Words it teaches |
|---|---|---|
| **Touch** | Poke a body part: he reacts and says it (today). Tickle belly = laugh. Long press = hug. | body, actions (hug, laugh, kiss) |
| **Talk-back** | He listens and squeaks back the child's words (today). Never paywalled. | anything the child says |
| **Feed** | Drag food from a small tray to his mouth. He likes some foods, makes a funny face at lemon. In the kitchen and on picnics, but a snack works anywhere. | food, feelings |
| **Dress-up** | Bedroom wardrobe has all the clothes words. Outside, the weather asks for something: rain → umbrella and boots, beach → hat and glasses, snow → scarf, gloves, jacket. Clothes stay on as he moves around. | clothes, nature (weather), colours ("the red hat") |
| **React** | His face shows feelings (happy, sad, scared, sleepy, angry, sick, hot, cold) and says the word. A "how is Googoo?" card game uses them. | feelings |
| **Sleep** | Lamp off or long quiet = he dozes; talking wakes him (today). | night-night, moon, star |
| **Dance and sing** | Music button and songs (today); copy-the-move game. | actions, numbers (count the claps) |
| **Picture face** | Every word he says shows as a picture on his face (today). Parents can switch on Farsi captions. | all |

## 5. Parent side

**Parent corner** (behind a real adult gate, for example "tap the number seven" written as a word, or a short sum; the 2-second gear hold is not enough for the stores).

| Section | What it shows or does |
|---|---|
| Progress | Words heard, found and said, by category and by place. A short list of "new this week". The sticker book in parent view (with Farsi words). |
| Settings | Show words (Farsi captions, today), mic on/off, voice volume, play time limit (off / 10 / 15 / 20 / 30 min), follow the real clock for the routine (on/off), open the school early. |
| Gentle screen time | The time limit ends with Googoo falling asleep, not a "time's up" screen. There is no reminder or notification to come back. |
| About and purchase | Privacy policy, restore purchase, the unlock (store app only). |
| Reset | Clear progress (with a confirm). |

**Privacy for kids (design rule).**
- No accounts, no login, no names typed. The child's name voice clip is for your family copy only.
- Progress lives on the device only.
- The mic sound is handled live on the device and never saved or sent.
- No ads, no analytics, no crash reporting, no third-party requests (fonts and libraries are bundled).
- The only thing that may leave the device is the store purchase check (RevenueCat). Anything else needs a new privacy review first (see monetization-plan.md, risk 5).
- Paid app: no in-app purchases aimed at the child. Locked places say "ask Mommy or Daddy" and nothing more; any purchase screen is behind the adult gate.

## 6. Prop budget (Tripo)

Rule from `tripo-objects.md`: build in 3D only what the child touches or what makes the place recognisable. Everything else stays a picture on cards and on Googoo's face. Reuse props across places (fruit, ball, animals, trees).

| Group | Must-have | Nice-to-have | Total | Build batch |
|---|---|---|---|---|
| Living room | 7 | 3 | 10 | 1 |
| Play room | 6 | 1 | 7 | 1 |
| Bedroom | 3 | 1 | 4 | 1 |
| Food pool (Feed, kitchen, shops, picnic) | 10 | 4 | 14 | 2 |
| Kitchen | 7 | 3 | 10 | 2 |
| Bathroom | 5 | 1 | 6 | 2 |
| Dress-up clothes (worn by Googoo) | 6 | 2 | 8 | 2 |
| Courtyard | 5 | 2 | 7 | 3 |
| Street | 4 | 2 | 6 | 3 |
| Bakery and fruit shop | 4 | 2 | 6 | 3 |
| Park | 5 | 2 | 7 | 3 |
| Farm | 6 | 2 | 8 | 4 |
| School | 5 | 1 | 6 | 4 |
| Beach | 4 | 2 | 6 | 5 |
| Zoo | 5 | 2 | 7 | 5 |
| **Total** | **82** | **30** | **112** | |

**Build order:** batch 1 = the existing house rooms (21, replaces today's primitive furniture) → batch 2 = kitchen, bathroom, food, clothes (38) → batch 3 = the first four outside places (26) → batch 4 = farm and school (14) → batch 5 = beach and zoo (13).

**Honest flags:** 112 props at a few tries each is weeks of Tripo work and probably 2-3 months of the paid plan. Keeping one style across 112 models is the hardest part: make a style sheet and test 5 props before batch 1. Animals (farm, zoo, ducks, goldfish) are the hardest props; if Tripo struggles, keep them simple or use CC0 packs that match. Phones need each place loaded on its own (not the whole world at once).

## 7. Build phases

| Phase | What it delivers | Notes |
|---|---|---|
| **0. Today** | 3 house rooms, talk-back, Find, Feed, Say it, Colour, Count, Animals, stories, songs, sleep, lamp, star counter, parent corner, phone layout. | Live and on the test site. |
| **1. New look** | Engine decided (Unity or web); the Tripo Googoo with his face kit; batch 1 props in the 3 rooms; star total saved; first sticker book (house pages). | The engine decision is the blocker. Everything else waits on it. |
| **2. Full house** | Kitchen and bathroom tabs; batch 2 props; Feed by dragging; bath and teeth games; dress-up wardrobe; daily routine hints; new voice lines for the new words. | First version that feels like a whole home. |
| **3. Map and first places** | Map button, star unlocks, tap-to-walk; courtyard, street, shops, park (batch 3); front door in the scene. | The biggest technical step: walking, loading places one at a time. |
| **4. School and farm** | Reading and writing classroom (letter of the day, tracing, letter hunt, letters stickers); farm; parent corner v2 (adult gate, progress by place, time limit). | Tracing right to left needs careful testing with your son. |
| **5. Store release** | Voice rewrite and re-record (Googoo, not پاش); privacy policy; bundled files; no `name.mp3`; Android closed test (12 testers, 14 days); purchase (trial then lifetime unlock); iOS after Android. | Ship with house + 5 outside places + school. |
| **6. Free updates** | Beach, zoo, Nowruz and Yalda dressings, new stories and songs. | Gives parents a reason to trust the one-time price. |

**Honest overall flag:** phases 1-5 are several months of part-time work, with the most time in props, voice lines and phone testing, not code. The plan is still worth it because every phase is playable on its own; your son can test each one.

## 8. Open questions (multiple choice)

**Q1. Order of the outside places?**
- A. Courtyard, street, shops, park, farm, school, beach, zoo (the order in HANDOFF, close to home first). **Recommended**
- B. Park first (most fun), then courtyard, farm, shops, street...
- C. Vehicles first (street), because many kids love cars.

**Q2. How do stars unlock places?**
- A. Star total reached; stars are never spent. **Recommended** (nothing can be lost)
- B. Spend stars to open a place (feels like buying; the counter goes down).
- C. Star total, plus a parent switch to open any place early.

**Q3. Should the daily routine follow the real clock?**
- A. Yes, by default, with a parent switch to turn it off. **Recommended**
- B. No; Googoo cycles morning to night inside each session.
- C. No routine at all.

**Q4. Does Googoo have needs (hungry, sleepy, dirty)?**
- A. Only as gentle hints on his face that go away on their own. **Recommended**
- B. Real needs that grow over time (like Tamagotchi).
- C. No needs at all.

**Q5. What ships in the store version?**
- A. House (5 rooms) + courtyard, street, shops, park, farm + school; beach and zoo later as free updates. **Recommended**
- B. Everything (13 scenes) before launch.
- C. House only, then outside places as updates.

**Q6. When does the school (reading and writing) open?**
- A. By stars, and the parent can open it early. **Recommended**
- B. Always open from day one.
- C. Only when the parent turns it on (for children 4 and up).

**Q7. Eighth place: is the zoo right?**
- A. Zoo (uses the 15 wild animal words we already have). **Recommended**
- B. Doctor's clinic (body and feelings words, helps with real doctor visits).
- C. Grandma's house (family words, a second Persian home).
- D. Only 7 places; skip it.

**Q8. Price for the store version?** (decisions.md says US$59 lifetime; monetization-plan.md suggests US$9.99 then US$14.99.)
- A. 7-day free trial, then US$14.99 lifetime, with an early-family price of US$9.99. **Recommended**
- B. 7-day trial, then US$59 lifetime (as decided).
- C. 7-day trial, then US$29.99 lifetime.
- D. Free house, paid outside places (one unlock), no trial.

## Owner's answers (2026-10-21)
| Question | Decision |
|---|---|
| Star unlocks | Total reached, never spent. **Lower thresholds plus simple achievements, so kids see everything sooner.** New star targets: courtyard 5, street 15, shops 30, park 50, farm 75, school 100, beach 130, moon 160 (tune after testing). Achievements = simple firsts ("fed Googoo", "first story", "10 words") that give stars and stickers. |
| Routine | Follows the real clock, with a parent switch. |
| Googoo's needs | **None.** No hunger, dirt or sleep meters; routine hints are suggestions only. |
| First outside place | Courtyard حیاط. |
| Store v1 | House (5 rooms) + courtyard, street, shops, park, farm + school. Beach and the 8th place come later as free updates. |
| School | Opens with stars; a parent can open it early. |
| 8th place | **The moon, reached by rocket** (replaces the zoo and the clinic): rocket launch from the park or courtyard, moon walk, stars and planets, space words (ماه، ستاره، موشک، فضانورد). |
| Price | 7-day trial, then **US$14.99 lifetime** (US$9.99 early-family price). Replaces US$59. |

**Art direction (2026-10-21):** the team leans towards Unity with slightly nicer 3D; the whole world (rooms, sky, floors, lighting), not just the props, gets upgraded to match Googoo's new style.

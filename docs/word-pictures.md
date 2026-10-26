# Word pictures (replace the emojis)

Every word in the game shows an emoji today (cards, Googoo's face screen, book covers). A drawn picture replaces that emoji everywhere as soon as it's added. Words without a picture keep their emoji, so this can go one sheet at a time.

Done: sister (`assets/pics/sister.webp`).

## How to make them (ChatGPT or Gemini)

1. New image chat. Attach `Sister.png` as the style reference.
2. Paste the style prompt below, then one sheet line (9 things in a 3x3 grid).
3. Save the sheet into `DownloadsGooGoo Robo backgroundpictures` named `sheet-01.png`, `sheet-02.png`... Claude cuts it with `py -3.10 tools/cut_sheet.py <sheet> 01` (white background removed, 512px WebP in assets/pics, emoji added to PICART), then builds.
   (Single pictures are fine too: name them after the word, e.g. `brother.png`.)

Check before sending: one thing per square, nothing touching another square, no writing or numbers in the picture (except the number sheet), nothing cut off at the edges.

## Style prompt

> Match the style of the attached picture exactly: soft rounded premium 3D cartoon illustration for a toddler's learning game, warm friendly, clean simple shapes, gentle soft shading, mid-tone rich colours (NOT pastel, NOT neon). Make a 3x3 grid sheet of 9 separate pictures on a plain pure white background, each picture centred in its own square with plenty of white space around it, nothing touching, no borders, no shadows on the background, no text, no letters, no labels. Each picture is a single clear object or character, seen from the front, easy for a 3-year-old to recognise. The 9 pictures, left to right, top to bottom:

## Sheets

**Sheet 01:** ball ⚽, apple 🍎, banana 🍌, teddy bear 🧸, car 🚗, bread 🍞, milk 🥛, water 💧, head 👦

**Sheet 02:** hand ✋, tummy 😋, foot 🦶, eyes 👁️, ear 👂, mouth 👄, lamp 💡, book 📖, bed 🛏️

**Sheet 03:** table 🍽️, chair 🪑, cat 🐱, dog 🐶, horse 🐴, cow 🐮, sheep 🐑, goat 🐐, chicken 🐔

**Sheet 04:** rooster 🐓, chick 🐥, duck 🦆, rabbit 🐰, mouse 🐭, fish 🐟, bird 🐦, parrot 🦜, tiger 🐯

**Sheet 05:** elephant 🐘, monkey 🐒, giraffe 🦒, zebra 🦓, penguin 🐧, turtle 🐢, frog 🐸, snake 🐍, butterfly 🦋

**Sheet 06:** bee 🐝, ant 🐜, ladybug 🐞, octopus 🐙, whale 🐋, dolphin 🐬, camel 🐫, owl 🦉, squirrel 🐿️

**Sheet 07:** orange 🍊, grapes 🍇, watermelon 🍉, melon 🍈, strawberry 🍓, cherries 🍒, peach 🍑, pear 🍐

**Sheet 08:** pineapple 🍍, lemon 🍋, carrot 🥕, tomato 🍅, cucumber 🥒, potato 🥔, corn 🌽, egg 🥚, cheese 🧀

**Sheet 09:** rice 🍚, pasta 🍝, pizza 🍕, cake 🍰, ice cream 🍦, chocolate 🍫, candy 🍬, cookie 🍪, honey 🍯

**Sheet 10:** juice 🧃, tea 🍵, soup 🍲, sandwich 🥪, mushroom 🍄, kiwi 🥝, popcorn 🍿, teeth 🦷, tongue 👅

**Sheet 11:** finger ☝️, face 🙂, nose 👃, arm 💪, shoes 👟, socks 🧦, hat 🧢, pants 👖, shirt 👕

**Sheet 12:** boots 🥾, jacket 🧥, glasses 👓, gloves 🧤, scarf 🧣, bag 🎒, umbrella ☂️, slippers 🩴, watch ⌚

**Sheet 13:** door 🚪, window 🪟, TV 📺, phone 📱, key 🔑, bath 🛁, potty 🚽, soap 🧼, toothbrush 🪥

**Sheet 14:** bucket 🪣, spoon 🥄, fork 🍴, plate 🍽️, cup 🥤, broom 🧹, candle 🕯️, present 🎁, balloon 🎈

**Sheet 15:** doll 🪆, scissors ✂️, pencil ✏️, slide 🛝, puzzle 🧩, drum 🥁, guitar 🎸, piano 🎹, kite 🪁

**Sheet 16:** robot 🤖, bus 🚌, train 🚂, airplane ✈️, ship 🚢, boat ⛵, bike 🚲, motorbike 🏍️, truck 🚚

**Sheet 17:** tractor 🚜, ambulance 🚑, fire truck 🚒, police car 🚓, helicopter 🚁, rocket 🚀, taxi 🚕, sun ☀️, moon 🌙

**Sheet 18:** star ⭐, cloud ☁️, rain 🌧️, snow ❄️, rainbow 🌈, tree 🌳, flower 🌸, leaf 🍃, fire 🔥

**Sheet 19:** sea 🌊, mountain ⛰️, rock 🪨, shell 🐚, red 🔴, blue 🔵, green 🟢, yellow 🟡, orange (colour) 🟠

**Sheet 20:** purple 🟣, black ⚫, white ⚪, pink 🩷, brown 🟤, one 1️⃣, two 2️⃣, three 3️⃣, four 4️⃣

**Sheet 21:** five 5️⃣, six 6️⃣, seven 7️⃣, eight 8️⃣, nine 9️⃣, ten 🔟, circle ⭕, square 🔲, triangle 🔺

**Sheet 22:** heart ❤️, mommy 👩, daddy 👨, grandma 👵, grandpa 👴, brother 👦, baby 👶, doctor 🧑‍⚕️, police officer 👮

**Sheet 23:** firefighter 🧑‍🚒, happy 😀, sad 😢, angry 😠, scared 😨, sleepy 😴, tired 😩, sick 🤒, hot 🥵

**Sheet 24:** cold 🥶, run 🏃, swim 🏊, sing 🎤, hug 🤗, kiss 😘, bye-bye 👋, laugh 😂, cry 😭

**Sheet 25:** clap 👏, dance 💃, night-night 🛌

Notes:
- People (mommy, daddy, grandma, grandpa, brother, baby, doctor...) should look like the same family as the sister picture: a friendly Persian family.
- Feelings and actions (happy, sad, run, hug...): a child like the sister picture doing it, head and shoulders or full body.
- Colours: a simple round paint blob of that colour. Numbers: the digit as a chunky toy number (the only sheet with writing on it).

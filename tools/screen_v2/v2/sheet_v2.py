import os
from PIL import Image, ImageDraw, ImageFont
D = r"C:\Users\ahmma\Downloads\Pash 3D\screen_preview"
rows = [("current", "CURRENT\n(old sheet)"), ("new", "NEW v2\n(cut-in LCD)")]
cols = [("front", "Front"), ("34", "3/4"), ("side", "Side 90°"), ("corner", "Corner zoom ~4x"), ("edge", "Top-edge zoom ~4x")]
C, LW, HH, G = 460, 210, 70, 8
f = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 28); fs = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)
sh = Image.new("RGB", (LW + len(cols) * (C + G), HH + len(rows) * (C + G) + 40), (246, 244, 240)); d = ImageDraw.Draw(sh)
for ci, (_, t) in enumerate(cols): d.text((LW + ci * (C + G) + 10, 20), t, fill=(30, 40, 60), font=f)
for ri, (k, t) in enumerate(rows):
    y = HH + ri * (C + G)
    d.multiline_text((16, y + C // 2 - 36), t, fill=(30, 40, 60), font=f, spacing=6)
    for ci, (v, _) in enumerate(cols):
        sh.paste(Image.open(os.path.join(D, f"v2cmp_{k}_{v}.png")).convert("RGB").resize((C, C), Image.LANCZOS), (LW + ci * (C + G), y))
d.text((16, sh.height - 32), "Googoo screen preview v2 - EEVEE, standard view, rest pose, same lights as compare.png. Same camera per column. Full-res 1600px v2cmp_*.png alongside.", fill=(90, 90, 100), font=fs)
sh.save(os.path.join(D, "compare_v2.png")); print(sh.size)

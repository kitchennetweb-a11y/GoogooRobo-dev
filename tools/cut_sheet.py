"""Cut a 3x3 word-picture sheet (docs/word-pictures.md) into game pictures.

  py -3.10 tools/cut_sheet.py "C:/Users/ahmma/Downloads/GooGoo Robo background/pictures/sheet-01.png" 01
  py -3.10 tools/cut_sheet.py ".../brother.png" brother      (a single picture: its word id)

Each square: the white background around it becomes transparent (flood fill from the edges, so white
inside the picture stays), trimmed, centred on a 512x512 square -> assets/pics/<word>.webp, and its emoji is
added to PICART in src_pash-robot.html. Then run tools/build.py.
"""
import json, re, sys, pathlib
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src_pash-robot.html"


def words():
    s = SRC.read_text(encoding="utf-8")
    return {w[0]: w for w in json.loads(re.search(r"const SAY_WORDS=(\[.*?\]\]);", s).group(1))}


def sheet_ids(n):
    W = words(); en = {w[3]: k for k, w in W.items()}
    line = re.search(rf"^\*\*Sheet {int(n):02d}:\*\* (.+)$", (ROOT / "docs/word-pictures.md").read_text(encoding="utf-8"), re.M).group(1)
    return [en[p.rsplit(" ", 1)[0]] for p in line.split(", ")]


def cutout(im, tol=232):
    """white background (touching the edges) -> transparent; returns the trimmed RGBA picture or None if empty"""
    im = im.convert("RGBA")
    if im.getextrema()[3][0] < 250:  # already has transparency
        a = im.getchannel("A")
    else:
        m = Image.eval(im.convert("RGB").split()[0], lambda v: 0).copy()
        px, r = m.load(), im.load()
        for y in range(im.height):
            for x in range(im.width):
                if min(r[x, y][:3]) >= tol: px[x, y] = 255
        for x, y in [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)] + [(x, 0) for x in range(0, im.width, 16)] + [(x, im.height - 1) for x in range(0, im.width, 16)] + [(0, y) for y in range(0, im.height, 16)] + [(im.width - 1, y) for y in range(0, im.height, 16)]:
            if px[x, y] == 255: ImageDraw.floodfill(m, (x, y), 128)
        a = m.point(lambda v: 0 if v == 128 else 255).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1))
    im.putalpha(a)
    box = a.point(lambda v: 255 if v > 24 else 0).getbbox()
    return im.crop(box) if box else None


def save(pic, wid, size=512, pad=.06):
    s = int(max(pic.size) * (1 + 2 * pad)); c = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    c.paste(pic, ((s - pic.width) // 2, (s - pic.height) // 2)); c = c.resize((size, size), Image.LANCZOS)
    out = ROOT / "assets/pics" / f"{wid}.webp"; out.parent.mkdir(exist_ok=True); c.save(out, "WEBP", quality=85, method=6); return out


def add_picart(pairs):
    s = SRC.read_text(encoding="utf-8"); m = re.search(r"const PICART=\{(.*?)\}", s)
    cur = dict(re.findall(r"'([^']+)':'([^']+)'", m.group(1))); cur.update(pairs)
    s = s[:m.start(1)] + ",".join(f"'{e}':'{n}'" for e, n in cur.items()) + s[m.end(1):]
    SRC.write_text(s, encoding="utf-8", newline="")


def main(path, what):
    W = words(); im = Image.open(path)
    if what in W: cells = [(what, im)]
    else:
        ids = sheet_ids(what); w, h = im.width / 3, im.height / 3
        cells = [(ids[i], im.crop((round(i % 3 * w), round(i // 3 * h), round((i % 3 + 1) * w), round((i // 3 + 1) * h)))) for i in range(len(ids))]
    pairs = {}
    for wid, cell in cells:
        pic = cutout(cell)
        if not pic: print("EMPTY", wid); continue
        print(wid, save(pic, wid).name, pic.size); pairs[W[wid][4]] = wid
    add_picart(pairs)


if __name__ == "__main__":
    if len(sys.argv) == 3: main(*sys.argv[1:])
    else:  # self-check: a white square with a red disc (white inside it) cuts to the disc, inside kept
        t = Image.new("RGB", (100, 100), "white"); d = ImageDraw.Draw(t); d.ellipse((20, 20, 80, 80), fill="red"); d.ellipse((45, 45, 55, 55), fill="white")
        p = cutout(t); assert abs(p.width - 61) <= 3 and p.getpixel((p.width // 2, p.height // 2))[3] == 255 and p.getpixel((0, 0))[3] < 40, (p.size, p.getpixel((0, 0)))
        assert sheet_ids(1)[0] == "ball" and len(sheet_ids(25)) >= 1; print("ok")

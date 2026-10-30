# Build: audio/manifest.json (from audio/*.mp3 + vocab CSVs) and index.html (from src_pash-robot.html).
# Run from anywhere: python tools/build.py
import csv, glob, hashlib, json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-title" content="Googoo Robo"><meta name="theme-color" content="#bfe3f2">'
        '<link rel="manifest" href="manifest.webmanifest"><link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">'
        '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png"></head><body>\n')

# bubble text per key, from any CSV that has display_text (the v2 line files)
text = {}
for f in glob.glob(os.path.join(ROOT, 'vocab', '*.csv')):
    for r in csv.DictReader(open(f, encoding='utf-8-sig')):
        if r.get('display_text'):
            tr = r.get('translit', '')
            text[r['file_name'][:-4]] = [r['display_text'], f"{tr} ({r['english']})" if tr else r['english']]

keys = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, 'audio', '*.mp3')))
json.dump({k: text.get(k) for k in keys}, open(os.path.join(ROOT, 'audio', 'manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))

src = open(os.path.join(ROOT, 'src_pash-robot.html'), encoding='utf-8').read()
page = HEAD + src + '\n</body></html>\n'
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8', newline='').write(page)

# sw.js cache versions: shell = hash of the page + manifest/stories, audio = hash of clip names and contents
# (a changed sw.js makes browsers install it, which drops the old caches)
h = lambda s: hashlib.sha1(s.encode()).hexdigest()[:10]
shell_v = h(page + json.dumps(keys) + open(os.path.join(ROOT, 'vocab', 'stories.json'), encoding='utf-8').read())
audio_v = hashlib.sha1(b''.join(k.encode() + open(os.path.join(ROOT, 'audio', k + '.mp3'), 'rb').read() for k in keys)).hexdigest()[:10]  # contents: a re-made clip can have the same size
swp = os.path.join(ROOT, 'sw.js')
sw = re.sub(r"const SHELL_V='[^']*',AUDIO_V='[^']*'", f"const SHELL_V='{shell_v}',AUDIO_V='{audio_v}'", open(swp, encoding='utf-8').read())
open(swp, 'w', encoding='utf-8', newline='').write(sw)
print(f'manifest: {len(keys)} clips ({sum(k in text for k in keys)} with v2 text); index.html: {len(src) // 1024} KB')

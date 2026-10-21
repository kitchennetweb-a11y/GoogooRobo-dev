# Build: audio/manifest.json (from audio/*.mp3 + vocab CSVs) and index.html (from src_pash-robot.html).
# Run from anywhere: python tools/build.py
import csv, glob, json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-title" content="Googoo Robo"><meta name="theme-color" content="#bfe3f2"></head><body>\n')

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
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8', newline='').write(HEAD + src + '\n</body></html>\n')
print(f'manifest: {len(keys)} clips ({sum(k in text for k in keys)} with v2 text); index.html: {len(src) // 1024} KB')

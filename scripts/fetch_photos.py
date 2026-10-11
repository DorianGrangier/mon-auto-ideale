"""Télécharge et optimise les photos indiquées dans la feuille (colonnes « Photo » et « Crédit photo »).
Usage : python3 scripts/fetch_photos.py <photos_src.json>
Écrit assets/photos/<modèle>.webp et data/photos.json. Une photo introuvable ne bloque jamais la publication."""
import json, os, sys, io, re, unicodedata, urllib.request
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = json.load(open(sys.argv[1], encoding='utf-8'))
# Images insérées directement dans les cellules de la feuille : adresses relevées par Claude via le connecteur Google Sheets
cells_p = os.path.join(ROOT, 'data', 'photos_cells.json')
if os.path.exists(cells_p):
    for k, v in json.load(open(cells_p, encoding='utf-8')).items():
        src.setdefault(k, v)
state_p = os.path.join(ROOT, 'data', 'photos.json')
state = json.load(open(state_p, encoding='utf-8')) if os.path.exists(state_p) else {}
outdir = os.path.join(ROOT, 'assets', 'photos'); os.makedirs(outdir, exist_ok=True)
def slug(s):
    s = unicodedata.normalize('NFD', s); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', s.lower()))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
ok, fail, kept = [], [], 0
for k, v in src.items():
    f = slug(k.replace('|', ' ')) + '.webp'; path = os.path.join(outdir, f)
    old = state.get(k)
    if old and old.get('url') == v['url'] and os.path.exists(path):
        old['credit'] = v['credit']; kept += 1; continue
    try:
        req = urllib.request.Request(v['url'], headers={'User-Agent': UA, 'Accept': 'image/*,*/*'})
        data = urllib.request.urlopen(req, timeout=40).read()
        im = Image.open(io.BytesIO(data)); im.load()
        if im.mode not in ('RGB', 'RGBA'): im = im.convert('RGBA' if 'A' in im.getbands() else 'RGB')
        if im.width > 960: im = im.resize((960, round(im.height * 960 / im.width)), Image.LANCZOS)
        im.save(path, 'WEBP', quality=78, method=6)
        state[k] = {'url': v['url'], 'f': f, 'credit': v['credit'], 'w': im.width, 'h': im.height}
        ok.append(k)
    except Exception as e:
        fail.append(f'{k} : {type(e).__name__} {str(e)[:120]}')
for k in [k for k in state if k not in src]:
    p = os.path.join(outdir, state[k]['f'])
    if os.path.exists(p): os.remove(p)
    del state[k]
json.dump(state, open(state_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
rep = [f'## Photos', f'- {len(state)} modèles avec photo ({len(ok)} nouvelles, {kept} inchangées)'] + [f'- ⚠️ Échec : {x}' for x in fail]
print('\n'.join(rep))
if os.environ.get('GITHUB_STEP_SUMMARY'): open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8').write('\n'.join(rep) + '\n')

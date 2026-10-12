"""Copie autonome du comparateur pour l'aperçu Claude (artifact) : CSS en ligne, polices Google Fonts,
liens vers les fiches et pages ouverts sur le site en ligne. Usage : python3 tools/artifact.py dist/index.html sortie.html"""
import re, sys, os
BASE = 'https://doriangrangier.github.io/mon-auto-ideale/'
src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
css = open(src.rsplit('/', 1)[0] + '/assets/site.css', encoding='utf-8').read()
css = re.sub(r"@font-face\{[^}]*\}\n?", '', css)
fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@100..900&family=Unbounded:wght@200..900&display=swap">'
h = re.sub(r'<link rel="preload"[^>]*>\n?', '', h)
h = h.replace('<link rel="stylesheet" href="assets/site.css">', fonts + '\n<style>\n' + css + '\n</style>')
own = os.path.basename(src)
def _link(m):
    href = m.group(1)
    if href == own: return 'href="#"'
    return f'href="{BASE}{href}" target="_blank" rel="noopener"'
h = re.sub(r'href="((?:index|comparateur|marques|methode|mentions-legales)\.html(?:#[^"]*)?)"', _link, h)
h = re.sub(r'href="(modeles/[a-z0-9-]+\.html)"', _link, h)
h = h.replace("const ficheUrl = c=> 'modeles/'", f"const ficheUrl = c=> '{BASE}modeles/'")
h = h.replace('<a class="fiche-link" href="${ficheUrl(c)}">', '<a class="fiche-link" href="${ficheUrl(c)}" target="_blank" rel="noopener">')
# Photos : intégrées dans la page (data URI) si le dossier assets/photos est à côté, sinon chargées depuis le site
import os, base64, json as _j
pdir = os.path.join(src.rsplit('/', 1)[0], 'assets', 'photos')
m = re.search(r'<script type="application/json" id="photos-data">(.*?)</script>', h, re.S)
if m and os.path.isdir(pdir):
    ph = _j.loads(m.group(1).replace('<\\/', '</'))
    for k, v in ph.items():
        fp = os.path.join(pdir, v['f'])
        if os.path.exists(fp): v['f'] = 'data:image/webp;base64,' + base64.b64encode(open(fp, 'rb').read()).decode()
    h = h[:m.start(1)] + _j.dumps(ph, ensure_ascii=False) + h[m.end(1):]
    h = h.replace("const PHOTO_BASE = 'assets/photos/';", "const PHOTO_BASE = '';")
else:
    h = h.replace("const PHOTO_BASE = 'assets/photos/';", f"const PHOTO_BASE = '{BASE}assets/photos/';")
assert 'assets/site.css' not in h
open(out, 'w', encoding='utf-8').write(h)
print('ok', len(h) // 1024, 'Ko')

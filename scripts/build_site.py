"""Génère le site statique « Mioto » dans dist/.

Usage : python3 scripts/build_site.py [dossier_sortie]
Entrées : data/data.json (versions), data/avis.json (avis par modèle), data/meta.json (pays, drapeaux,
sites constructeurs, liste des modèles éligibles aux aides, silhouettes), src/index.body.html, assets/.
Variable d'environnement SITE_URL (ex. https://mioto-auto.fr/) pour les liens absolus.
"""
import json, math, os, re, shutil, sys, unicodedata, html, datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist')
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/') + '/' if os.environ.get('SITE_URL') else ''

def load(p): return json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
CARS = load('data/data.json'); AVIS = load('data/avis.json'); META = load('data/meta.json')
# Pages modèles sur les sites constructeurs : colonne « Lien constructeur » de la feuille en priorité, sinon data/liens.json
LIENS = load('data/liens.json') if os.path.exists(os.path.join(ROOT, 'data/liens.json')) else {}
for _c in CARS:
    if _c.get('u'): LIENS[_c['b'] + '|' + _c['m']] = _c['u']
PH = load('data/photos.json') if os.path.exists(os.path.join(ROOT, 'data/photos.json')) else {}

# --- Malus 2026 (estimation) : malus CO2 + malus au poids, plafonnés ensemble à 80 000 € ----------------------------
# Barème CO2 2026 (L'argus, 1er janvier 2026) : 50 € à 108 g/km … 80 000 € dès 192 g/km.
MALUS_CO2 = [50, 75, 100, 125, 150, 170, 190, 210, 230, 240, 260, 280, 310, 330, 360, 400, 450, 540, 650, 740, 818, 898, 983,
             1074, 1172, 1276, 1386, 1504, 1629, 1761, 1901, 2049, 2205, 2370, 2544, 2726, 2918, 3119, 3331, 3552, 3784, 4026,
             4279, 4543, 4818, 5105, 5404, 5715, 6126, 6637, 7248, 7959, 8770, 9681, 10692, 11803, 13014, 14325, 15736, 17247,
             18858, 20569, 22380, 24291, 26302, 28413, 30624, 32935, 35346, 37857, 40468, 43179, 45990, 48901, 51912, 55023,
             58134, 61245, 64356, 67467, 70578, 73689, 76800, 79911]   # 108 à 191 g/km
def malus_co2(g):
    if g is None or g < 108: return 0
    return 80000 if g >= 192 else MALUS_CO2[int(g) - 108]
def malus_poids(c):
    """Malus au poids 2026 : seuil 1 500 kg, 10 à 30 €/kg par tranche. Électriques et hydrogène exonérés ;
    abattement de 200 kg (plafonné à 15 % de la masse) pour les hybrides rechargeables de plus de 50 km d'autonomie,
    100 kg pour les autres hybrides et les micro-hybrides (barème du Journal de l'Automobile, 1er juillet 2026)."""
    w, e = c.get('w'), c['e']
    if w is None or e in ('ev', 'h2'): return 0
    if e == 'phev': ab = min(200, .15 * w) if (c.get('aut') or 0) > 50 else 100
    else: ab = 100 if e in ('hev', 'essm', 'diem') else 0
    m = w - ab; t = 0
    for lo, hi, r in ((1500, 1700, 10), (1700, 1800, 15), (1800, 1900, 20), (1900, 2000, 25), (2000, 10**6, 30)):
        if m > lo: t += (min(m, hi) - lo) * r
    return round(t)
for _c in CARS:
    _ml = min(80000, malus_co2(_c.get('co2')) + malus_poids(_c))
    if _ml: _c['ml'] = _ml
NATION, ADJ, SITE, ENERGY, TR, SILS = META['NATION'], META['ADJ'], META['SITE'], META['ENERGY'], META['TR'], META['SILS']
FLAGS = META['FLAG_SVG']; SCORE_ENV = set(META['SCORE_ENV'])
TODAY = datetime.date.today()

def slug(s):
    s = unicodedata.normalize('NFD', s); s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', s.lower()))
def esc(s): return html.escape(str(s), quote=True)
NB = ' '
def fmt(n, d=0):
    if n is None: return '—'
    s = f'{n:,.{d}f}'.replace(',', ' ').replace('.', ',').replace(' ', NB)
    return s
def eur(n): return '—' if n is None else fmt(n) + NB + '€'
def flag(b, cls='flag'):
    inner = FLAGS.get(NATION.get(b, ''), '')
    if not inner: return ''
    n = esc(NATION.get(b, ''))
    return f'<svg class="{cls}" viewBox="0 0 30 20" role="img" aria-label="{n}"><title>{n}</title>{inner}<rect x=".25" y=".25" width="29.5" height="19.5" fill="none" stroke="rgba(0,0,0,.3)" stroke-width=".8"/></svg>'
def eligible(c): return c['e'] == 'ev' and ((c['b'] + '|' + c['m']) in SCORE_ENV or (c['b'] + '|' + c['m'] + '|' + c['v']) in SCORE_ENV) and c.get('p') and c['p'] <= 47000 and c.get('w') and c['w'] < 2400
def tags(c): return [ {'Roadster': 'Cabriolet', 'Limousine': 'Berline'}.get(t, t) for t in c['c'].split(', ')]
def photo(b, m): return PH.get(f'{b}|{m}')
def pic(c, p, cls='ph'):
    ph = photo(c['b'], c['m'])
    return f'<img class="{cls}" src="{p}assets/photos/{ph["f"]}" alt="{esc(c["b"])} {esc(c["m"])}" loading="lazy" decoding="async" width="{ph.get("w", 960)}" height="{ph.get("h", 540)}">' if ph else sil(c)
def sil(c):
    t = tags(c); k = next((x for x in t if x in SILS), 'Berline'); return SILS[k]

# --- regroupement par modèle -------------------------------------------------
MODELS = {}
for c in CARS:
    MODELS.setdefault((c['b'], c['m']), []).append(c)
for k in MODELS: MODELS[k].sort(key=lambda c: (c.get('p') or 10**9, c.get('hp') or 0))
def mslug(b, m): return slug(b + ' ' + m)
def avis_for(b, m):
    out = []
    base, ev = AVIS.get(f'{b}|{m}'), AVIS.get(f'{b}|{m}|ev')
    if ev and base: out = [('Versions thermiques et hybrides', base), ('Version électrique', ev)]
    elif base: out = [('', base)]
    elif ev: out = [('', ev)]
    return out
def pmin(l): ps = [c['p'] for c in l if c.get('p')]; return min(ps) if ps else None

# --- gabarits communs ----------------------------------------------------------
# Logo : les deux « o » sont des phares escamotables (fichiers sources dans assets/logo/).
LOGO_SVG = open(os.path.join(ROOT, 'assets', 'logo', 'mioto-blanc.svg'), encoding='utf-8').read().strip().replace(
    '<svg xmlns="http://www.w3.org/2000/svg" ', '<svg class="logo-svg" width="101" height="30" aria-hidden="true" focusable="false" ')
import hashlib
CSS_V = hashlib.md5(open(os.path.join(ROOT, 'assets', 'site.css'), 'rb').read()).hexdigest()[:8]
def nav(p, cur):
    items = [('index.html', 'Accueil'), ('comparateur.html', 'Comparateur'), ('face-a-face.html', 'Face à face'), ('marques.html', 'Marques et modèles'), ('selections.html', 'Sélections'), ('methode.html', 'Méthode')]
    links = ''.join(f'<a href="{p}{h}"{" aria-current=\"page\"" if h == cur else ""}>{t}</a>' for h, t in items)
    return f'<nav class="topnav" aria-label="Navigation principale"><a class="logo" href="{p}index.html" aria-label="Mioto, accueil">{LOGO_SVG}<span class="logo-tag">comparateur de voitures neuves</span></a><div class="topnav-links">{links}</div></nav>'
def head(title, desc, path, p, extra=''):
    canon = f'<link rel="canonical" href="{SITE_URL}{path}">\n<meta property="og:url" content="{SITE_URL}{path}">' if SITE_URL else ''
    og_img = (f'\n<meta property="og:image" content="{SITE_URL}assets/og-image.png">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">'
              f'\n<meta property="og:image:alt" content="Mioto, le comparateur de voitures neuves selon vos critères">\n<meta name="twitter:card" content="summary_large_image">') if SITE_URL else ''
    return f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Mioto">
<meta property="og:locale" content="fr_FR">
{canon}{og_img}
<meta name="theme-color" content="#6620F0">
<link rel="icon" href="{p}assets/favicon.ico" sizes="48x48">
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{p}assets/apple-touch-icon.png">
<link rel="preload" href="{p}assets/fonts/outfit-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{p}assets/site.css?v={CSS_V}">
{extra}
</head>
<body>
'''
def foot(p):
    return f'''<footer class="site-foot"><div class="wrap">
  <p><b>Mioto</b> — le comparateur indépendant de voitures neuves selon vos critères, pour les modèles vendus en France. Données mises à jour le {TODAY.strftime('%d/%m/%Y')}.</p>
  <p><a href="{p}index.html">Accueil</a> · <a href="{p}comparateur.html">Comparateur</a> · <a href="{p}face-a-face.html">Face à face</a> · <a href="{p}marques.html">Marques et modèles</a> · <a href="{p}selections.html">Sélections</a> · <a href="{p}methode.html">Méthode</a> · <a href="{p}mentions-legales.html">Mentions légales</a></p>
  <p class="small">Prix « à partir de » indicatifs, tarifs constructeurs. Vérifiez les conditions auprès du constructeur ou d'un concessionnaire avant tout achat.</p>
</div></footer>
</body>
</html>
'''
def hero_small(p, cur, kicker, h1, sub, right=''):
    return f'''<header class="hero hero-sm">
  {nav(p, cur)}
  <div class="hero-in"><div><div class="kicker">{kicker}</div><h1>{h1}</h1>{f'<p>{sub}</p>' if sub else ''}</div>{right}</div>
  <div class="road"></div>
</header>
'''
def write(rel, txt):
    path = os.path.join(OUT, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(txt)

# --- page d'accueil (comparateur) ----------------------------------------------
def build_index():
    body = open(os.path.join(ROOT, 'src/index.body.html'), encoding='utf-8').read()
    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    meta_js = {k: META[k] for k in ('NATION', 'ADJ', 'SITE', 'SCORE_ENV')}
    meta_js['LIENS'] = LIENS
    body = body.replace('__NAV__', nav('', 'comparateur.html')).replace('__DATA__', js(CARS)).replace('__AVIS__', js(AVIS)).replace('__META__', js(meta_js)).replace('__PHOTOS__', js({k: {'f': v['f'], 'c': v['credit']} for k, v in PH.items()}))
    n_models, n_brands = len(MODELS), len({b for b, _ in MODELS})
    desc = f'Trouvez la voiture neuve qui vous correspond parmi {n_models} modèles de {n_brands} marques vendues en France : note sur 100 selon vos critères, avis et fiches détaillées.'
    write('comparateur.html', head('Le comparateur | Mioto', desc, 'comparateur.html', '') + body + '\n' + foot(''))


# --- face à face : jusqu'à 4 modèles choisis à la main --------------------------------
def build_face():
    src = open(os.path.join(ROOT, 'src/index.body.html'), encoding='utf-8').read()
    shared = '\n'.join(re.findall(r'//<shared>\n(.*?)//</shared>', src, re.S))   # mêmes fonctions et même fiche technique que le comparateur
    body = open(os.path.join(ROOT, 'src/face.body.html'), encoding='utf-8').read()
    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    meta_js = {k: META[k] for k in ('NATION', 'ADJ', 'SITE', 'SCORE_ENV')}
    meta_js['LIENS'] = LIENS
    body = (body.replace('__SHARED_JS__', shared).replace('__DATA__', js(CARS)).replace('__AVIS__', js(AVIS))
                .replace('__META__', js(meta_js)).replace('__PHOTOS__', js({k: {'f': v['f'], 'c': v['credit']} for k, v in PH.items()})))
    desc = "Comparez côte à côte jusqu'à quatre voitures neuves de votre choix : fiches techniques, prix, malus et avis de la presse, motorisation par motorisation."
    hero = hero_small('', 'face-a-face.html', 'Face à face', "Comparez <span>jusqu'à 4 modèles</span>",
                      "Vous savez déjà entre quelles voitures vous hésitez ? Choisissez-les et comparez leurs fiches techniques et notre avis côte à côte.")
    write('face-a-face.html', head("Face à face : comparez jusqu'à 4 voitures neuves | Mioto", desc, 'face-a-face.html', '') + hero + body + '\n' + foot(''))


# --- page d'accueil ------------------------------------------------------------------
# Exemples de la page d'accueil : notes recalculées à chaque génération avec la même
# formule que le comparateur (src/index.body.html), sur les données du jour.
BASE = .8
def _at_least(v, t, tol, bonus): return BASE + (1 - BASE) * min(1, (v - t) / (bonus * t)) if v >= t else BASE * max(0, 1 - (t - v) / (tol * t))
def _at_most(v, t, tol, bonus): return BASE + (1 - BASE) * min(1, (t - v) / (bonus * t)) if v <= t else BASE * max(0, 1 - (v - t) / (tol * t))
def _round(x): return int(math.floor(x + .5))
MOTO_SIM = {'ess': {'ess': 1, 'essm': .9, 'gpl': .6, 'hev': .5, 'phev': .3, 'die': .2, 'diem': .2}, 'die': {'die': 1, 'diem': .9, 'ess': .2, 'essm': .2},
            'mhev': {'essm': 1, 'diem': 1, 'hev': .6, 'ess': .5, 'die': .4, 'phev': .3}, 'hev': {'hev': 1, 'phev': .6, 'essm': .5, 'diem': .4, 'ev': .2},
            'phev': {'phev': 1, 'hev': .5, 'ev': .4}, 'ev': {'ev': 1, 'h2': .5, 'phev': .4}, 'gpl': {'gpl': 1, 'ess': .3, 'essm': .2}, 'h2': {'h2': 1, 'ev': .5}}
MOTO_LBL = {'ess': 'Essence', 'die': 'Diesel', 'mhev': 'Hybride léger', 'hev': 'Hybride', 'phev': 'Hybride rechargeable', 'ev': 'Électrique', 'gpl': 'GPL', 'h2': 'Hydrogène'}
IMP = {1: 'Secondaire', 2: 'Important', 3: 'Impératif'}

def _crit(c, k, o):
    """Renvoie (nom, cible, valeur affichée, note 0-1, explication) ou None si la donnée manque."""
    def vs(score, plus, pile, moins): return plus if score > .805 else (pile if score >= .795 else moins)
    if k == 'price':
        v, t = c.get('p'), o['val']
        if v is None: return None
        v += c.get('ml', 0)   # prix malus 2026 inclus, comme dans le comparateur
        sc = _at_most(v, t, .15, .4)
        why = f'{eur(t - v)} sous le budget, bonus' if sc > .805 else ('Tout juste dans le budget' if v <= t else f'{eur(v - t)} au-dessus du budget, la note chute')
        return 'Budget', f'{eur(t)} maximum', eur(v) + (' malus inclus' if c.get('ml') else ''), sc, why
    if k == 'body':
        tg = tags(c); sc = 1 if any(t in o['val'] for t in tg) else 0
        return 'Carrosserie', ' ou '.join(o['val']), c['c'], sc, 'Conforme' if sc else 'Non conforme'
    if k == 'moto':
        sc = max(MOTO_SIM[u].get(c['e'], 0) for u in o['val'])
        return 'Motorisation', ' ou '.join(MOTO_LBL[u] for u in o['val']), ENERGY.get(c['e'], c['e']), sc, 'Conforme' if sc == 1 else ('Proche, note partielle' if sc else 'Non conforme')
    if k == 'aut':
        v, t = c.get('aut'), o['val']
        if v is None: return None
        sc = _at_least(v, t, .5, .5); return 'Autonomie', f'{fmt(t)} km minimum', f'{fmt(v)} km', sc, vs(sc, 'Mieux que demandé', 'Pile la cible', 'Un peu juste')
    if k == 'chg':
        v, t = c.get('kw'), o['val']
        if v is None: return None
        sc = _at_least(v, t, .6, 1); return 'Recharge', f'{fmt(t)} kW minimum', f'{fmt(v)} kW', sc, vs(sc, 'Mieux que demandé', 'Pile la cible', 'Un peu juste')
    if k == 'trunk':
        v, t = c.get('tk'), o['val']
        if v is None: return None
        sc = _at_least(v, t, .35, .4); return 'Coffre', f'{fmt(t)} L minimum', f'{fmt(v)} L', sc, vs(sc, 'Plus grand que demandé', 'Pile la cible', 'Plus petit que demandé')
    if k == 'seats':
        big = c['pl'] > 5; sc = (1 if big else 0) if o['val'] == 'gt5' else (.6 if big else 1)
        return 'Places', 'Plus de 5' if o['val'] == 'gt5' else '5 au plus', f"{c['pl']} places", sc, 'Conforme' if sc == 1 else 'Non conforme'
    if k == 'ncap':
        v, t = c.get('nc'), o['val']
        if v is None: return None
        sc = (1 if t >= 5 else BASE + (1 - BASE) * (v - t) / (5 - t)) if v >= t else BASE * max(0, 1 - (t - v) / 2)
        return 'Euro NCAP', f'{t} étoiles minimum', f'{v} étoiles', sc, 'Conforme' if v >= t else 'En deçà'
    if k == 'power':
        h, lo, hi = c.get('hp'), o['min'], o.get('max')
        if h is None: return None
        sc = BASE * max(0, 1 - (lo - h) / (.4 * lo)) if h < lo else (BASE * max(0, 1 - (h - hi) / (.5 * hi)) if hi and h > hi else 1)
        return 'Puissance', f'{lo} à {hi} ch' if hi else f'{lo} ch minimum', f'{h} ch', sc, 'Dans la fourchette' if sc == 1 else 'Hors fourchette'
    if k == 'trans':
        awd = c.get('tr') == 'AWD'; sc = (1 if awd else 0) if o['val'] == 'awd' else (.6 if awd else 1)
        return 'Transmission', '4 roues motrices' if o['val'] == 'awd' else '2 roues motrices', TR.get(c.get('tr'), 'n.c.'), sc, 'Conforme' if sc == 1 else 'Non conforme'
    if k == 'box':
        sc = 1 if c.get('bx') == o['val'] else 0; lbl = {'A': 'Automatique', 'M': 'Manuelle'}
        return 'Boîte', lbl[o['val']], lbl.get(c.get('bx'), 'n.c.'), sc, 'Conforme' if sc else 'Non conforme'

EXAMPLES = [  # six critères au moins par exemple ; chaque voiture arrivait en tête du comparateur avec ces critères (octobre 2026)
    ('Une citadine électrique pour Léa', 'BYD', 'Dolphin Surf', 'Boost 43,2 kWh 88 ch',
     [('price', 3, {'val': 32000}), ('body', 3, {'val': ['Citadine']}), ('moto', 3, {'val': ['ev']}), ('aut', 2, {'val': 400}), ('ncap', 2, {'val': 4}), ('trunk', 1, {'val': 300})]),
    ('Un sept places pour la famille Martin', 'Renault', 'Espace', '1.2 Full Hybrid E-Tech 200 ch',
     [('seats', 3, {'val': 'gt5'}), ('price', 2, {'val': 45000}), ('ncap', 2, {'val': 5}), ('box', 2, {'val': 'A'}), ('moto', 1, {'val': ['hev']}), ('trunk', 1, {'val': 600})]),
    ('Partir loin en électrique avec Karim', 'Tesla', 'Model 3', 'Grande Autonomie RWD 320 ch',
     [('moto', 3, {'val': ['ev']}), ('aut', 3, {'val': 550}), ('chg', 2, {'val': 150}), ('price', 2, {'val': 50000}), ('ncap', 2, {'val': 5}), ('trunk', 1, {'val': 450})]),
    ('Un SUV pour la montagne pour Hélène', 'Ford', 'Kuga', '2.5 Duratec Hybrid I-AWD 183 ch',
     [('body', 3, {'val': ['SUV']}), ('trans', 3, {'val': 'awd'}), ('price', 2, {'val': 40000}), ('power', 1, {'min': 130, 'max': 200}), ('box', 1, {'val': 'A'}), ('trunk', 1, {'val': 450})]),
    ('Un break hybride pour Thomas, gros rouleur', 'Toyota', 'Corolla Touring', '1.8 Hybride 140 ch',
     [('body', 3, {'val': ['Break']}), ('moto', 2, {'val': ['hev']}), ('price', 2, {'val': 40000}), ('trunk', 2, {'val': 550}), ('ncap', 2, {'val': 4}), ('box', 1, {'val': 'A'})]),
    ('Le plaisir de conduire pour Marc', 'Ford', 'Mustang', '5.0 Ti-VCT V8 BVM6 446 ch',
     [('body', 3, {'val': ['Sportive', 'Coupé']}), ('power', 3, {'min': 300, 'max': 450}), ('price', 2, {'val': 70000}), ('moto', 2, {'val': ['ess']}), ('box', 1, {'val': 'M'}), ('trunk', 1, {'val': 300})]),
]
def _col(sc): return 'var(--s80)' if sc >= 80 else 'var(--s60)' if sc >= 60 else 'var(--s40)' if sc >= 40 else 'var(--s0)'

def examples_html():
    figs = []
    for title, b, m, v, crits in EXAMPLES:
        best = None
        for c in (x for x in CARS if x['b'] == b and x['m'] == m and x['v'] == v):  # versions homonymes : on garde la mieux notée
            rows, num, den = [], 0, 0
            for k, w, o in crits:
                r = _crit(c, k, o)
                if r is None: rows = None; break
                name, cible, val, sc, why = r; num += sc * w; den += w; s100 = _round(100 * sc)
                rows.append(f'<li><span class="ex-c"><b>{name}</b><small>{esc(cible)}</small></span><span class="ex-w">{IMP[w]} <em>×{w}</em></span>'
                            f'<span class="ex-bar"><i style="width:{max(s100, 2)}%;background:{_col(s100)}"></i></span><span class="ex-s num">{s100}</span>'
                            f'<span class="ex-why">{esc(val)} : {why[0].lower() + why[1:]}</span></li>')
            if rows and (best is None or num / den > best[1]): best = (rows, num / den)
        if best is None: print(f'  exemple ignoré (version introuvable ou donnée manquante) : {b} {m} {v}'); continue
        rows = best[0]
        total = _round(100 * best[1]); i = len(figs) + 1
        figs.append(f'''<figure class="ex-card" aria-label="Exemple {i} : {esc(title)}">
        <figcaption><span class="ex-k">Exemple {i}</span><b>{esc(title)}</b><small><a href="modeles/{mslug(b, m)}.html">{esc(b)} {esc(m)}</a>, {esc(v)}</small></figcaption>
        <ol class="ex-list">{''.join(rows)}</ol>
        <div class="ex-total"><span>Note finale<small>moyenne pondérée des {len(rows)} critères</small></span><b class="num" style="color:{_col(total)}">{total}<small>/100</small></b></div>
      </figure>''')
    if not figs: return ''
    n = len(figs)
    cur = ' aria-current="true"'
    dots = ''.join(f'<button type="button" aria-label="Exemple {i + 1}"{cur if i == 0 else ""}></button>' for i in range(n))
    return f'''<div class="ex-slider" data-slider>
      <div class="ex-track" tabindex="0" aria-label="Exemples de notes">{''.join(figs)}</div>
      <div class="ex-nav"><button type="button" class="ex-prev" aria-label="Exemple précédent">‹</button><div class="ex-dots">{dots}</div><span class="ex-count num">1 / {n}</span><button type="button" class="ex-next" aria-label="Exemple suivant">›</button></div>
    </div>
    <script>(()=>{{const s=document.querySelector('[data-slider]');if(!s)return;const t=s.querySelector('.ex-track'),f=[...t.children],d=[...s.querySelectorAll('.ex-dots button')],n=s.querySelector('.ex-count');
      const cur=()=>Math.round(t.scrollLeft/t.clientWidth);const go=i=>{{i=(i+f.length)%f.length;t.scrollTo({{left:i*t.clientWidth,behavior:'smooth'}});}};
      const upd=()=>{{const i=cur();d.forEach((b,j)=>b.toggleAttribute('aria-current',j===i));n.textContent=(i+1)+' / '+f.length;}};
      t.addEventListener('scroll',()=>requestAnimationFrame(upd),{{passive:true}});
      s.querySelector('.ex-prev').onclick=()=>go(cur()-1);s.querySelector('.ex-next').onclick=()=>go(cur()+1);d.forEach((b,j)=>b.onclick=()=>go(j));
      t.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'){{e.preventDefault();go(cur()+1);}}if(e.key==='ArrowLeft'){{e.preventDefault();go(cur()-1);}}}});}})();</script>'''

def build_home():
    p = ''; n_models = len(MODELS); n_brands = len({b for b, _ in MODELS}); n_avis = len(AVIS)
    parade = ''.join(SILS[k] for k in ['Citadine', 'SUV urbain', 'Berline', 'Sportive', 'Break', 'Tout-terrain'])
    slides = examples_html()
    desc = f"Mioto, le comparateur de voitures neuves selon vos critères, classe les voitures neuves vendues en France selon vos propres critères : une note sur 100 pour chacune des {fmt(len(CARS))} versions de {n_models} modèles, avec fiches et avis."
    body = f'''<header class="hero home-hero">
  {nav(p, 'index.html')}
  <div class="home-in">
    <div class="kicker">Indépendant · sans publicité</div>
    <h1 class="home-title">Le comparateur de voitures neuves <span>selon vos critères</span></h1>
    <p class="home-lead">Vous savez ce qui compte pour vous : un budget, une taille, une autonomie, un grand coffre… Nous passons au crible les <b>{fmt(len(CARS))} versions</b> de <b>{n_models} modèles</b> vendus en France et donnons à chacune une <b>note sur&nbsp;100</b> qui dit à quel point elle vous correspond.</p>
    <div class="home-ctas">
      <a class="cta cta-main" href="{p}comparateur.html">Lancer le comparateur</a>
      <a class="cta cta-alt" href="{p}marques.html">Parcourir les marques et modèles</a>
    </div>
  </div>
  <div class="parade home-parade" aria-hidden="true">{parade}</div>
  <div class="road"></div>
</header>
<div class="wrap page home">
  <section class="steps" aria-labelledby="h-steps">
    <h2 class="sec-title" id="h-steps">Comment ça marche</h2>
    <ol class="step-list">
      <li><span class="step-n">1</span><h3>Choisissez vos critères</h3><p>Budget, carrosserie, nombre de places, motorisation, puissance, coût de l'énergie, autonomie, coffre, sécurité… Activez seulement ceux qui comptent pour vous.</p></li>
      <li><span class="step-n">2</span><h3>Dites ce qui est important</h3><p>Chaque critère peut être <b>secondaire</b>, <b>important</b> ou <b>impératif</b>. Un critère impératif pèse trois fois plus qu'un critère secondaire.</p></li>
      <li><span class="step-n">3</span><h3>Découvrez votre classement</h3><p>Les voitures sont classées instantanément, de la mieux notée à la moins bien notée. Comparez-en jusqu'à trois côte à côte et ouvrez leur fiche détaillée.</p></li>
    </ol>
  </section>

  <section class="home-sel" aria-labelledby="h-sel">
    <h2 class="sec-title" id="h-sel">Nos sélections</h2>
    <ul class="home-sel-list">{''.join(f'<li><a href="selections/{x["slug"]}.html">{_nb(esc(x["short"]))}</a></li>' for x in SELECTIONS)}</ul>
  </section>

  <section class="card note-card" aria-labelledby="h-note">
    <div class="note-txt">
      <h2 id="h-note">Pourquoi une note sur 100 ?</h2>
      <p>Comparer des fiches techniques, c'est comparer des chiffres qui ne disent pas tous la même chose. Une note unique répond à une seule question : <b>cette voiture vous correspond-elle ?</b> Elle ne dit pas qu'une voiture est « bonne » dans l'absolu : la même voiture peut obtenir 95 pour une personne et 40 pour une autre.</p>
      <h3>Comment elle est calculée</h3>
      <ul class="rules">
        <li><b>Chaque critère est noté sur 100.</b> Atteindre tout juste votre cible vaut 80 ; faire nettement mieux rapporte jusqu'à 20 points de plus ; être en deçà en fait perdre.</li>
        <li><b>Les notes sont pondérées</b> par l'importance que vous avez choisie (×1, ×2 ou ×3).</li>
        <li><b>Le budget est un plafond.</b> En dessous, la voiture gagne des points ; au-dessus, sa note de prix chute vite et tombe à 0 dès 15&nbsp;% de dépassement.</li>
        <li><b>La moyenne pondérée donne la note finale.</b> À note égale, la voiture la moins chère passe devant.</li>
        <li><b>Un critère impératif raté</b> peut écarter la voiture du classement : c'est vous qui décidez.</li>
        <li><b>Les avis de la rédaction n'entrent jamais dans le calcul</b> : la note ne dépend que de vos critères et des données.</li>
      </ul>
      <p><a href="{p}methode.html">Tous les détails de la méthode</a></p>
    </div>
    {slides}
  </section>

  <section class="facts" aria-label="En chiffres">
    <div class="fact"><b class="num">{fmt(len(CARS))}</b><span>versions notées</span></div>
    <div class="fact"><b class="num">{n_models}</b><span>modèles, des citadines aux SUV</span></div>
    <div class="fact"><b class="num">{n_brands}</b><span>marques parmi les plus vendues en France</span></div>
    <div class="fact"><b class="num">{n_avis}</b><span>avis rédigés à partir d'au moins deux essais de la presse auto</span></div>
  </section>

  <section class="choices" aria-labelledby="h-go">
    <h2 class="sec-title" id="h-go">Par où commencer ?</h2>
    <div class="choice-grid">
      <a class="choice" href="{p}comparateur.html"><span class="choice-k">Je cherche une voiture</span><b>Le comparateur</b><span>Partez d'une page blanche, activez vos critères et obtenez votre classement personnalisé.</span><span class="choice-go">Lancer le comparateur →</span></a>
      <a class="choice" href="{p}marques.html"><span class="choice-k">Je veux explorer</span><b>Les marques et modèles</b><span>Les {n_models} modèles de {n_brands} marques, avec leurs versions, leurs prix, leurs caractéristiques et notre avis.</span><span class="choice-go">Parcourir le répertoire →</span></a>
    </div>
  </section>
</div>
'''
    write('index.html', head('Mioto — le comparateur de voitures neuves selon vos critères', desc, '', p) + body + foot(p))

# --- fiches modèles ---------------------------------------------------------------
def tile(v, l): return f'<div class="tile"><b class="num">{v}</b><span>{l}</span></div>'
def rng(vals, unit, d=0):
    vals = [v for v in vals if v is not None]
    if not vals: return '—'
    a, b = min(vals), max(vals)
    return f'{fmt(a, d)}{NB}{unit}' if a == b else f'{fmt(a, d)} à {fmt(b, d)}{NB}{unit}'
def avis_html(b, m):
    blocks = avis_for(b, m)
    if not blocks: return ''
    out = ''
    for title, a in blocks:
        out += f'''<div class="avis-bloc">{f'<h3>{esc(title)}</h3>' if title else ''}
  <blockquote class="lead">{esc(a['v'])}</blockquote>
  <div class="avis-cols">
    <div><h5 class="pl">Points forts</h5><ul class="c-ul pl">{''.join(f'<li>{esc(x)}</li>' for x in a['p'])}</ul></div>
    <div><h5 class="mn">Points faibles</h5><ul class="c-ul mn">{''.join(f'<li>{esc(x)}</li>' for x in a['m'])}</ul></div>
  </div>
  <p class="avis-q"><b>Pour qui ?</b> {esc(a['q'])}</p>
  {f'<p class="avis-x"><b>Selon la version</b> {esc(a["x"])}</p>' if a.get('x') else ''}
  {f'<p class="avis-s"><b>Bon à savoir</b> {esc(a["s"])}</p>' if a.get('s') else ''}
</div>'''
    return f'<section class="card"><h2>Notre avis</h2>{out}<p class="small">Synthèse d\'au moins deux essais de la presse automobile, sans influence sur les notes du comparateur.</p></section>'
# tableau des versions : libellés courts et lisibles
TR_COURT = {'FWD': 'Traction', 'RWD': 'Propulsion', 'AWD': '4x4'}
def boite_txt(c):
    b = c.get('bxl') or ''
    if b.startswith('BVM'): return 'Manuelle' + (f' {b[3:]}' if b[3:] else '')
    if b.startswith('BVA') or c.get('bx') == 'A': return 'Automatique'
    return esc(b)
def recharge_td(c):
    # électrique : durée 10-80 % puis puissance de recharge rapide ; hybride rechargeable : puissance de charge
    if c['e'] == 'ev':
        parts = ([f"10-80{NB}% en {fmt(c['t80'])}{NB}min"] if c.get('t80') else []) + ([f"{fmt(c['kw'], 1 if c['kw'] % 1 else 0)}{NB}kW max."] if c.get('kw') else [])
    elif c['e'] == 'phev' and c.get('kw'):
        parts = [f"{fmt(c['kw'], 1 if c['kw'] % 1 else 0)}{NB}kW"]
    else:
        parts = []
    return f'<td class="num">{" · ".join(parts) or "—"}</td>'
def conso(c):
    # consommation d'abord (avec son unité), puis l'autonomie électrique
    if c['e'] == 'ev':
        parts = ([f"{fmt(c['kwh'],1)}{NB}kWh/100{NB}km"] if c.get('kwh') else []) + ([f"{c['aut']}{NB}km"] if c.get('aut') else [])
        return ' · '.join(parts) or '—'
    s = f"{fmt(c['l'],1)}{NB}L/100{NB}km" if c.get('l') is not None else '—'
    if c['e'] == 'phev' and c.get('aut'): s += f" · {c['aut']}{NB}km élec."
    return s
def similar(b, m, l):
    c0 = l[0]; t0 = tags(c0)[0]; p0 = pmin(l) or 0
    cands = []
    for (bb, mm), ll in MODELS.items():
        if (bb, mm) == (b, m): continue
        if t0 not in tags(ll[0]): continue
        p = pmin(ll)
        if p is None or not p0: continue
        cands.append((abs(p - p0) / p0, bb, mm, ll))
    cands.sort(key=lambda x: x[0])
    return cands[:6]
def mini_card(bb, mm, ll, p):
    c = ll[0]; en = sorted({ENERGY[x['e']] for x in ll})
    return f'''<a class="mcard" href="{p}modeles/{mslug(bb, mm)}.html"><span class="msil{' has-ph' if photo(bb, mm) else ''}">{pic(c, p)}</span><span class="mname">{flag(bb)} {esc(bb)} {esc(mm)}</span><span class="mmeta">{esc(tags(c)[0])} · {esc(' / '.join(en))}</span><span class="mprice">{'dès ' + eur(pmin(ll)) if pmin(ll) else 'prix n.c.'}</span></a>'''

def build_model(b, m, l):
    c0 = l[0]; p = '../'; name = f'{b} {m}'
    en = sorted({ENERGY[c['e']] for c in l}, key=lambda x: list(ENERGY.values()).index(x))
    ev = [c for c in l if c['e'] == 'ev']; therm = [c for c in l if c['e'] != 'ev']
    tiles = []
    if ev: tiles.append(tile(rng([c.get('aut') for c in ev], 'km'), 'Autonomie WLTP'))
    if therm: tiles.append(tile(rng([c.get('l') for c in therm if c['e'] != 'phev'] or [c.get('l') for c in therm], 'L', 1), 'Conso. /100 km'))
    tiles.append(tile(rng([c.get('hp') for c in l], 'ch'), 'Puissance'))
    tiles.append(tile(rng([c.get('tk') for c in l], 'L'), 'Coffre'))
    nc = next((c.get('nc') for c in l if c.get('nc')), None)
    tiles.append(tile(f'{nc}{NB}★' if nc else 'n.c.', 'Euro NCAP'))
    badges = []
    el = [c for c in l if eligible(c)]
    if el: badges.append('<span class="bdg aid">Éligible aux aides' + ('' if len(el) == len(l) else (' (' + ', '.join(esc(c['v']) for c in el) + ')' if len(el) <= 2 else ' (certaines versions)')) + '</span>')
    ends = {c['end'] for c in l if c.get('end')}
    if ends: badges.append(f'<span class="bdg warn">Fin de commercialisation {min(ends)}</span>')
    soon = {c['y'] for c in l if c.get('y') and c['y'] > TODAY.year}
    if soon: badges.append(f'<span class="bdg warn">Arrivée prévue en {min(soon)}</span>')
    site = LIENS.get(f'{b}|{m}') or SITE.get(b)
    has_chg = any(c['e'] in ('ev', 'phev') and (c.get('t80') or c.get('kw')) for c in l)
    rows = ''.join(f'''<tr><th scope="row">{esc(c['v'])}</th><td>{esc(ENERGY[c['e']])}</td><td class="num">{c.get('hp','—')}{NB}ch</td><td>{boite_txt(c)}</td><td>{esc(TR_COURT.get(c.get('tr'), c.get('tr') or ''))}</td><td class="num">{conso(c)}</td>{recharge_td(c) if has_chg else ''}<td class="num">{c.get('tk','—')}</td><td class="num pr">{eur(c.get('p'))}{' <span class="aidt">aides</span>' if eligible(c) else ''}{f'<small class="mlt">+ {eur(c["ml"])} de malus</small>' if c.get('ml') else ''}</td></tr>''' for c in l)
    def span(vals, unit='', d=0):
        return rng(vals, unit, d)
    dl = [('Carrosserie', esc(c0['c'])), ('Motorisations', esc(' · '.join(en))), ('Places', esc(' ou '.join(sorted({str(c.get('pl')) for c in l if c.get('pl')})))),
          ('Portes', esc(' ou '.join(sorted({str(c.get('dr')) for c in l if c.get('dr')})))), ('Longueur', span([c.get('len') for c in l], 'm', 2)),
          ('Poids à vide', span([c.get('w') for c in l], 'kg')), ('0 à 100 km/h', span([c.get('acc') for c in l], 's', 1)),
          ("Crit'Air", esc(' ou '.join(sorted({str(c.get('ca')) for c in l if c.get('ca') is not None})) or '—')),
          ('Coffre avant', esc(' ou '.join(sorted({'oui' if c['fk'] else 'non' for c in l if c.get('fk') is not None}, reverse=True)) or '—')),
          ('Recharge 10-80 %', span([c.get('t80') for c in l if c.get('t80')], 'min')),
          ('Commercialisé depuis', esc(str(min(c['y'] for c in l if c.get('y'))) if any(c.get('y') for c in l) else '—')),
          ('Marque', f"{flag(b)} {esc(b)} · {esc(ADJ.get(NATION.get(b, ''), ''))}")]
    dl = [(k, v) for k, v in dl if not (k in ('Coffre avant', 'Recharge 10-80 %') and v == '—')]
    if ev: dl.insert(5, ('Recharge rapide max.', span([c.get('kw') for c in ev], 'kW')))
    sims = similar(b, m, l)
    desc = (AVIS.get(f'{b}|{m}') or AVIS.get(f'{b}|{m}|ev') or {}).get('v') or f'{name} : prix, versions, autonomie, consommation et caractéristiques.'
    pm = pmin(l)
    title = f'{name} : prix, versions et avis' + (f' (dès {fmt(pm)} €)' if pm else '') + ' | Mioto'
    ld = {'@context': 'https://schema.org', '@type': 'Car', 'name': name, 'brand': {'@type': 'Brand', 'name': b}, 'bodyType': c0['c'],
          'vehicleEngine': [{'@type': 'EngineSpecification', 'name': c['v']} for c in l[:10]]}
    ps = [c['p'] for c in l if c.get('p')]
    if ps: ld['offers'] = {'@type': 'AggregateOffer', 'priceCurrency': 'EUR', 'lowPrice': min(ps), 'highPrice': max(ps), 'offerCount': len(ps)}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    sub = f"{esc(tags(c0)[0])} · {esc(' / '.join(en))} · {len(l)} version{'s' if len(l) > 1 else ''}"
    page = head(title, desc, f'modeles/{mslug(b, m)}.html', p, extra) + hero_small(p, '', f'{flag(b)} Fiche modèle · {esc(b)}', f'{esc(b)} <span>{esc(m)}</span>', sub, (f'<figure class="hero-photo">{pic(c0, p)}<figcaption>{esc(photo(b, m)["credit"])}</figcaption></figure>' if photo(b, m) else f'<div class="hero-sil">{sil(c0)}</div>')) + f'''<div class="wrap page">
  <nav class="crumbs" aria-label="Fil d'Ariane"><a href="{p}marques.html">Marques et modèles</a> › <a href="{p}marques.html#{slug(b)}">{esc(b)}</a> › <span>{esc(m)}</span></nav>
  <section class="card summary">
    <div class="sum-top">
      <div class="price num">{f'<small class="from">À partir de</small>{eur(pm)}' if pm else 'Prix non communiqué'}</div>
      <div class="acts2">{f'<a class="site-btn" href="{esc(site)}" target="_blank" rel="noopener">Voir sur le site {esc("DS" if b == "DS Automobiles" else b)}</a>' if site else ''}<a class="fiche-link" href="{p}face-a-face.html?m={quote(b + '|' + m)}">Comparer face à face</a><a class="fiche-link" href="{p}comparateur.html">Comparer avec mes critères</a></div>
    </div>
    {f'<div class="bdgs">{"".join(badges)}</div>' if badges else ''}
    <div class="tiles">{''.join(tiles)}</div>
  </section>
  {avis_html(b, m)}
  <section class="card"><h2>{f'Les {len(l)} versions' if len(l) > 1 else 'La seule version'}</h2>
    <div class="vt-wrap"><table class="vtable"><thead><tr><th scope="col">Version</th><th scope="col">Énergie</th><th scope="col">Puissance</th><th scope="col">Boîte</th><th scope="col">Transmission</th><th scope="col">Conso. / autonomie</th>{'<th scope="col">Recharge</th>' if has_chg else ''}<th scope="col">Coffre (L)</th><th scope="col">Prix dès</th></tr></thead><tbody>{rows}</tbody></table></div>
    <p class="small">Consommation et autonomie : valeurs minimales annoncées par le constructeur en cycle WLTP mixte. Prix « à partir de » de la finition d'entrée pour chaque motorisation. Malus 2026 (CO₂ et poids) estimé d'après le barème officiel, hors abattements familiaux.</p>
  </section>
  <section class="card"><h2>Caractéristiques</h2><dl class="specs">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in dl)}</dl></section>
  {f'<section><h2 class="sec-title">À comparer aussi</h2><div class="mgrid">{"".join(mini_card(bb, mm, ll, p) for _, bb, mm, ll in sims)}</div></section>' if sims else ''}
</div>
''' + foot(p)
    write(f'modeles/{mslug(b, m)}.html', page)

# --- marques -------------------------------------------------------------------------
# Catalogue : au sein d'une marque, les modèles sont rangés par catégorie (la carrosserie principale la plus fréquente de leurs versions)
CAT_ORDER = ['Citadine', 'Compacte', 'Berline', 'Break', 'Monospace', 'SUV urbain', 'SUV', 'Tout-terrain', 'Coupé', 'Cabriolet']
CAT_LABEL = {'Citadine': 'Citadines', 'Compacte': 'Compactes', 'Berline': 'Berlines', 'Break': 'Breaks', 'Monospace': 'Monospaces',
             'SUV urbain': 'SUV urbains', 'SUV': 'SUV', 'Tout-terrain': 'Tout-terrain', 'Coupé': 'Coupés', 'Cabriolet': 'Cabriolets et roadsters'}
def model_cat(l):
    from collections import Counter
    alias = {'Roadster': 'Cabriolet', 'Limousine': 'Berline'}
    return Counter(alias.get(c['c'].split(', ')[0], c['c'].split(', ')[0]) for c in l).most_common(1)[0][0]
def build_brands():
    p = ''; brands = sorted({b for b, _ in MODELS}, key=lambda s: slug(s))
    jump = ''.join(f'<a href="#{slug(b)}">{flag(b)} {esc(b)}</a>' for b in brands)
    secs = ''
    for b in brands:
        ms = [(mm, ll) for (bb, mm), ll in MODELS.items() if bb == b]
        groups = {}
        for mm, ll in ms: groups.setdefault(model_cat(ll), []).append((mm, ll))
        body = ''
        for cat in sorted(groups, key=lambda c: CAT_ORDER.index(c) if c in CAT_ORDER else 99):
            g = sorted(groups[cat], key=lambda x: pmin(x[1]) or 10**9)   # dans une catégorie : du moins cher au plus cher
            body += f'<div class="cat-grp"><h3 class="cat-h">{CAT_LABEL.get(cat, cat)} <small>{len(g)}</small></h3><div class="mgrid">{"".join(mini_card(b, mm, ll, p) for mm, ll in g)}</div></div>'
        secs += f'''<section class="brand-sec" id="{slug(b)}"><h2>{flag(b, 'flag-lg')} {esc(b)} <small>{len(ms)} modèle{'s' if len(ms) > 1 else ''} · marque {esc(ADJ.get(NATION.get(b, ''), ''))}</small></h2><div class="cat-wrap">{body}</div></section>'''
    n = len(MODELS)
    page = head('Toutes les marques et tous les modèles | Mioto', f'Les {n} modèles de voitures neuves de {len(brands)} marques vendues en France, avec prix, versions et avis.', 'marques.html', p) \
        + hero_small(p, 'marques.html', 'Catalogue', 'Marques <span>et modèles</span>', f'{n} modèles de {len(brands)} marques, rangés par catégorie puis par prix d\'entrée.') \
        + f'<div class="wrap page"><nav class="jump jump-desk" aria-label="Aller à une marque">{jump}</nav>' \
        + f'<details class="jump-mob" id="jump-mob"><summary><span>Aller à une marque</span><small>{len(brands)} marques</small></summary><nav class="jump-list" aria-label="Aller à une marque">{jump}</nav></details>' \
        + f'{secs}</div>' \
        + '<script>document.querySelectorAll("#jump-mob a").forEach(a=>a.addEventListener("click",()=>{document.getElementById("jump-mob").open=false}));</script>' + foot(p)
    write('marques.html', page)

# --- pages de texte ---------------------------------------------------------------
def build_text(rel, title, h1, kicker, desc, content):
    p = ''
    write(rel, head(f'{title} | Mioto', desc, rel, p) + hero_small(p, rel, kicker, h1, '') + f'<div class="wrap page prose">{content}</div>' + foot(p))

METHODE = open(os.path.join(ROOT, 'src/methode.html'), encoding='utf-8').read()
LEGAL = open(os.path.join(ROOT, 'src/mentions-legales.html'), encoding='utf-8').read()


# --- sélections thématiques (pages fixes pour les moteurs de recherche) ------------------------------------------------
# Chaque sélection est un jeu de critères passé au même moteur de notation que le comparateur ; une version par modèle,
# les voitures qui ratent un critère impératif sont écartées. Le bouton « Affiner » ouvre le comparateur pré-rempli.
import base64
SELECTIONS = [
  dict(slug='citadines-electriques-moins-de-25000-euros', t='Les meilleures citadines électriques à moins de 25 000 €', short='Citadines électriques à moins de 25 000 €',
       intro="Petites électriques pour la ville et la périphérie : prix catalogue sous 25 000 €, autonomie d'au moins 250 km et bonne note de sécurité.",
       crits=[('price', 3, {'val': 25000}), ('body', 3, {'val': ['Citadine']}), ('moto', 3, {'val': ['ev']}), ('aut', 2, {'val': 250}), ('ncap', 1, {'val': 4})]),
  dict(slug='voitures-electriques-eligibles-aux-aides', t='Les meilleures voitures électriques éligibles aux aides', short='Électriques éligibles aux aides',
       intro="Électriques ouvrant droit à la prime « coup de pouce » (ex-bonus écologique) : score environnemental obtenu, prix sous 47 000 € et poids sous 2,4 t.",
       aid=True, filt=lambda c: eligible(c),
       crits=[('moto', 3, {'val': ['ev']}), ('price', 2, {'val': 40000}), ('aut', 2, {'val': 400}), ('chg', 1, {'val': 100}), ('ncap', 1, {'val': 4})]),
  dict(slug='suv-electriques-moins-de-40000-euros', t='Les meilleurs SUV électriques à moins de 40 000 €', short='SUV électriques à moins de 40 000 €',
       intro="SUV compacts et familiaux 100 % électriques sous 40 000 €, avec au moins 400 km d'autonomie et un coffre logeable.",
       crits=[('body', 3, {'val': ['SUV urbain', 'SUV']}), ('moto', 3, {'val': ['ev']}), ('price', 3, {'val': 40000}), ('aut', 2, {'val': 400}), ('trunk', 1, {'val': 400})]),
  dict(slug='suv-hybrides-moins-de-35000-euros', t='Les meilleurs SUV hybrides à moins de 35 000 €', short='SUV hybrides à moins de 35 000 €',
       intro="SUV hybrides non rechargeables (full hybrid) sous 35 000 €, malus 2026 compris, avec un coffre d'au moins 400 litres.",
       crits=[('body', 3, {'val': ['SUV urbain', 'SUV']}), ('moto', 3, {'val': ['hev']}), ('price', 3, {'val': 35000}), ('trunk', 2, {'val': 400}), ('ncap', 1, {'val': 4})]),
  dict(slug='voitures-familiales-moins-de-30000-euros', t='Les meilleures voitures familiales à moins de 30 000 €', short='Familiales à moins de 30 000 €',
       intro="Toutes carrosseries confondues : un grand coffre (450 litres et plus), cinq étoiles Euro NCAP de préférence et un prix sous 30 000 €, malus compris.",
       crits=[('trunk', 3, {'val': 450}), ('price', 3, {'val': 30000}), ('ncap', 2, {'val': 5}), ('seats', 1, {'val': 'le5'})]),
  dict(slug='suv-7-places', t='Les meilleurs SUV 7 places', short='SUV 7 places',
       intro="SUV à sept places pour les grandes familles, classés selon le prix (jusqu'à 50 000 €, malus compris), la sécurité et la boîte automatique.",
       crits=[('seats', 3, {'val': 'gt5'}), ('body', 2, {'val': ['SUV']}), ('price', 2, {'val': 50000}), ('ncap', 1, {'val': 4}), ('box', 1, {'val': 'A'})]),
  dict(slug='breaks-grand-coffre', t='Les meilleurs breaks à grand coffre', short='Breaks à grand coffre',
       intro="Breaks d'au moins 600 litres de coffre pour les longs trajets et les vacances, classés aussi selon le prix et la sécurité.",
       crits=[('body', 3, {'val': ['Break']}), ('trunk', 3, {'val': 600}), ('price', 2, {'val': 45000}), ('ncap', 1, {'val': 4})]),
  dict(slug='voitures-electriques-grande-autonomie', t='Les voitures électriques avec la plus grande autonomie', short='Électriques à grande autonomie',
       intro="Électriques capables d'au moins 550 km en cycle WLTP mixte, avec une recharge rapide d'au moins 150 kW, jusqu'à 60 000 €.",
       crits=[('moto', 3, {'val': ['ev']}), ('aut', 3, {'val': 550}), ('chg', 2, {'val': 150}), ('price', 2, {'val': 60000})]),
  dict(slug='voitures-electriques-recharge-rapide', t='Les voitures électriques qui rechargent le plus vite', short='Électriques à recharge rapide',
       intro="Électriques acceptant au moins 200 kW sur borne rapide, avec une autonomie d'au moins 400 km.",
       crits=[('moto', 3, {'val': ['ev']}), ('chg', 3, {'val': 200}), ('aut', 2, {'val': 400}), ('price', 1, {'val': 60000})]),
  dict(slug='hybrides-rechargeables-grande-autonomie', t='Les hybrides rechargeables avec la plus grande autonomie électrique', short='Hybrides rechargeables à grande autonomie',
       intro="Hybrides rechargeables capables d'au moins 80 km en électrique (WLTP), pour rouler au quotidien sans essence, jusqu'à 50 000 €.",
       crits=[('moto', 3, {'val': ['phev']}), ('aut', 3, {'val': 80}), ('price', 2, {'val': 50000})]),
  dict(slug='voitures-neuves-les-moins-cheres', t='Les voitures neuves les moins chères', short='Voitures neuves les moins chères',
       intro="Les voitures neuves les plus abordables du marché français, malus 2026 compris, jusqu'à 20 000 € environ.",
       crits=[('price', 3, {'val': 20000}), ('trunk', 1, {'val': 250})]),
  dict(slug='premiere-voiture-jeune-conducteur', t='Les meilleures premières voitures pour jeune conducteur', short='Première voiture pour jeune conducteur',
       intro="Pour un premier achat : une puissance raisonnable (70 à 130 ch, plus simple à assurer et à maîtriser), un prix sous 20 000 € malus compris et une bonne note de sécurité.",
       crits=[('price', 3, {'val': 20000}), ('power', 3, {'min': 70, 'max': 130}), ('ncap', 2, {'val': 4}), ('body', 1, {'val': ['Citadine', 'Compacte', 'SUV urbain']})]),
  dict(slug='voitures-automatiques-moins-de-25000-euros', t='Les meilleures voitures automatiques à moins de 25 000 €', short='Automatiques à moins de 25 000 €',
       intro="Boîte automatique (ou électrique) sans se ruiner : prix sous 25 000 €, malus compris, avec une bonne note de sécurité.",
       crits=[('box', 3, {'val': 'A'}), ('price', 3, {'val': 25000}), ('ncap', 1, {'val': 4}), ('trunk', 1, {'val': 300})]),
  dict(slug='voitures-4-roues-motrices-moins-de-40000-euros', t='Les meilleures 4 roues motrices à moins de 40 000 €', short='4 roues motrices à moins de 40 000 €',
       intro="Transmission intégrale pour la montagne, la neige ou les chemins, sous 40 000 €, malus compris.",
       crits=[('trans', 3, {'val': 'awd'}), ('price', 3, {'val': 40000}), ('body', 2, {'val': ['SUV urbain', 'SUV', 'Tout-terrain']})]),
  dict(slug='sportives-moins-de-50000-euros', t='Les meilleures sportives à moins de 50 000 €', short='Sportives à moins de 50 000 €',
       intro="Coupés, cabriolets et sportives de 250 ch et plus sous 50 000 €, malus 2026 compris : le plaisir de conduire sans exploser le budget.",
       filt=lambda c: 'SUV' not in c['c'],   # les SUV « coupés » ne sont pas des sportives
       crits=[('body', 3, {'val': ['Sportive', 'Coupé', 'Cabriolet']}), ('power', 3, {'min': 250, 'max': 0}), ('price', 3, {'val': 50000})]),
  dict(slug='voitures-sans-malus-2026', t='Les meilleures voitures thermiques et hybrides sans malus en 2026', short='Thermiques et hybrides sans malus',
       intro="Voitures essence, diesel et hybrides qui échappent au malus CO₂ et au malus au poids 2026, classées selon le prix et le coffre.",
       filt=lambda c: c['e'] not in ('ev', 'h2') and not c.get('ml'),
       crits=[('price', 2, {'val': 25000}), ('trunk', 1, {'val': 350}), ('ncap', 1, {'val': 4})]),
]
UNK = .5
def _sel_score(c, crits):
    num = den = 0; parts = []; fail = False
    for k, w, o in crits:
        r = _crit(c, k, o)
        if r is None: val, sc = 'n.c.', UNK
        else: _, _, val, sc, _ = r
        num += sc * w; den += w; parts.append((k, val, sc))
        if w == 3 and sc < .5: fail = True
    return num / den, parts, fail
def selection_rank(sel):
    best = {}
    for c in CARS:
        if c.get('p') is None or (sel.get('filt') and not sel['filt'](c)): continue
        sc, parts, fail = _sel_score(c, sel['crits'])
        if fail: continue
        tot = c['p'] + c.get('ml', 0); key = (c['b'], c['m'])
        if key not in best or (sc, -tot) > (best[key][0], -best[key][3]): best[key] = (sc, c, parts, tot)
    return sorted(best.values(), key=lambda x: (-x[0], x[3]))
def sel_state(sel):
    st = {}
    for k, w, o in sel['crits']:
        x = {'w': w}
        if k == 'price': x.update({'min': 0, 'val': o['val'], 'malus': True})
        elif k == 'power': x.update({'min': o['min'], 'max': o.get('max') or 0})
        elif k == 'trunk': x.update({'val': o['val'], 'fk': False})
        else: x['val'] = o['val']
        st[k] = x
    if sel.get('aid'): st['aid'] = {}
    raw = json.dumps({'s': st, 'o': {'m': True, 'st': True}}, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')
CRIT_TXT = {'price': lambda o: f"prix jusqu'à {eur(o['val'])}, malus compris", 'body': lambda o: ' ou '.join(o['val']),
            'moto': lambda o: ' ou '.join(MOTO_LBL[u] for u in o['val']), 'aut': lambda o: f"autonomie d'au moins {fmt(o['val'])} km",
            'chg': lambda o: f"recharge d'au moins {fmt(o['val'])} kW", 'trunk': lambda o: f"coffre d'au moins {fmt(o['val'])} L",
            'ncap': lambda o: f"{o['val']} étoiles Euro NCAP ou plus", 'seats': lambda o: 'plus de 5 places' if o['val'] == 'gt5' else '5 places',
            'box': lambda o: 'boîte automatique' if o['val'] == 'A' else 'boîte manuelle', 'trans': lambda o: '4 roues motrices' if o['val'] == 'awd' else '2 roues motrices',
            'power': lambda o: f"{o['min']} ch minimum" + (f" et {o['max']} ch maximum" if o.get('max') else '')}
def _first_sentence(t, n=170):
    t = t.split('. ')[0].rstrip('.') + '.'
    return t if len(t) <= n else t[:n - 1].rsplit(' ', 1)[0] + '…'
def _nb(t): return re.sub(r'(\d) (\d{3})', '\\1\u202f\\2', t).replace(' €', '\u00a0€')
def _pl(n, word): return f"{n} {word}{'s' if n > 1 else ''}"
def build_selections():
    p = '../'; cards = []; day = TODAY.strftime('%d/%m/%Y')
    for sel in SELECTIONS:
        L = selection_rank(sel); top = L[:10]
        if not top: print('  sélection vide :', sel['slug']); continue
        rel = f"selections/{sel['slug']}.html"
        crit_li = ''.join(f"<li><b>{IMP[w]}</b> : {esc(CRIT_TXT[k](o))}</li>" for k, w, o in sel['crits'])
        if sel.get('aid'): crit_li += "<li><b>Filtre</b> : éligible aux aides à l'achat</li>"
        items = []
        for i, (sc, c, parts, tot) in enumerate(top, 1):
            s100 = _round(100 * sc); b, m = c['b'], c['m']
            facts = ' · '.join(esc(str(v)) for k, v, _ in parts if k != 'price' and v != 'n.c.')
            av = avis_for(b, m); verdict = _first_sentence(av[0][1]['v']) if av else ''
            ml = f'<small class="mlp">+ {eur(c["ml"])} de malus</small>' if c.get('ml') else ''
            aid = ' <span class="aidt">aides</span>' if eligible(c) else ''
            items.append(
                f'<li class="sel-item"><span class="sel-rank num">{i}</span><div class="sel-main">'
                f'<a class="sel-name" href="{p}modeles/{mslug(b, m)}.html">{flag(b)} {esc(b)} {esc(m)}</a><span class="sel-ver">{esc(c["v"])}</span>'
                + (f'<span class="sel-facts">{facts}</span>' if facts else '') + (f'<p class="sel-avis">{esc(verdict)}</p>' if verdict else '')
                + f'</div><div class="sel-side"><span class="score num" style="background:{_col(s100)}">{s100}<small>/100</small></span>'
                f'<span class="sel-pr num"><small>à partir de</small>{eur(c["p"])}{aid}{ml}</span></div></li>')
        others = ''.join(f'<li><a href="{x["slug"]}.html">{_nb(esc(x["short"]))}</a></li>' for x in SELECTIONS if x is not sel)
        desc = f"{sel['t']} : le classement Mioto des {len(top)} meilleurs modèles, avec une note sur 100, mis à jour le {day}."
        body = (f'<div class="wrap page sel"><p class="sel-intro">{_nb(esc(sel["intro"]))} Classement calculé par le moteur de notation de Mioto : '
                f'une note sur 100 par voiture, une version par modèle (la mieux notée), {_pl(len(L), "modèle")} en lice.</p>'
                f'<div class="card sel-crits"><div><h2>Les critères de cette sélection</h2><ul>{crit_li}</ul></div>'
                f'<div class="sel-cta"><a class="cta cta-main" href="{p}comparateur.html#c={sel_state(sel)}">Affiner avec mes critères</a>'
                + ('<small>Le comparateur reprend ces critères, sans le filtre propre à cette page.</small>' if sel.get('filt') and not sel.get('aid') else '') + '</div></div>'
                f'<ol class="sel-list">{"".join(items)}</ol>'
                f'<p class="small">Prix « à partir de » de la version citée, tarifs constructeurs ; malus 2026 estimé. Données mises à jour le {day}.</p>'
                f'<section class="sel-more"><h2 class="sec-title">Autres sélections</h2><ul>{others}</ul></section></div>')
        write(rel, head(f"{sel['t']} | Mioto", desc, rel, p) + hero_small(p, 'selections.html', 'Sélection', _nb(esc(sel['t'])), f'Classement mis à jour le {day}') + body + foot(p))
        w0 = top[0][1]
        cards.append(f'<a class="sel-card" href="selections/{sel["slug"]}.html"><b>{_nb(esc(sel["short"]))}</b>'
                     f'<span>N° 1 : {flag(w0["b"])} {esc(w0["b"])} {esc(w0["m"])}</span><small>{_pl(len(L), "modèle")} en lice</small></a>')
    page = (head('Sélections : les meilleures voitures neuves par catégorie | Mioto',
                 "Citadines électriques, SUV hybrides, familiales, 7 places, voitures sans malus… Les meilleures voitures neuves par catégorie selon la note Mioto.", 'selections.html', '')
            + hero_small('', 'selections.html', 'Sélections', 'Les meilleures <span>par catégorie</span>',
                         "Des classements prêts à l'emploi, calculés par le même moteur que le comparateur et mis à jour chaque jour.")
            + f'<div class="wrap page"><div class="sel-grid">{"".join(cards)}</div><p class="small">Envie d\'un classement sur mesure ? '
              f'<a href="comparateur.html">Lancez le comparateur</a> avec vos propres critères.</p></div>' + foot(''))
    write('selections.html', page)
    return [f"selections/{x['slug']}.html" for x in SELECTIONS]

def main():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, 'assets'), os.path.join(OUT, 'assets'))
    shutil.copy(os.path.join(ROOT, 'assets', 'favicon.ico'), os.path.join(OUT, 'favicon.ico'))
    build_index()
    build_face()
    build_home()
    for (b, m), l in MODELS.items(): build_model(b, m, l)
    build_brands()
    sel_urls = build_selections()
    n = len(MODELS)
    build_text('methode.html', 'Méthode', 'Notre <span>méthode</span>', 'Comment ça marche', "Comment Mioto calcule la note sur 100, d'où viennent les données et comment sont rédigés les avis.",
               METHODE.replace('__N_MODELS__', str(n)).replace('__N_VERSIONS__', fmt(len(CARS))))
    build_text('mentions-legales.html', 'Mentions légales', 'Mentions <span>légales</span>', 'Informations', 'Mentions légales et données personnelles du site Mioto.', LEGAL)
    p4 = SITE_URL or ''
    write('404.html', head('Page introuvable | Mioto', "Cette page n'existe pas ou plus.", '404.html', p4) + hero_small(p4, '', 'Erreur 404', 'Page <span>introuvable</span>', '')
          + f'<div class="wrap page prose"><p>Ce modèle n\'est peut-être plus commercialisé, ou l\'adresse a changé.</p><p><a href="{p4}index.html">Retour à l\'accueil</a> · <a href="{p4}comparateur.html">Comparateur</a> · <a href="{p4}marques.html">Tous les modèles</a></p></div>' + foot(p4))
    urls = ['', 'comparateur.html', 'face-a-face.html', 'marques.html', 'selections.html', 'methode.html', 'mentions-legales.html'] + sel_urls + [f'modeles/{mslug(b, m)}.html' for b, m in MODELS]
    if SITE_URL:
        write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
              ''.join(f'  <url><loc>{SITE_URL}{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>\n' for u in urls) + '</urlset>\n')
        write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n')
    else:
        write('robots.txt', 'User-agent: *\nAllow: /\n')
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    print(f'{len(urls)} pages générées dans {OUT} ({len(CARS)} versions, {n} modèles)')

if __name__ == '__main__':
    main()

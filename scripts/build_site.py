"""Génère le site statique « Mon Auto Idéale » dans dist/.

Usage : python3 scripts/build_site.py [dossier_sortie]
Entrées : data/data.json (versions), data/avis.json (avis par modèle), data/meta.json (pays, drapeaux,
sites constructeurs, liste des modèles éligibles aux aides, silhouettes), src/index.body.html, assets/.
Variable d'environnement SITE_URL (ex. https://pseudo.github.io/mon-auto-ideale/) pour les liens absolus.
"""
import json, math, os, re, shutil, sys, unicodedata, html, datetime

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
FAVICON = ("data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230B5D44'/%3E"
           "%3Cpath d='M6 20 L9 14 Q10 12 13 12 H19 Q22 12 23.5 14 L26 18 V22 H6Z' fill='%23F2C230'/%3E%3Ccircle cx='11' cy='22' r='3' fill='%23fff'/%3E%3Ccircle cx='21' cy='22' r='3' fill='%23fff'/%3E%3C/svg%3E")
def nav(p, cur):
    items = [('index.html', 'Accueil'), ('comparateur.html', 'Comparateur'), ('marques.html', 'Marques et modèles'), ('methode.html', 'Méthode')]
    links = ''.join(f'<a href="{p}{h}"{" aria-current=\"page\"" if h == cur else ""}>{t}</a>' for h, t in items)
    return f'<nav class="topnav" aria-label="Navigation principale"><a class="logo" href="{p}index.html">Mon Auto <b>Idéale</b></a><div class="topnav-links">{links}</div></nav>'
def head(title, desc, path, p, extra=''):
    canon = f'<link rel="canonical" href="{SITE_URL}{path}">\n<meta property="og:url" content="{SITE_URL}{path}">' if SITE_URL else ''
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
<meta property="og:locale" content="fr_FR">
{canon}
<meta name="theme-color" content="#0B3D2E">
<link rel="icon" href="{FAVICON}">
<link rel="preload" href="{p}assets/fonts/outfit-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{p}assets/site.css">
{extra}
</head>
<body>
'''
def foot(p):
    return f'''<footer class="site-foot"><div class="wrap">
  <p><b>Mon Auto Idéale</b> — comparateur indépendant de voitures neuves vendues en France. Données mises à jour le {TODAY.strftime('%d/%m/%Y')}.</p>
  <p><a href="{p}index.html">Accueil</a> · <a href="{p}comparateur.html">Comparateur</a> · <a href="{p}marques.html">Marques et modèles</a> · <a href="{p}methode.html">Méthode</a> · <a href="{p}mentions-legales.html">Mentions légales</a></p>
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
    write('comparateur.html', head('Le comparateur | Mon Auto Idéale', desc, 'comparateur.html', '') + body + '\n' + foot(''))


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
        sc = _at_most(v, t, .15, .4)
        why = f'{eur(t - v)} sous le budget, bonus' if sc > .805 else ('Tout juste dans le budget' if v <= t else f'{eur(v - t)} au-dessus du budget, la note chute')
        return 'Budget', f'{eur(t)} maximum', eur(v), sc, why
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
    desc = f"Mon Auto Idéale classe les voitures neuves vendues en France selon vos propres critères : une note sur 100 pour chacune des {fmt(len(CARS))} versions de {n_models} modèles, avec fiches et avis."
    body = f'''<header class="hero home-hero">
  {nav(p, 'index.html')}
  <div class="home-in">
    <div class="kicker">Comparateur indépendant de voitures neuves</div>
    <h1>Mon Auto <span>Idéale</span></h1>
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
    write('index.html', head('Mon Auto Idéale — trouvez la voiture neuve qui vous correspond', desc, '', p) + body + foot(p))

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
def conso(c):
    if c['e'] == 'ev': return f"{c['aut']}{NB}km · {fmt(c['kwh'],1)}{NB}kWh" if c.get('aut') and c.get('kwh') else (f"{c['aut']}{NB}km" if c.get('aut') else '—')
    s = f"{fmt(c['l'],1)}{NB}L" if c.get('l') is not None else '—'
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
    rows = ''.join(f'''<tr><th scope="row">{esc(c['v'])}</th><td>{esc(ENERGY[c['e']])}</td><td class="num">{c.get('hp','—')}{NB}ch</td><td>{esc(c.get('bxl') or '')}</td><td>{esc(TR.get(c.get('tr'), c.get('tr') or ''))}</td><td class="num">{conso(c)}</td><td class="num">{c.get('co2','—')}</td><td class="num">{c.get('tk','—')}</td><td class="num pr">{eur(c.get('p'))}{' <span class="aidt">aides</span>' if eligible(c) else ''}</td></tr>''' for c in l)
    def span(vals, unit='', d=0):
        return rng(vals, unit, d)
    dl = [('Carrosserie', esc(c0['c'])), ('Motorisations', esc(' · '.join(en))), ('Places', esc(' ou '.join(sorted({str(c.get('pl')) for c in l if c.get('pl')})))),
          ('Portes', esc(' ou '.join(sorted({str(c.get('dr')) for c in l if c.get('dr')})))), ('Longueur', span([c.get('len') for c in l], 'm', 2)),
          ('Poids à vide', span([c.get('w') for c in l], 'kg')), ('0 à 100 km/h', span([c.get('acc') for c in l], 's', 1)),
          ("Crit'Air", esc(' ou '.join(sorted({str(c.get('ca')) for c in l if c.get('ca') is not None})) or '—')),
          ('Commercialisé depuis', esc(str(min(c['y'] for c in l if c.get('y'))) if any(c.get('y') for c in l) else '—')),
          ('Marque', f"{flag(b)} {esc(b)} · {esc(ADJ.get(NATION.get(b, ''), ''))}")]
    if ev: dl.insert(5, ('Recharge rapide max.', span([c.get('kw') for c in ev], 'kW')))
    sims = similar(b, m, l)
    desc = (AVIS.get(f'{b}|{m}') or AVIS.get(f'{b}|{m}|ev') or {}).get('v') or f'{name} : prix, versions, autonomie, consommation et caractéristiques.'
    pm = pmin(l)
    title = f'{name} : prix, versions et avis' + (f' (dès {fmt(pm)} €)' if pm else '') + ' | Mon Auto Idéale'
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
      <div class="acts2">{f'<a class="site-btn" href="{esc(site)}" target="_blank" rel="noopener">Voir sur le site {esc("DS" if b == "DS Automobiles" else b)}</a>' if site else ''}<a class="fiche-link" href="{p}comparateur.html">Comparer avec mes critères</a></div>
    </div>
    {f'<div class="bdgs">{"".join(badges)}</div>' if badges else ''}
    <div class="tiles">{''.join(tiles)}</div>
  </section>
  {avis_html(b, m)}
  <section class="card"><h2>Les {len(l)} version{'s' if len(l) > 1 else ''}</h2>
    <div class="vt-wrap"><table class="vtable"><thead><tr><th scope="col">Version</th><th scope="col">Énergie</th><th scope="col">Puissance</th><th scope="col">Boîte</th><th scope="col">Transmission</th><th scope="col">Conso. / autonomie</th><th scope="col">CO₂ (g/km)</th><th scope="col">Coffre (L)</th><th scope="col">Prix dès</th></tr></thead><tbody>{rows}</tbody></table></div>
    <p class="small">Consommation et autonomie : valeurs minimales annoncées par le constructeur en cycle WLTP mixte. Prix « à partir de » de la finition d'entrée pour chaque motorisation.</p>
  </section>
  <section class="card"><h2>Caractéristiques</h2><dl class="specs">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in dl)}</dl></section>
  {f'<section><h2 class="sec-title">À comparer aussi</h2><div class="mgrid">{"".join(mini_card(bb, mm, ll, p) for _, bb, mm, ll in sims)}</div></section>' if sims else ''}
</div>
''' + foot(p)
    write(f'modeles/{mslug(b, m)}.html', page)

# --- marques -------------------------------------------------------------------------
def build_brands():
    p = ''; brands = sorted({b for b, _ in MODELS}, key=lambda s: slug(s))
    jump = ''.join(f'<a href="#{slug(b)}">{flag(b)} {esc(b)}</a>' for b in brands)
    secs = ''
    for b in brands:
        ms = sorted([(mm, ll) for (bb, mm), ll in MODELS.items() if bb == b], key=lambda x: pmin(x[1]) or 10**9)
        secs += f'''<section class="brand-sec" id="{slug(b)}"><h2>{flag(b, 'flag-lg')} {esc(b)} <small>{len(ms)} modèle{'s' if len(ms) > 1 else ''} · marque {esc(ADJ.get(NATION.get(b, ''), ''))}</small></h2><div class="mgrid">{''.join(mini_card(b, mm, ll, p) for mm, ll in ms)}</div></section>'''
    n = len(MODELS)
    page = head('Toutes les marques et tous les modèles | Mon Auto Idéale', f'Les {n} modèles de voitures neuves de {len(brands)} marques vendues en France, avec prix, versions et avis.', 'marques.html', p) \
        + hero_small(p, 'marques.html', 'Catalogue', 'Marques <span>et modèles</span>', f'{n} modèles de {len(brands)} marques, classés par prix d\'entrée.') \
        + f'<div class="wrap page"><nav class="jump" aria-label="Aller à une marque">{jump}</nav>{secs}</div>' + foot(p)
    write('marques.html', page)

# --- pages de texte ---------------------------------------------------------------
def build_text(rel, title, h1, kicker, desc, content):
    p = ''
    write(rel, head(f'{title} | Mon Auto Idéale', desc, rel, p) + hero_small(p, rel, kicker, h1, '') + f'<div class="wrap page prose">{content}</div>' + foot(p))

METHODE = open(os.path.join(ROOT, 'src/methode.html'), encoding='utf-8').read()
LEGAL = open(os.path.join(ROOT, 'src/mentions-legales.html'), encoding='utf-8').read()

def main():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, 'assets'), os.path.join(OUT, 'assets'))
    build_index()
    build_home()
    for (b, m), l in MODELS.items(): build_model(b, m, l)
    build_brands()
    n = len(MODELS)
    build_text('methode.html', 'Méthode', 'Notre <span>méthode</span>', 'Comment ça marche', "Comment Mon Auto Idéale calcule la note sur 100, d'où viennent les données et comment sont rédigés les avis.",
               METHODE.replace('__N_MODELS__', str(n)).replace('__N_VERSIONS__', fmt(len(CARS))))
    build_text('mentions-legales.html', 'Mentions légales', 'Mentions <span>légales</span>', 'Informations', 'Mentions légales et données personnelles du site Mon Auto Idéale.', LEGAL)
    p4 = SITE_URL or ''
    write('404.html', head('Page introuvable | Mon Auto Idéale', "Cette page n'existe pas ou plus.", '404.html', p4) + hero_small(p4, '', 'Erreur 404', 'Page <span>introuvable</span>', '')
          + f'<div class="wrap page prose"><p>Ce modèle n\'est peut-être plus commercialisé, ou l\'adresse a changé.</p><p><a href="{p4}index.html">Retour à l\'accueil</a> · <a href="{p4}comparateur.html">Comparateur</a> · <a href="{p4}marques.html">Tous les modèles</a></p></div>' + foot(p4))
    urls = ['', 'comparateur.html', 'marques.html', 'methode.html', 'mentions-legales.html'] + [f'modeles/{mslug(b, m)}.html' for b, m in MODELS]
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

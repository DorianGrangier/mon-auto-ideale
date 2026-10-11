"""Contrôles avant publication : compare les nouvelles données à celles déjà en ligne.
Usage : python3 scripts/check_data.py <ancien data.json> <nouveau data.json>
Code de sortie 1 (publication bloquée) si un contrôle bloquant échoue.
Le rapport est aussi écrit dans $GITHUB_STEP_SUMMARY quand il existe."""
import json, sys, os
old = json.load(open(sys.argv[1], encoding='utf-8')) if os.path.exists(sys.argv[1]) else []
new = json.load(open(sys.argv[2], encoding='utf-8'))
avis = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'avis.json'), encoding='utf-8'))
block, warn, info = [], [], []

def models(d): return {(c['b'], c['m']) for c in d}
if len(new) < 300: block.append(f'Seulement {len(new)} versions (minimum 300).')
if old and len(new) < 0.85 * len(old): block.append(f'Le nombre de versions chute de {len(old)} à {len(new)} (plus de 15 %).')
if old and len(models(new)) < 0.9 * len(models(old)): block.append(f'Le nombre de modèles chute de {len(models(old))} à {len(models(new))} (plus de 10 %).')
nop = sum(1 for c in new if not c.get('p'))
if nop > 0.05 * len(new): block.append(f'{nop} versions sans prix (plus de 5 %).')

RULES = [('hp', 40, 1300, 'puissance (ch)'), ('p', 8000, 500000, 'prix (€)'), ('w', 700, 3600, 'poids (kg)'),
         ('tk', 80, 1000, 'coffre (L)'), ('len', 2.4, 6.0, 'longueur (m)')]
def anomalies(d):
    out = set()
    for c in d:
        k = (c['b'], c['m'], c['v'])
        for f, lo, hi, lab in RULES:
            v = c.get(f)
            if v is not None and not (lo <= v <= hi): out.add((k, f'{lab} = {v}'))
        if c['e'] == 'ev' and c.get('aut') is not None and not (80 <= c['aut'] <= 1100): out.add((k, f"autonomie = {c['aut']} km"))
        if c['e'] not in ('ev',) and c.get('l') is not None and not (0.3 <= c['l'] <= 20): out.add((k, f"consommation = {c['l']} L/100"))
        if c['e'] == 'ev' and c.get('l') is not None: out.add((k, 'électrique avec une consommation de carburant'))
    return out
newan = anomalies(new) - anomalies(old)
for (k, msg) in sorted(newan): block.append(f'{k[0]} {k[1]} « {k[2]} » : {msg}')

om, nm = models(old), models(new)
for b, m in sorted(nm - om): info.append(f'Nouveau modèle : {b} {m}')
for b, m in sorted(om - nm): info.append(f'Modèle retiré : {b} {m}')
info.append(f'{len(new)} versions, {len(nm)} modèles (avant : {len(old)} versions, {len(om)} modèles).')
for b, m in sorted(nm):
    if f'{b}|{m}' not in avis and f'{b}|{m}|ev' not in avis: warn.append(f"Pas encore d'avis pour {b} {m}")

rep = ['## Contrôle des données', '']
rep += ['### Bloquant (le site n\'est pas mis à jour)'] + [f'- {x}' for x in block] + [''] if block else ['Aucun problème bloquant.', '']
if warn: rep += ['### À compléter'] + [f'- {x}' for x in warn] + ['']
rep += ['### Changements'] + [f'- {x}' for x in info]
txt = '\n'.join(rep); print(txt)
if os.environ.get('GITHUB_STEP_SUMMARY'):
    open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8').write(txt + '\n')
sys.exit(1 if block else 0)

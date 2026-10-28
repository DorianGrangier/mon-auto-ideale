import json, sys, csv
# Conversion de la feuille « Auto » (Google Sheets) en données du site.
# Usage : python3 scripts/build_data.py <feuille.csv | export.json | fichier.xlsx> <sortie.json>
SRC=sys.argv[1]; OUT=sys.argv[2]
if SRC.endswith('.xlsx'):
    import openpyxl
    wb=openpyxl.load_workbook(SRC,data_only=True); ws=wb.active
    raw=list(ws.iter_rows(values_only=True))
elif SRC.endswith('.csv'):
    with open(SRC,newline='',encoding='utf-8') as f: raw=list(csv.reader(f))
else:
    raw=json.load(open(SRC))['values']
# Colonnes facultatives après « Prix min. » : « Photo » (adresse de l'image) et « Crédit photo »
HDR=[str(h or '').strip().lower() for h in raw[0]]
def col(*names):
    for i,h in enumerate(HDR):
        if any(h.startswith(n) for n in names): return i
    return None
IPH, ICR = col('photo'), col('crédit photo','credit photo','crédit')
PHOTOS_SRC={}
for r in raw[1:]:
    if len(r)>2 and r[1] and IPH is not None and len(r)>IPH and str(r[IPH] or '').strip().startswith('http'):
        b=str(r[1]).strip(); b={'Mercedes':'Mercedes-Benz','Mercedes Benz':'Mercedes-Benz','DS':'DS Automobiles','Citroen':'Citroën'}.get(b,b)
        k=b+'|'+str(r[2]).strip()
        if k not in PHOTOS_SRC:
            cr=str(r[ICR]).strip() if ICR is not None and len(r)>ICR and r[ICR] else ''
            PHOTOS_SRC[k]={'url':str(r[IPH]).strip(),'credit':(cr if cr.startswith('©') else '© '+cr) if cr else '© '+b}
# Colonnes repérées par leur titre : l'ordre des colonnes dans la feuille peut changer sans casser le site.
CANON=['Nation','Constructeur','Modèle','Génération','Phase','Nom motorisation','Carrosserie','Début','Fin','Portes','Places',
 'Motorisation','Architecture moteur','Cylindrée (L)','Puissance max. (ch)','Couple max. (Nm)','0-100 km/h min. (s)',
 'Conso. WLTP min. (L/100km)','Émi. CO2 WLTP min. (g/km)','Classe énergétique','Conso. WLTP min (kWh/100km)',
 'Auto. élec. WLTP mixte (km)','Capacité batterie (kWh)','Type de recharge','Pui. charge max. (kW)','Boîte','Trans.',
 'Poids à vide','Longueur (m)','Largeur (m)','Hauteur (m)','Volume coffre arrière min. (L)','Étoiles EuroNCAP',"Crit'Air",'Prix min.']
def _k(h): return ' '.join(str(h or '').lower().replace('’',"'").split())
_pos={_k(h):i for i,h in enumerate(raw[0])}
IDX=[]
for h in CANON:
    i=_pos.get(_k(h))
    if i is None:  # titre légèrement modifié : on cherche un début commun
        i=next((j for k,j in _pos.items() if k.startswith(_k(h)[:12])),None)
    assert i is not None, f'Colonne introuvable dans la feuille : « {h} »'
    IDX.append(i)
# Colonnes facultatives (critères à venir) : temps de recharge 10-80 % et coffre avant
def _opt(prefix):
    return next((j for k,j in _pos.items() if k.startswith(prefix)), None)
IDX += [_opt('temps recharge'), _opt("présence d'un coffre"), _opt('lien'), _opt('version 7')]  # « Version 7 places ? » : troisième rangée proposée (en série ou en option)
raw=[tuple((list(r)[i] if i is not None and i<len(r) else None) for i in IDX) for r in raw]
rows=[r for r in raw[1:] if r[1]]
ALIAS={'Mercedes':'Mercedes-Benz','Mercedes Benz':'Mercedes-Benz','DS':'DS Automobiles','Citroen':'Citroën'}
rows=[tuple([r[0],ALIAS.get(str(r[1]).strip(),str(r[1]).strip())]+list(r[2:])) for r in rows]
rows=[r for r in rows if 'Quadricycle' not in str(r[6])]  # Citroën Ami, Fiat Topolino exclus
# Même modèle écrit avec ou sans accent (« Serie 3 » / « Série 3 ») : on garde l'orthographe la plus fréquente,
# sinon les deux fiches auraient la même adresse et l'une écraserait l'autre.
import unicodedata, collections
def _norm(s): return ''.join(ch for ch in unicodedata.normalize('NFD', str(s).strip().lower()) if unicodedata.category(ch) != 'Mn')
_seen=collections.defaultdict(collections.Counter)
for r in rows: _seen[(r[1], _norm(r[2]))][str(r[2]).strip()]+=1
_canon={k: max(c, key=lambda n: (c[n], n != _norm(n))) for k, c in _seen.items()}
for k, c in _seen.items():
    if len(c) > 1: print('  orthographes unifiées :', k[0], dict(c), '→', _canon[k])
rows=[tuple([r[0], r[1], _canon[(r[1], _norm(r[2]))]] + list(r[3:])) for r in rows]
def num(v):
    if v is None: return None
    if isinstance(v,(int,float)): return v
    s=str(v).replace('\u202f','').replace('\xa0','').replace('€','').replace(' ','').strip().replace(',','.')
    if s in ('-','?',''): return None
    try: return float(s)
    except: return None
def s_(v):
    if isinstance(v,float) and v.is_integer(): return str(int(v))
    s=str(v).strip()
    try:
        f=float(s)
        if f.is_integer() and '.' in s: return str(int(f))
    except: pass
    return s
def i_(v):
    n=num(v); return None if n is None else (int(n) if float(n).is_integer() else n)
def _yn(v):
    v=str(v or '').strip().lower()
    return 1 if v in ('oui','yes','o','x','1','vrai','true') else (0 if v in ('non','no','n','0','faux','false') else None)
EN={'Essence':'ess','Essence + Hy. légère':'essm','Diesel':'die','Diesel + Hy. légère':'diem',
    'Hybride simple':'hev','PHEV':'phev','Électrique':'ev','Essence + GPL':'gpl','Essence + GPL + Hy. légère':'gpl','Hydrogène':'h2'}
def energie(v):
    # libellé connu, sinon déduit des mots du libellé (un nouveau libellé dans la feuille ne bloque plus la mise à jour)
    v=str(v or '').strip()
    if v in EN: return EN[v]
    t=v.lower(); leg='légère' in t or 'legere' in t
    for cle,code in (('gpl','gpl'),('hydrog','h2'),('phev','phev'),('rechargeable','phev'),('électrique','ev'),('electrique','ev'),('hybride simple','hev'),('full hybrid','hev')):
        if cle in t: print(f'  motorisation « {v} » lue comme {code}'); return code
    if 'diesel' in t: print(f'  motorisation « {v} » lue comme diesel'); return 'diem' if leg else 'die'
    if 'essence' in t: print(f'  motorisation « {v} » lue comme essence'); return 'essm' if leg else 'ess'
    raise SystemExit(f'Motorisation inconnue dans la feuille : « {v} »')
out=[]
for r in rows:
    tags=[t.strip() for t in str(r[6]).split(',')]
    # SUV urbain et crossover regroupés ; les grands crossovers (> 4,45 m) sont classés en SUV, comme les vendent les constructeurs
    L_=num(r[28]); nt=[]
    for x in tags:
        if x.lower()=='suv urbain': x='SUV urbain'
        elif x=='Crossover': x='SUV urbain' if (L_ is None or L_<=4.45) else 'SUV'
        if x not in nt: nt.append(x)
    tags=nt
    box=str(r[25])
    out.append({
     'b':s_(r[1]),'m':s_(r[2]),'g':i_(r[3]),'v':s_(r[5]),'c':', '.join(tags),
     'y':i_(r[7]),'end':i_(r[8]),'dr':i_(r[9]),'pl':i_(r[10]),'e':energie(r[11]),'eng':s_(r[12]),
     'hp':i_(r[14]),'nm':i_(r[15]),'acc':num(r[16]),'l':num(r[17]),'co2':i_(r[18]),'cls':r[19],
     'kwh':num(r[20]),'aut':i_(r[21]),'bat':num(r[22]),'rt':None if r[23] in ('-',None) else r[23],
     'kw':num(r[24]),'bx':'A' if box=='BVA' else 'M','bxl':box,'tr':r[26],'w':i_(r[27]),
     'len':num(r[28]),'tk':i_(r[31]),'nc':i_(r[32]),'ca':i_(r[33]),'p':i_(r[34]),'t80':num(r[35]),'fk':_yn(r[36]),'u':(str(r[37]).strip() if r[37] and str(r[37]).strip().startswith('http') else None),
     's7':_yn(r[38]) or None})
# garde-fou : des noms de version purement numériques signalent une colonne mal lue
_num=sum(1 for d in out if str(d.get('v','')).replace('.','').isdigit())
assert _num < len(out)*0.05, f'{_num} noms de version purement numériques : colonne « Nom motorisation » mal lue ?'
# strip None keys to save space
out=[{k:v for k,v in d.items() if v is not None} for d in out]
json.dump(out,open(OUT,'w'),ensure_ascii=False,separators=(',',':'))
import os
json.dump(PHOTOS_SRC,open(os.path.join(os.path.dirname(os.path.abspath(OUT)),'photos_src.json'),'w'),ensure_ascii=False,indent=1)
print(len(out), len(json.dumps(out,ensure_ascii=False,separators=(',',':')))//1024,'KB')

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
raw=[tuple(list(r)+[None]*(35-len(r)))[:35] for r in raw]
assert raw[0][1]=='Constructeur' and raw[0][34]=='Prix min.', 'Colonnes inattendues : '+str(raw[0])
rows=[r for r in raw[1:] if r[1]]
ALIAS={'Mercedes':'Mercedes-Benz','Mercedes Benz':'Mercedes-Benz','DS':'DS Automobiles','Citroen':'Citroën'}
rows=[tuple([r[0],ALIAS.get(str(r[1]).strip(),str(r[1]).strip())]+list(r[2:])) for r in rows]
rows=[r for r in rows if 'Quadricycle' not in str(r[6])]  # Citroën Ami, Fiat Topolino exclus
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
EN={'Essence':'ess','Essence + Hy. légère':'essm','Diesel':'die','Diesel + Hy. légère':'diem',
    'Hybride simple':'hev','PHEV':'phev','Électrique':'ev','Essence + GPL':'gpl','Hydrogène':'h2'}
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
     'y':i_(r[7]),'end':i_(r[8]),'dr':i_(r[9]),'pl':i_(r[10]),'e':EN[r[11]],'eng':s_(r[12]),
     'hp':i_(r[14]),'nm':i_(r[15]),'acc':num(r[16]),'l':num(r[17]),'co2':i_(r[18]),'cls':r[19],
     'kwh':num(r[20]),'aut':i_(r[21]),'bat':num(r[22]),'rt':None if r[23] in ('-',None) else r[23],
     'kw':num(r[24]),'bx':'A' if box=='BVA' else 'M','bxl':box,'tr':r[26],'w':i_(r[27]),
     'len':num(r[28]),'tk':i_(r[31]),'nc':i_(r[32]),'ca':i_(r[33]),'p':i_(r[34])})
# strip None keys to save space
out=[{k:v for k,v in d.items() if v is not None} for d in out]
json.dump(out,open(OUT,'w'),ensure_ascii=False,separators=(',',':'))
import os
json.dump(PHOTOS_SRC,open(os.path.join(os.path.dirname(os.path.abspath(OUT)),'photos_src.json'),'w'),ensure_ascii=False,indent=1)
print(len(out), len(json.dumps(out,ensure_ascii=False,separators=(',',':')))//1024,'KB')

"""Traductions anglaises partagées par build_site.py (pages en/) : libellés de données et noms de versions.

Les données restent en français (clés de la feuille) ; seules les valeurs affichées sont traduites.
La même règle de traduction des noms de versions existe en JavaScript (VNAME_EN dans src/index.body.html).
"""
import re

ENERGY = {'ess': 'Petrol', 'essm': 'Petrol mild hybrid', 'die': 'Diesel', 'diem': 'Diesel mild hybrid', 'hev': 'Hybrid',
          'phev': 'Plug-in hybrid', 'ev': 'Electric', 'gpl': 'Petrol + LPG', 'h2': 'Hydrogen'}
TR = {'FWD': 'Front-wheel drive', 'RWD': 'Rear-wheel drive', 'AWD': 'All-wheel drive'}
TR_SHORT = {'FWD': 'FWD', 'RWD': 'RWD', 'AWD': 'AWD'}
BODY = {'Citadine': 'City car', 'Compacte': 'Hatchback', 'Berline': 'Saloon', 'Break': 'Estate', 'Monospace': 'MPV',
        'SUV urbain': 'Small SUV', 'SUV': 'SUV', 'Tout-terrain': 'Off-roader', 'Coupé': 'Coupé', 'Cabriolet': 'Convertible',
        'Roadster': 'Roadster', 'Limousine': 'Limousine', 'Sportive': 'Sports car'}
BODY_PL = {'Citadine': 'City cars', 'Compacte': 'Hatchbacks', 'Berline': 'Saloons', 'Break': 'Estates', 'Monospace': 'MPVs',
           'SUV urbain': 'Small SUVs', 'SUV': 'SUVs', 'Tout-terrain': 'Off-roaders', 'Coupé': 'Coupés', 'Cabriolet': 'Convertibles and roadsters'}
NATION = {'Allemagne': 'Germany', 'Chine': 'China', 'Corée du Sud': 'South Korea', 'Espagne': 'Spain', 'France': 'France',
          'Italie': 'Italy', 'Japon': 'Japan', 'Roumanie': 'Romania', 'Royaume-Uni': 'United Kingdom',
          'République tchèque': 'Czech Republic', 'Suède': 'Sweden', 'États-Unis': 'United States'}
ADJ = {'Allemagne': 'German', 'Chine': 'Chinese', 'Corée du Sud': 'South Korean', 'Espagne': 'Spanish', 'France': 'French',
       'Italie': 'Italian', 'Japon': 'Japanese', 'Roumanie': 'Romanian', 'Royaume-Uni': 'British',
       'République tchèque': 'Czech', 'Suède': 'Swedish', 'États-Unis': 'American'}

def body_en(s):
    """« SUV, Coupé » → « SUV, Coupé » en anglais, tag par tag."""
    return ', '.join(BODY.get(t, t) for t in s.split(', '))

_VN = [
    (r'\bHybride [Rr]echargeable\b', 'Plug-in Hybrid'),
    (r'\bPlug-In Hybride\b', 'Plug-in Hybrid'),
    (r'\bMicro-hybride\b', 'Mild Hybrid'),
    (r'\b[Hh]ybride\b', 'Hybrid'),
    (r'Électrique', 'Electric'),
    (r'Hydrogène', 'Hydrogen'),
    (r'\bEssence\b', 'Petrol'),
    (r'\bBatterie\b', 'Battery'),
    (r'\bAutonomie [Ll]ongue\b', 'Long Range'),
    (r'\bGrande [Aa]utonomie\b', 'Long Range'),
    (r'\bAutonomie [Ss]tandard\b', 'Standard Range'),
    (r'\bAutonomie étendue\b', 'Extended Range'),
    (r'\bAutonomie confort\b', 'Comfort Range'),
    (r'\bAutonomie urbaine\b', 'Urban Range'),
    (r'\bPropulsion\b', 'RWD'),
    (r'\bEmpattement [Ll]ong\b', 'Long Wheelbase'),
    (r'\bEmpattement [Cc]ourt\b', 'Short Wheelbase'),
    (r'\bBVM\d*\b', 'Manual'),
    (r'\bBVA\d*\b', 'Auto'),
    (r'(\d),(\d)', r'\1.\2'),
    (r'(\d) ?ch\b', r'\1 hp'),
    (r'  +', ' '),
]
def vname_en(v):
    """Nom de version affiché sur le site anglais (le nom français reste la clé)."""
    for a, b in _VN: v = re.sub(a, b, v)
    return v.strip()

if __name__ == '__main__':
    import json, sys
    for line in sys.stdin: print(vname_en(line.rstrip('\n')))

# --- comparateur et face à face : remplacements appliqués au HTML/JS pour les pages anglaises --------------------------------
# Chaque paire (texte français exact, texte anglais) ; appliquées dans l'ordre, sur toutes les occurrences.
# Les clés de données (carrosseries, motorisations, versions) ne sont jamais remplacées : elles sont traduites à l'affichage
# par META.BODY_LBL, META.VN et META.ADJ, injectés par build_site.py.
VN_JS = [[a.replace('(?i)', ''), 'g', b.replace('\\1', '$1').replace('\\2', '$2')] for a, b in _VN]

JS_EN = [
 # liens et chemins
 ('aria-label="Retirer le modèle ${i+1}">', 'aria-label="Remove model ${i+1}">'), 
 ("href=\"methode.html\"", "href=\"method.html\""), ("href=\"marques.html\"", "href=\"brands.html\""),
 ("href=\"face-a-face.html#f=", "href=\"head-to-head.html#f="), ("'modeles/'+slug", "'models/'+slug"),
 ("const PHOTO_BASE = 'assets/photos/';", "const PHOTO_BASE = '../assets/photos/';"),
 # en-tête et panneau
 ('<div class="kicker">Le comparateur</div>', '<div class="kicker">Compare</div>'),
 ('<h1>Trouvez votre <span>voiture idéale</span></h1>', '<h1>Find your <span>ideal car</span></h1>'),
 ("Activez les critères qui comptent pour vous et choisissez leur importance : chaque version reçoit une note sur 100.", "Switch on the criteria that matter to you and set how important each one is: every version gets a score out of 100."),
 ('Comment est calculée la note&nbsp;?', 'How is the score calculated?'),
 ('aria-label="Critères de recherche"', 'aria-label="Search criteria"'), ('<h2>Vos critères</h2>', '<h2>Your criteria</h2>'),
 ('id="btn-example">Exemple</button>', 'id="btn-example">Example</button>'), ('id="btn-reset">Tout effacer</button>', 'id="btn-reset">Clear all</button>'),
 ('Voir les résultats</button>', 'See results</button>'),
 ("Exemple pré-rempli : citadine électrique de 150 à 200&nbsp;ch, au moins 400&nbsp;km d'autonomie et recharge rapide, à moins de 32&nbsp;000&nbsp;€. Modifiez librement les critères.",
  "Pre-filled example: an electric city car with 150 to 200&nbsp;hp, at least 400&nbsp;km of range and fast charging, for under €32,000. Feel free to change the criteria."),
 ('<h2>Sur le podium</h2>', '<h2>On the podium</h2>'), ('<h2 id="list-title">Classement</h2>', '<h2 id="list-title">Ranking</h2>'),
 (' Une version par modèle</label>', ' One version per model</label>'),
 (' Masquer les voitures qui ratent un critère impératif</label>', ' Hide cars that miss an essential criterion</label>'),
 ('Afficher 20 de plus', 'Show 20 more'), ('Nouvelle recherche</button>', 'New search</button>'),
 ('<summary>Sources et méthode de calcul</summary>', '<summary>Sources and how the score works</summary>'),
 ('>Lire la méthode complète</a>', '>Read the full method</a>'), ('>Toutes les marques et tous les modèles</a>', '>All brands and models</a>'),
 ("Source : fichier Auto.xlsx (<span id=\"nb-marques\">les</span> marques parmi les plus vendues en France). Prix « à partir de » : tarif de la finition d'entrée de gamme pour chaque motorisation, consommation et autonomie électrique : valeurs minimales annoncées par le constructeur en cycle WLTP mixte. Coût de l'énergie : estimation à partir de la consommation WLTP, hors pertes de recharge et conduite réelle.",
  "Source: the Mioto database (<span id=\"nb-marques\">the</span> brands among the best sellers in France). “From” prices: price of the entry-level trim for each powertrain. Consumption and electric range: lowest figures announced by the manufacturer on the combined WLTP cycle. Energy cost: estimate based on WLTP consumption, excluding charging losses and real-world driving."),
 ("« Notre avis » : synthèse d'essais et d'informations publiés dans la presse spécialisée et par les constructeurs (agrément, finition, fiabilité, garantie, restylages et remplaçants annoncés), à jour en octobre 2026. Ces avis n'entrent pas dans le calcul de la note.",
  "“Our verdict”: a summary of road tests and information published by the motoring press and by manufacturers (driving, build quality, reliability, warranty, announced facelifts and successors), translated from French. These reviews are never part of the score."),
 ("« Éligible aux aides à l'achat » : voiture électrique neuve ayant atteint le score environnemental, à moins de 47&nbsp;000&nbsp;€ et 2,4&nbsp;t (prime CEE, ex-bonus écologique). Liste ADEME vérifiée le 12 octobre 2026, version par version quand elle les distingue. La prime est majorée pour les « gros rouleurs » (plus de 12 000 km par an pour le travail) depuis le 1er septembre 2026, et le leasing social 2026 retient les mêmes voitures sous 1,8 t. Vérifiez la version exacte sur le site de l'ADEME avant achat.",
  "“Eligible for purchase incentives”: new electric car that has obtained the French environmental score, under €47,000 and 2.4&nbsp;t (the CEE incentive, formerly the ecological bonus). ADEME list checked on 12 October 2026, version by version where it distinguishes them. The incentive is higher for high-mileage drivers (over 12,000 km a year for work) since 1 September 2026, and the 2026 social leasing scheme covers the same cars under 1.8 t. Check the exact version on the ADEME website before buying."),
 ("Calcul de la note : chaque critère activé reçoit une note sur 100. Pour les critères chiffrés (prix, coffre, coût de l'énergie…), atteindre tout juste votre cible donne 80 ; faire nettement mieux rapporte jusqu'à 20 points de plus, être en deçà en fait perdre. Les notes sont pondérées par l'importance choisie (secondaire ×1, important ×2, impératif ×3) puis ramenées sur 100. Au-delà du budget, la note du prix chute vite : elle tombe à 0 à 15&nbsp;% au-dessus. À note égale, la voiture la moins chère passe devant, puis celle au coût d'énergie le plus bas, à la plus grande autonomie électrique, la plus puissante, et enfin une marque française devant une marque étrangère. Une donnée non communiquée vaut 0,5.",
  "How the score works: each active criterion is scored out of 100. For numerical criteria (price, boot, energy cost…), just meeting your target earns 80; doing clearly better earns up to 20 extra points, falling short loses points. Scores are weighted by the importance you choose (secondary ×1, important ×2, essential ×3) and brought back to a score out of 100. Over budget, the price score drops fast: it reaches 0 at 15&nbsp;% over. When scores are equal, the cheaper car comes first, then the one with the lowest energy cost, the longest electric range, the most power, and finally a French brand ahead of a foreign one. A missing figure counts as 0.5."),
 ('Modifier mes critères <b id="fab-count">', 'Edit my criteria <b id="fab-count">'),
 # avis
 ('aria-label="Notre avis sur ', 'aria-label="Our verdict on '), ('>Notre avis<', '>Our verdict<'), ("'Notre avis'", "'Our verdict'"),
 ('au-delà de la fiche technique', 'beyond the spec sheet'), ('Points forts', 'Strengths'), ('Points faibles', 'Weaknesses'),
 ('<b>Pour qui ?</b>', '<b>Who is it for?</b>'), ('<b>Selon la version</b>', '<b>By version</b>'), ('<b>Bon à savoir</b>', '<b>Good to know</b>'),
 ("'Pour qui'", "'Who is it for'"), ("'Selon la version'", "'By version'"), ("'En bref'", "'In short'"),
 ('<summary>Lire notre avis complet</summary>', '<summary>Read our full verdict</summary>'),
 # malus et prix
 ('} de malus 2026<', '} 2026 malus<'), (' de malus</small>', ' malus</small>'), ("+' de malus'", "+' malus'"),
 ('Prix n.c.', 'Price n/a'), ('prix n.c.', 'price n/a'), ("'n.c.'", "'n/a'"), ("/n\\.c\\.|non testée/", "/n\\/a|not tested/"),
 ('<small class="from">À partir de</small>', '<small class="from">From</small>'), ('<small>à partir de</small>', '<small>from</small>'),
 ("'à partir de '", "'from '"), ("'à partir de\\u00a0'", "'from\\u00a0'"),
 # référentiels
 ("const ENERGY = {ess:'Essence',essm:'Essence micro-hybride',die:'Diesel',diem:'Diesel micro-hybride',hev:'Hybride',phev:'Hybride rechargeable',ev:'Électrique',gpl:'Essence + GPL',h2:'Hydrogène'};",
  "const ENERGY = {ess:'Petrol',essm:'Petrol mild hybrid',die:'Diesel',diem:'Diesel mild hybrid',hev:'Hybrid',phev:'Plug-in hybrid',ev:'Electric',gpl:'Petrol + LPG',h2:'Hydrogen'};"),
 ("const MOTO_OPTS = [['ess','Essence'],['die','Diesel'],['mhev','Hybride léger'],['hev','Hybride'],['phev','Hybride rechargeable'],['ev','Électrique'],['gpl','GPL'],['h2','Hydrogène']];",
  "const MOTO_OPTS = [['ess','Petrol'],['die','Diesel'],['mhev','Mild hybrid'],['hev','Hybrid'],['phev','Plug-in hybrid'],['ev','Electric'],['gpl','LPG'],['h2','Hydrogen']];"),
 ("const FUEL_LABEL = {sp:'SP95',go:'gazole',e85:'E85',gpl:'GPL',el:'électricité'};", "const FUEL_LABEL = {sp:'petrol',go:'diesel',e85:'E85',gpl:'LPG',el:'electricity'};"),
 ("+' + électricité'", "+' + electricity'"),
 ("const fmtCost = v=> v==null?'n/a':'≈\\u00a0'+fmt(Math.round(v/10)*10)+'\\u00a0€/an';", "const fmtCost = v=> v==null?'n/a':'≈\\u00a0€'+fmt(Math.round(v/10)*10)+'/yr';"),
 ("const AID_TXT = \"Éligible aux aides à l'achat\";", "const AID_TXT = \"Eligible for purchase incentives\";"),
 ("const TR = {FWD:'Traction',RWD:'Propulsion',AWD:'4 roues motrices'};", "const TR = {FWD:'Front-wheel drive',RWD:'Rear-wheel drive',AWD:'All-wheel drive'};"),
 ("c.pl+' ou 7 places' : c.pl+' places'", "c.pl+' or 7 seats' : c.pl+' seats'"),
 # critères
 ("name:'Nombre de places', short:'Places'", "name:'Number of seats', short:'Seats'"),
 ("name:\"Coût de l'énergie par an\", short:'Coût énergie'", "name:'Annual energy cost', short:'Energy cost'"),
 ("name:'Autonomie électrique', short:'Autonomie élec.'", "name:'Electric range', short:'Range'"),
 ("name:'Puissance de recharge', short:'Recharge'", "name:'Charging power', short:'Charging'"),
 ("name:'Boîte de vitesses', short:'Boîte'", "name:'Gearbox', short:'Gearbox'"),
 ("name:'Volume de coffre', short:'Coffre'", "name:'Boot space', short:'Boot'"),
 ("name:'Étoiles Euro NCAP', short:'Euro NCAP'", "name:'Euro NCAP stars', short:'Euro NCAP'"),
 ("[0,'sans batterie rechargeable']", "[0,'no plug-in battery']"), ("[0,'sans recharge']", "[0,'no charging']"),
 ("' · 10-80 % en '+fmt(c.t80)+' min'", "' · 10-80% in '+fmt(c.t80)+' min'"),
 ("c.bx==='A'?'Automatique':'Manuelle ('+c.bxl.replace('BVM','')+' rapports)'", "c.bx==='A'?'Automatic':'Manual ('+c.bxl.replace('BVM','')+'-speed)'"),
 ("c.bx==='A'?'Automatique':'Manuelle '+c.bxl.replace('BVM','')+' rapports'", "c.bx==='A'?'Automatic':c.bxl.replace('BVM','')+'-speed manual'"),
 ("+(c.fk?' + coffre avant':'')", "+(c.fk?' + front boot':'')"),
 ("'non testée'", "'not tested'"), ("' étoiles'", "' stars'"),
 ("const W_LABELS = [[1,'Secondaire'],[2,'Important'],[3,'Impératif']];", "const W_LABELS = [[1,'Secondary'],[2,'Important'],[3,'Essential']];"),
 ("unit:'€',la:'Prix minimum',lb:'Prix maximum'", "unit:'€',la:'Minimum price',lb:'Maximum price'"),
 ("unit:'ch',la:'Puissance minimum',lb:'Puissance maximum'", "unit:'hp',la:'Minimum power',lb:'Maximum power'"),
 ('placeholder="sans limite"', 'placeholder="no limit"'), ('(curseur)', '(slider)'),
 ('<label>De ${nb(', '<label>From ${nb('), ('<label>à ${nb(', '<label>to ${nb('),
 # aides de saisie
 ("Plusieurs choix possibles. Une motorisation proche (ex. hybride rechargeable pour « hybride ») obtient une note partielle. Choisir « Électrique » affiche les critères d'autonomie et de puissance de recharge.",
  "Several choices possible. A similar powertrain (e.g. plug-in hybrid for “hybrid”) gets a partial score. Choosing “Electric” shows the range and charging power criteria."),
 ("Plusieurs choix possibles. Une carrosserie proche (ex. SUV urbain pour « SUV ») obtient une note partielle.", "Several choices possible. A similar body style (e.g. small SUV for “SUV”) gets a partial score."),
 ("[['le5','5 places ou moins'],['gt5','Plus de 5 places']]", "[['le5','5 seats or fewer'],['gt5','More than 5 seats']]"),
 ("Avec « Plus de 5 places », seules les voitures proposées en 7 places (de série ou en option) conviennent. Avec « 5 places ou moins », une voiture uniquement 7 places reste possible (note partielle).",
  "With “More than 5 seats”, only cars available with 7 seats (as standard or as an option) qualify. With “5 seats or fewer”, a 7-seat-only car is still possible (partial score)."),
 ("'€/an'", "'€/yr'"), ("'km/an'", "'km/yr'"),
 ("Budget maximum de carburant ou d'électricité par an, selon le kilométrage et les prix ci-dessous.", "Maximum yearly budget for fuel or electricity, based on the mileage and prices below."),
 ("Autonomie WLTP mixte minimale annoncée par le constructeur. Concerne les électriques et hybrides rechargeables.", "Minimum combined WLTP range announced by the manufacturer. Applies to electric cars and plug-in hybrids."),
 ("Puissance maximale acceptée par la voiture (borne rapide DC si disponible). Le temps de recharge de 10 à 80 %, plus parlant, est affiché à côté quand il est connu ; il comptera dans la note quand il sera renseigné pour toutes les voitures.",
  "Maximum power the car accepts (DC rapid charger if available). The 10-80% charging time, more telling, is shown alongside when known; it will count in the score once it is available for every car."),
 ("De 50 à 1 000 ch, par pas de 10 ch. Poussez la poignée de droite au bout (ou videz la case) pour « sans limite ». Une voiture un peu en dehors de la fourchette obtient une note partielle.",
  "From 50 to 1,000 hp, in 10 hp steps. Push the right-hand handle to the end (or empty the box) for “no limit”. A car slightly outside the range gets a partial score."),
 ("[['A','Automatique'],['M','Manuelle']]", "[['A','Automatic'],['M','Manual']]"),
 ("[['awd','4 roues motrices'],['2wd','2 roues motrices']]", "[['awd','All-wheel drive'],['2wd','Two-wheel drive']]"),
 ("« 2 roues motrices » regroupe traction et propulsion. Une 4 roues motrices y garde une note partielle.", "“Two-wheel drive” covers front- and rear-wheel drive. An all-wheel-drive car keeps a partial score."),
 (' Avec coffre avant (frunk)</label>', ' With front boot (frunk)</label>'),
 ("Volume minimum, banquette en place. Cochez « coffre avant » pour privilégier les voitures qui en ont un sous le capot : les autres gardent une note partielle.",
  "Minimum volume, rear seats up. Tick “front boot” to favour cars that have one under the bonnet: the others keep a partial score."),
 ('aria-label="Étoiles minimum"', 'aria-label="Minimum stars"'),
 ("aria-label=\"${n} étoile${n>1?'s':''} minimum\"", "aria-label=\"Minimum ${n} star${n>1?'s':''}\""),
 ("Minimum ${s.val} étoile${s.val>1?'s':''}. Les modèles non testés reçoivent une note moyenne.", "Minimum ${s.val} star${s.val>1?'s':''}. Untested models get an average score."),
 (' Inclure le malus 2026 (CO₂ et poids)</label>', ' Include the 2026 French malus tax (CO₂ and weight)</label>'),
 ("Fourchette de prix catalogue. Laissez le minimum à 0 pour ne fixer qu'un plafond. Au-dessus du maximum, la note tombe à 0 dès 15&nbsp;% de dépassement ; sous le minimum, elle baisse plus doucement (0 à 30&nbsp;% en dessous).",
  "List price range. Leave the minimum at 0 to set a ceiling only. Above the maximum, the score drops to 0 at 15&nbsp;% over; below the minimum, it falls more gently (0 at 30&nbsp;% under). The malus is a French registration tax based on CO₂ emissions and weight."),
 ("<h3>Kilométrage et prix de l'énergie</h3>${infoBtn('energy','Kilométrage et prix de l\\'énergie')}", "<h3>Mileage and energy prices</h3>${infoBtn('energy','Mileage and energy prices')}"),
 ('<div class="sub">Kilométrage annuel</div>', '<div class="sub">Annual mileage</div>'),
 ('>SP95 (€/L)<', '>Petrol SP95 (€/L)<'), ('>Gazole (€/L)<', '>Diesel (€/L)<'), ('>GPL (€/L)<', '>LPG (€/L)<'), ('>Électricité (€/kWh)<', '>Electricity (€/kWh)<'),
 ("Rouler à l'E85 avec un boîtier homologué (voitures essence et micro-hybrides essence)", "Run on E85 with an approved conversion kit (petrol and petrol mild-hybrid cars)"),
 ("Sert à estimer le coût annuel de chaque voiture à partir de sa consommation WLTP. E85 : surconsommation de 25 % comptée (Ford Kuga FlexiFuel, ou boîtier). GPL : surconsommation de 20 % comptée. Électricité : tarif réglementé option Base (recharge à domicile). Hybrides rechargeables : carburant et électricité, recharges régulières supposées.",
  "Used to estimate each car's yearly cost from its WLTP consumption. E85: 25% extra consumption counted (Ford Kuga FlexiFuel, or kit). LPG: 20% extra consumption counted. Electricity: French regulated “Base” tariff (home charging). Plug-in hybrids: fuel and electricity, regular charging assumed."),
 ("const GROUPS = {price:'Budget', body:'Gabarit', moto:'Motorisation et énergie', box:'Conduite', trunk:'Pratique et sécurité'};", "const GROUPS = {price:'Budget', body:'Size', moto:'Powertrain and energy', box:'Driving', trunk:'Practicality and safety'};"),
 ('aria-label="Aide : ${name}" title="Aide"', 'aria-label="Help: ${name}" title="Help"'),
 (" Éligible aux aides à l'achat <small>filtre</small></label>${infoBtn('aid',\"Aides à l'achat\")}", " Eligible for purchase incentives <small>filter</small></label>${infoBtn('aid','Purchase incentives')}"),
 ("Ne garde que les voitures électriques ouvrant droit à la prime « coup de pouce » (ex-bonus écologique) : score environnemental obtenu, prix sous 47 000 € et poids sous 2,4 t. Ce filtre ne modifie pas les notes.",
  "Keeps only electric cars eligible for the French “coup de pouce” incentive (formerly the ecological bonus): environmental score obtained, price under €47,000 and weight under 2.4 t. This filter does not change the scores."),
 ('<div class="grp">Marques</div>', '<div class="grp">Brands</div>'), (" Marques <small>filtre</small></label>${infoBtn('brand','Marques')}", " Brands <small>filter</small></label>${infoBtn('brand','Brands')}"),
 ("[['only','Uniquement'],['excl','Exclure']]", "[['only','Only'],['excl','Exclude']]"),
 ("'Seules les marques sélectionnées restent dans le classement.':'Les marques sélectionnées sont retirées du classement.'} Ce filtre ne modifie pas les notes.",
  "'Only the selected brands stay in the ranking.':'The selected brands are removed from the ranking.'} This filter does not change the scores."),
 ("`${n} critère${n>1?'s':''} actif${n>1?'s':''}` : 'Aucun critère actif'", "`${n} active criteri${n>1?'a':'on'}` : 'No active criteria'"),
 # boutons, messages
 ('Copier le résumé</button>', 'Copy summary</button>'), ('Copier le lien', 'Copy link'), ('Recommencer</button>', 'Start again</button>'),
 ("toast('Critères réinitialisés'", "toast('Criteria cleared'"), ("b.textContent='Annuler'", "b.textContent='Undo'"),
 ("const verdict = sc => sc>=88?'Correspondance excellente':sc>=75?'Très bonne correspondance':sc>=60?'Bonne correspondance':sc>=40?'Correspondance partielle':'Faible correspondance';",
  "const verdict = sc => sc>=88?'Excellent match':sc>=75?'Very good match':sc>=60?'Good match':sc>=40?'Partial match':'Poor match';"),
 ('aria-label="Note ${sc} sur 100"', 'aria-label="Score ${sc} out of 100"'),
 ("'Remplit tous vos critères'", "'Meets all your criteria'"), ("Remplit tous vos critères", "Meets all your criteria"),
 ("'Non testée Euro NCAP':'Donnée manquante ('+p.cr.short.toLowerCase()+')'", "'Not tested by Euro NCAP':'Missing data ('+p.cr.short.toLowerCase()+')'"),
 ("(soft?'Un peu sous votre prix minimum':'Sous votre prix minimum') : (soft?'Un peu au-dessus du budget':'Au-dessus du budget')", "(soft?'Slightly below your minimum price':'Below your minimum price') : (soft?'Slightly over budget':'Over budget')"),
 ("soft?'Énergie un peu chère à l’usage':'Énergie chère à l’usage'", "soft?'Slightly high energy cost':'High energy cost'"),
 ("'Pas de coffre avant' : (soft?'Coffre un peu juste':'Coffre trop petit')", "'No front boot' : (soft?'Boot a little small':'Boot too small')"),
 ("c.plug?(soft?'Autonomie un peu juste':'Autonomie insuffisante'):'Pas de batterie rechargeable'", "c.plug?(soft?'Range a little short':'Range too short'):'No plug-in battery'"),
 ("c.plug?(soft?'Recharge un peu lente':'Recharge lente'):'Pas de recharge'", "c.plug?(soft?'Charging a little slow':'Slow charging'):'No charging'"),
 ("'Moins d’étoiles Euro NCAP que souhaité'", "'Fewer Euro NCAP stars than wanted'"),
 ("c.hp<s.min?'Moins puissante que souhaité':'Plus puissante que souhaité'", "c.hp<s.min?'Less powerful than wanted':'More powerful than wanted'"),
 ("'Carrosserie différente', moto:()=> 'Motorisation différente'", "'Different body style', moto:()=> 'Different powertrain'"),
 ("s.val==='gt5'?'Pas de 7 places':'Plus de 5 places'", "s.val==='gt5'?'No 7-seat version':'More than 5 seats'"),
 ("c.bx==='A'?'Boîte automatique':'Boîte manuelle'", "c.bx==='A'?'Automatic gearbox':'Manual gearbox'"),
 ("c.tr==='AWD'?'4 roues motrices':'Pas de 4 roues motrices'", "c.tr==='AWD'?'All-wheel drive':'No all-wheel drive'"),
 ("'Point faible : '", "'Weak point: '"),
 ("<span class=\"lbl\"> autre${n>1?'s':''} version${n>1?'s':''}</span>", "<span class=\"lbl\"> other version${n>1?'s':''}</span>"),
 ('Toutes les versions qui passent vos filtres, de la mieux notée à la moins bien notée.', 'Every version that passes your filters, from highest to lowest score.'),
 ('data-close>Fermer</button>', 'data-close>Close</button>'),
 ("c.bx==='A'?'Auto':'Manuelle'", "c.bx==='A'?'Auto':'Manual'"),
 # résumé à copier
 ("v=(s.min>0?'budget de '+eur(s.min)+' à '+eur(s.val):'budget maximum '+eur(s.val))+(s.malus!==false?' (malus inclus)':'');", "v=(s.min>0?'budget '+eur(s.min)+' to '+eur(s.val):'maximum budget '+eur(s.val))+(s.malus!==false?' (malus included)':'');"),
 ("v=[...s.val].map(BL).join(' ou ');", "v=[...s.val].map(BL).join(' or ');"),
 ("v=s.val==='gt5'?'plus de 5 places':'5 places ou moins';", "v=s.val==='gt5'?'more than 5 seats':'5 seats or fewer';"),
 ("[x,x])[1]).join(' ou ');", "[x,x])[1]).join(' or ');"),
 ("v=s.min+(s.max?' à '+s.max+' ch':' ch et plus');", "v=s.min+(s.max?' to '+s.max+' hp':' hp and above');"),
 ("v='énergie maximum '+fmt(s.val)+' €/an';", "v='energy at most '+eur(s.val)+'/yr';"),
 ("v='autonomie minimum '+s.val+' km';", "v='range at least '+s.val+' km';"),
 ("v='recharge minimum '+s.val+' kW';", "v='charging at least '+s.val+' kW';"),
 ("v=s.val==='A'?'boîte automatique':'boîte manuelle';", "v=s.val==='A'?'automatic gearbox':'manual gearbox';"),
 ("v=s.val==='awd'?'4 roues motrices':'2 roues motrices';", "v=s.val==='awd'?'all-wheel drive':'two-wheel drive';"),
 ("v='coffre minimum '+s.val+' L'+(s.fk?' avec coffre avant':'');", "v='boot at least '+s.val+' L'+(s.fk?' with front boot':'');"),
 ("v='Euro NCAP '+s.val+' étoiles minimum';", "v='Euro NCAP '+s.val+' stars minimum';"),
 ("L.push(v+(s.w===3?' (impératif)':''));", "L.push(v+(s.w===3?' (essential)':''));"),
 ("L.push(\"éligible aux aides à l'achat\");", "L.push('eligible for purchase incentives');"),
 ("L.push((B.mode==='only'?'marques : ':'sans : ')", "L.push((B.mode==='only'?'brands: ':'excluding: ')"),
 (" : ${r.score}/100, à partir de ${eur(r.car.p)}`", ": ${r.score}/100, from ${eur(r.car.p)}`"),
 ("`\\n\\nSur le site officiel : ${", "`\\n\\nOn the official website: ${"),
 ("`Mioto, le comparateur de voitures neuves selon vos critères\\nMes critères : ${L.join(' · ')}\\n\\nMon podium :\\n${top.join('\\n')}${w}\\n\\nVoir ce classement sur Mioto : ${shareURL()}`",
  "`Mioto, the new car comparison site built around your criteria\\nMy criteria: ${L.join(' · ')}\\n\\nMy podium:\\n${top.join('\\n')}${w}\\n\\nSee this ranking on Mioto: ${shareURL()}`"),
 ('<h2 id="cmp-title">Résumé de ma recherche</h2>', '<h2 id="cmp-title">My search summary</h2>'),
 ("La copie automatique n'est pas disponible ici : le texte est sélectionné, copiez-le avec Ctrl+C (ou un appui long sur mobile).", "Automatic copying isn't available here: the text is selected, copy it with Ctrl+C (or a long press on mobile)."),
 ("toast('Lien copié : il ouvre ce classement avec vos critères')", "toast('Link copied: it opens this ranking with your criteria')"),
 ("toast('Résumé copié : collez-le où vous voulez')", "toast('Summary copied: paste it wherever you like')"),
 ("'d’or'", "'Gold'"), ("'d’argent'", "'Silver'"), ("'de bronze'", "'Bronze'"), ('aria-label="Médaille ${lab}"', 'aria-label="${lab} medal"'),
 ("'Ouvrir la page '+c.bd+' '+c.md+' sur le site officiel':'Ouvrir le site officiel '+c.b} (nouvel onglet)\">${big?'Voir sur le site '+siteName(c.b):'Site '+siteName(c.b)}",
  "'Open the '+c.bd+' '+c.md+' page on the official website':'Open the official '+c.b+' website'} (new tab)\">${big?'See it on the '+siteName(c.b)+' website':siteName(c.b)+' website'}"),
 ('Arrivée prévue en ${c.y}', 'Due in ${c.y}'), ('Fin de commercialisation ${c.end}', 'End of sale ${c.end}'),
 ("c.bx==='A'?'Automatique':'Manuelle'];", "c.bx==='A'?'Automatic':'Manual'];"),
 ("t.push(c.tk+' L de coffre')", "t.push(c.tk+' L boot')"), ("t.push('4 roues motrices')", "t.push('All-wheel drive')"), ("t.push(fmtCost(ec)+' d\\'énergie')", "t.push(fmtCost(ec)+' energy')"),
 # fiches techniques
 ("['Marque',", "['Brand',"), ("'Motorisation'", "'Powertrain'"), ("+' ch'", "+' hp'"), ("${c.hp} ch<", "${c.hp} hp<"), ("['Couple',", "['Torque',"), ("['0 à 100 km/h',", "['0-100 km/h',"),
 ("['Conso. WLTP',", "['WLTP consumption',"), ("['Conso. élec.',", "['Electric consumption',"), ("['Coût énergie / an',", "['Energy cost / year',"), ("['Coût énergie',", "['Energy cost',"),
 ("' g/km · classe '", "' g/km · class '"), ("['Batterie',", "['Battery',"), ("'Autonomie élec.'", "'Electric range'"), ("['Recharge max.',", "['Max. charging',"), ("['Recharge 10-80 %',", "['10-80% charge',"),
 ("'Boîte'", "'Gearbox'"), ("'Transmission'", "'Drive'"), ("['Places / portes',", "['Seats / doors',"), ("c.pl+' ou 7'", "c.pl+' or 7'"), ("['Longueur',", "['Length',"), ("['Poids à vide',", "['Kerb weight',"),
 ("['Coffre avant',", "['Front boot',"), ("'Coffre'", "'Boot'"), ("(c.fk?'oui':'non')", "(c.fk?'yes':'no')"),
 ("['Commercialisée depuis',", "['On sale since',"), ("['Fin de commercialisation',", "['End of sale',"), ("['Aides à l\\'achat',", "['Purchase incentives',"),
 ("(eligibleAid(c)?'éligible':'non éligible')", "(eligibleAid(c)?'eligible':'not eligible')"), ("'Prix'", "'Price'"),
 ("['Malus 2026',", "['2026 malus (France)',"), ("' (estimation)'", "' (estimate)'"), ("'aucun'", "'none'"),
 ("['Conso. carburant',", "['Fuel consumption',"), ("['Conso. électrique',", "['Electric consumption',"), ("'Carrosserie'", "'Body style'"), ("'Puissance'", "'Power'"),
 ("'Autonomie'", "'Range'"), ("'Conso. /100 km'", "'Consumption /100 km'"),
 ('Éligible aux aides</span>', 'Eligible for incentives</span>'),
 ('Fin de série ${c.end}', 'Ends ${c.end}'), ('Arrive en ${c.y}', 'Due ${c.y}'),
 ('<summary>Pourquoi ${r.score}/100 ?</summary>', '<summary>Why ${r.score}/100?</summary>'), ('Fiche technique complète', 'Full specifications'),
 ('Fiche du modèle', 'Model page'), ("'Pondération : '", "'Weighting: '"),
 # résultats
 ("<b>Par où commencer ?</b><p>Activez un premier critère dans le panneau : votre budget, par exemple. Les voitures se classent aussitôt, avec une note sur 100. Ajoutez ensuite la carrosserie, la motorisation ou l'autonomie, et réglez l'importance de chacun.</p>",
  "<b>Where to start?</b><p>Switch on a first criterion in the panel: your budget, for example. Cars are ranked instantly, each with a score out of 100. Then add body style, powertrain or range, and set how important each one is.</p>"),
 ('data-open-crit>Choisir mes critères</button>', 'data-open-crit>Choose my criteria</button>'), ('data-example>Voir un exemple</button>', 'data-example>See an example</button>'),
 ("Aucune voiture ne correspond. Élargissez le filtre de marques, passez un critère impératif en « Important » ou décochez « Masquer les voitures qui ratent un critère impératif ».",
  "No car matches. Widen the brand filter, switch an essential criterion to “Important” or untick “Hide cars that miss an essential criterion”."),
 ('data-open-crit>Modifier mes critères</button>', 'data-open-crit>Edit my criteria</button>'),
 ('Et votre voiture <em>idéale</em> est…', 'And your <em>ideal</em> car is…'), ('N° 1 sur ', 'No. 1 of '), ("?'modèles':'versions'", "?'models':'versions'"),
 ('La suite du classement <small>${fmt(res.length-3)} autres', 'The rest of the ranking <small>${fmt(res.length-3)} more'),
 ('Voir le détail</button>', 'See details</button>'), ('${r.rank}e place · ', 'No. ${r.rank} · '),
 ("'<span aria-hidden=\"true\">✓</span><span class=\"lbl\"> Comparée</span>':'<span aria-hidden=\"true\">+</span><span class=\"lbl\"> Comparer</span>'",
  "'<span aria-hidden=\"true\">✓</span><span class=\"lbl\"> Added</span>':'<span aria-hidden=\"true\">+</span><span class=\"lbl\"> Compare</span>'"),
 ("aria-label=\"${on?'Retirer':'Ajouter'} ${c.bd} ${c.md} ${on?'de':'à'} la comparaison\"", "aria-label=\"${on?'Remove':'Add'} ${c.bd} ${c.md} ${on?'from':'to'} the comparison\""),
 ("trayMsg='3 voitures maximum : retirez-en une.'", "trayMsg='3 cars maximum: remove one.'"), ("'Ajoutez une deuxième voiture.'", "'Add a second car.'"),
 ('aria-label="Retirer ${c.bd} ${c.md}"', 'aria-label="Remove ${c.bd} ${c.md}"'), ('data-clear>Vider</button>', 'data-clear>Clear</button>'), ('>Comparer (${CMP.length})</button>', '>Compare (${CMP.length})</button>'),
 ("sec('Correspondance à vos critères')", "sec('Match with your criteria')"), ("row('Note globale'", "row('Overall score'"), ("sec('Fiche technique')", "sec('Specifications')"),
 ('<h2 id="cmp-title">Comparaison</h2>', '<h2 id="cmp-title">Comparison</h2>'), ('Ouvrir en face à face', 'Open head to head'), ('>Retirer</button>', '>Remove</button>'),
 ('▲ en vert : la meilleure valeur de la ligne. ▼ en rouge : la moins bonne. Les notes sont calculées avec vos critères actuels.', '▲ in green: the best value in the row. ▼ in red: the worst. Scores are calculated with your current criteria.'),
 ('</b> modèles · <b class="num">${brands.size}</b> marques', '</b> models · <b class="num">${brands.size}</b> brands'),
 # face à face
 ('<h2 id="ff-pick-t" class="ff-t">Vos modèles</h2>', '<h2 id="ff-pick-t" class="ff-t">Your models</h2>'),
 ("Pour chaque voiture, choisissez la marque, le modèle puis la motorisation. Vous pouvez aussi comparer deux motorisations d'un même modèle.", "For each car, choose the brand, the model and then the version. You can also compare two versions of the same model."),
 ("'Choisissez un deuxième modèle pour lancer le face-à-face.' : 'Choisissez au moins deux modèles pour lancer le face-à-face.'", "'Choose a second model to start the head to head.' : 'Choose at least two models to start the head to head.'"),
 ('<h2 class="ff-t">Le face-à-face</h2>', '<h2 class="ff-t">Head to head</h2>'), ("sh.textContent='Lien copié'", "sh.textContent='Link copied'"), ("window.prompt('Copiez ce lien :'", "window.prompt('Copy this link:'"),
 ('<span class="ff-n">Modèle ${i+1}</span>', '<span class="ff-n">Model ${i+1}</span>'),
 ('<span>Marque</span>', '<span>Brand</span>'), ('Choisir une marque', 'Choose a brand'), ('<span>Modèle</span>', '<span>Model</span>'),
 ("'Choisir un modèle':'Choisissez d’abord la marque'", "'Choose a model':'Choose a brand first'"), ('<span>Motorisation</span>', '<span>Version</span>'), ('Choisissez d’abord le modèle', 'Choose a model first'),
 ('<b>+ Ajouter un modèle</b>', '<b>+ Add a model</b>'), ("${left} place${left>1?'s':''} restante${left>1?'s':''}", "${left} slot${left>1?'s':''} left"),
 ('▲ en vert : la meilleure valeur de la ligne. ▼ en rouge : la moins bonne. Prix « à partir de », malus 2026 calculé sur le CO₂ et le poids.', '▲ in green: the best value in the row. ▼ in red: the worst. “From” prices; the 2026 French malus tax is calculated from CO₂ and weight.'),
]
_JS_USED = set()
def js_en(s):
    for i, (a, b) in enumerate(JS_EN):
        if a in s: _JS_USED.add(i); s = s.replace(a, b)
    return s
def js_unused():
    return [JS_EN[i][0] for i in range(len(JS_EN)) if i not in _JS_USED]

# --- noms de modèles et de marques sur le site anglais -------------------------------------------------------------------
BRAND = {'Opel': 'Opel / Vauxhall'}                        # Opel est vendue sous la marque Vauxhall au Royaume-Uni
BRAND_NATIONS = {'Opel': ['Allemagne', 'Royaume-Uni']}     # drapeaux affichés (clés françaises de meta.json)
BRAND_ADJ = {'Opel': 'German / British'}
BRAND_NATION = {'Opel': 'Germany / United Kingdom'}
_MN = [
    (r'^Série (\d)\b', r'\1 Series'),
    (r'^Classe ([A-Z])\b', r'\1-Class'),
    (r'^AMG GT 4 Portes$', 'AMG GT 4-Door Coupé'),
    (r'\bBreak\b', 'Estate'),
    (r'\bBerline\b', 'Saloon'),
]
def mname_en(b, m):
    """Nom de modèle affiché sur le site anglais (« Série 3 » → « 3 Series », « Classe C Break » → « C-Class Estate »)."""
    for a, r in _MN: m = re.sub(a, r, m)
    if b == 'BMW': m = re.sub(r'\bCabriolet\b', 'Convertible', m)
    return m

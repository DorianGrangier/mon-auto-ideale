# Mioto

Le comparateur de voitures neuves selon vos critères.

Comparateur de voitures neuves vendues en France : chaque version reçoit une note sur 100 selon les critères du visiteur, avec une fiche et un avis par modèle.

## Fonctionnement

- **Données** : la feuille Google Sheets « Auto » (un onglet, 35 colonnes, ordre fixe). Chaque nuit, le robot (`.github/workflows/site.yml`) la télécharge, la convertit (`scripts/build_data.py`), la contrôle (`scripts/check_data.py`) puis reconstruit et publie le site (`scripts/build_site.py`).
- **Garde-fou** : si un contrôle bloquant échoue (colonnes modifiées, chute du nombre de versions, valeur aberrante nouvelle…), rien n'est publié, l'ancienne version reste en ligne et GitHub envoie un e-mail. Le détail est dans l'onglet *Actions*, résumé de l'exécution.
- **Avis** : `data/avis.json`, un avis par modèle (`Marque|Modèle`, ou `Marque|Modèle|ev` pour une version électrique vendue sous le même nom).
- **Réglages** : `data/meta.json` (pays des marques, drapeaux, sites officiels, modèles éligibles aux aides, silhouettes).
- **Comparateur** : `src/index.body.html` ; styles : `assets/site.css` ; textes : `src/methode.html`, `src/mentions-legales.html`.

## Mettre à jour à la main

Onglet *Actions* → « Mise à jour du site » → *Run workflow*.

## Construire en local

```
python3 scripts/build_data.py feuille.csv data/data.json
python3 scripts/build_site.py dist
python3 -m http.server -d dist
```

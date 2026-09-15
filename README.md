# Fonds européens de cohésion en Île-de-France

Analyse des opérations financées par les fonds européens en Île-de-France : **FEDER, FSE et IEJ sur
2014-2020** (1 121 opérations, 693,2 M€ d'aide UE) et **FEDER et FSE+ sur 2021-2027** (le FTJ ne concerne aucun territoire francilien), avec
croisement INSEE sur le revenu médian communal. Étude de cas technique, réalisée en 2 heures.

- 📄 **[Résultats](RESULTATS.md)** ([PDF](RESULTATS.pdf)) — réponses et restitutions
- 🔧 **[Méthodologie](METHODOLOGIE.md)** ([PDF](METHODOLOGIE.pdf)) — outils, conventions, contrôles

![Mobilisation cumulée des deux programmations](sorties/q4_cumul_millesime.png)

## Ce que montrent les données

- **Le jeu de données ne contient pas le montant des fonds européens** : il faut le reconstituer
  (coût éligible × taux de cofinancement). C'est le principal enseignement sur la qualité.
- **Financement très concentré** : le top 10 pèse 38,6 % de l'enveloppe, porté par la Région et
  Bpifrance (instruments financiers, programmes régionaux de formation).
- **Seine-Saint-Denis premier département** (112,6 M€), qui capte à elle seule 10,04 des 12,97 M€ d'IEJ.
- **Corrélation fonds / revenu médian non concluante** : faible, négative, et calculée sur 26 %
  seulement du montant UE — seule fraction rattachable à une commune identifiable.
- **De 14-20 à 21-27** : 54 % du rythme précédent à millésime égal, mais des opérations 3,2 fois
  plus grosses en médiane.

## Lancer

```bash
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
.venv/bin/python src/telecharger.py   # ~59 Mo depuis les sources officielles
.venv/bin/python src/commun.py        # contrôles du socle
.venv/bin/python src/q1_analyse.py    # top 10, départements, croisement INSEE
.venv/bin/python src/q2_qualite.py    # complétude et anomalies mesurées
.venv/bin/python src/q3_feder.py      # départements FEDER et montant moyen
.venv/bin/python src/q4_evolution.py  # comparaison 14-20 / 21-27 et figures
```

Les quatre scripts d'analyse sont indépendants : chacun répond à une question et s'exécute seul.
`src/commun.py` porte le chargement partagé et les deux conventions de calcul. Tous écrivent
leurs tableaux dans `sorties/`, en markdown **et** en CSV — aucun chiffre des livrables n'est
saisi à la main.

Python 3.13, pandas, matplotlib, openpyxl. Export PDF par `pandoc` + XeLaTeX (commande dans la
méthodologie).

## Arborescence

```
RESULTATS.md / METHODOLOGIE.md   livrables (+ PDF)
src/                             6 scripts — 928 lignes, 9 fonctions, 0 classe
sorties/                         tableaux (.md/.csv), figures (.png), journaux d'exécution
data/                            sources brutes, non versionnées (re-téléchargeables)
```

## Sources

| Jeu | Origine |
|:---|:---|
| Opérations 2014-2020 | [Région Île-de-France / data.gouv.fr](https://www.data.gouv.fr/datasets/gestion-des-fonds-europeens-en-ile-de-france-liste-des-operations/) |
| Revenus communaux (FiLoSoFi 2017) | [INSEE](https://www.insee.fr/fr/statistiques/4291712) |
| Opérations 2021-2027 | [europe-en-france.gouv.fr](https://www.europe-en-france.gouv.fr/fr/ressources/liste-operations-feder-fse-ftj-2021-2027) |

Les données brutes ne sont pas versionnées (59 Mo) : `src/telecharger.py` les récupère à
l'identique et journalise URL, taille et date dans `sorties/journal_telechargement.md`.

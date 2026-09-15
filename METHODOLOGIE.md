---
title: "Fonds européens de cohésion en Île-de-France"
subtitle: "Étude de cas SGAE — méthodologie et outils"
date: "15 septembre 2026"
lang: fr
---

# 1. Outils

| Outil | Version | Usage |
|:---|:---|:---|
| Python | 3.13.15 | Traitement de toute la chaîne |
| pandas | 3.0.5 | Chargement, jointures, agrégations, corrélations |
| matplotlib | 3.11.2 | Les 4 figures, en PNG (aucune dépendance en ligne) |
| openpyxl | 3.1.5 | Lecture des classeurs `.xlsx` (INSEE, fichier 21-27) |
| uv | — | Environnement virtuel et dépendances |
| pandoc + XeLaTeX | 3.10.2 | Conversion des deux markdown en PDF |
| Claude Code (Opus 5) | — | Assistant de développement : exploration des schémas, écriture et débogage des scripts, rédaction sous revue humaine |

`scipy` a été volontairement écarté : la corrélation de Spearman est obtenue par un Pearson sur les
rangs, soit trois lignes de code et une dépendance de moins. **Aucun traitement manuel en tableur :
tous les chiffres des deux documents sortent des scripts**, donc rejouables et vérifiables.

# 2. Sources

- **Opérations 2014-2020** — export JSON de l'API Opendata de la Région Île-de-France (jeu
  référencé sur data.gouv.fr). 1 121 opérations, source mise à jour le 03/05/2022.
- **Revenus communaux** — INSEE, FiLoSoFi 2017, fichier communal. 1 260 communes franciliennes
  après exclusion des arrondissements parisiens.
- **Opérations 2021-2027** — fichier national FEDER-FSE+-FTJ d'europe-en-france.gouv.fr, version
  du 08/09/2025. 5 148 opérations toutes régions.

Toutes récupérées le 15/09/2026 à 10:15 ; URL exactes dans `src/telecharger.py`, journal horodaté
dans `sorties/journal_telechargement.md`.

Deux choix de fichier à signaler :

- **JSON plutôt que CSV** pour 14-20 : le champ département est multivalué ; le CSV l'aplatit en
  une chaîne dont le séparateur doit être devinné, le JSON le restitue comme une liste.
- **Revenus déclarés (`FILO2017_DEC_COM`) plutôt que disponibles** : la question porte sur les
  *foyers fiscaux*, donc sur le revenu déclaré avant redistribution. Indicateur `Q217`, onglet
  `ENSEMBLE`, à partir de la 6ᵉ ligne (les 5 premières sont un en-tête de présentation).

# 3. Chaîne de traitement

```
data/ (3 sources brutes)
   │
   ├─ src/telecharger.py ......... récupération + journal (URL, taille, date)
   ├─ src/commun.py .............. socle : renommage des 13 colonnes, montant UE,
   │                               normalisation des codes département, éclatement
   │                               multivalué, normalisation des libellés de communes
   ├─ src/q1_analyse.py .......... top 10, groupement départemental, croisement INSEE
   ├─ src/q2_qualite.py .......... complétude et anomalies mesurées
   ├─ src/q3_feder.py ............ départements FEDER et montant moyen
   └─ src/q4_evolution.py ........ comparaison 14-20 / 21-27 et figures
                │
                └─> sorties/ ..... un .md et un .csv par tableau, un .png par figure
```

Les quatre scripts d'analyse sont **indépendants** et s'exécutent seuls. `commun.py` existe parce
que le chargement a quatre appelants réels, sans abstraction spéculative. Chaque tableau est écrit
en markdown **et** en CSV, ce qui garantit qu'aucun chiffre des livrables n'a été recopié à la main.

# 4. Conventions de calcul

Le jeu 2014-2020 ne permet pas de répondre sans ces conventions, et deux analystes en retenant
d'autres obtiendraient d'autres chiffres. D'où leur énoncé explicite, avec leur effet chiffré.

## 4.1 Le montant UE est reconstitué

Aucune des 13 colonnes ne donne la subvention européenne. On pose :

> **montant UE = total des dépenses éligibles × taux de cofinancement UE**

Soit 693,2 M€ pour 1 668,9 M€ de dépenses éligibles — cohérent avec les « plus de 600 M€ » annoncés
dans la description du jeu, ce qui valide la formule.

## 4.2 Département multivalué : comptage intégral, montant au prorata

Le champ est une **liste** (une opération régionale porte les huit départements) :

- **nombre d'opérations** : comptée dans **chacun** des départements cités — d'où 2 241
  rattachements franciliens pour 1 121 opérations ;
- **montant** : **divisé à parts égales** entre les départements cités, de sorte que la somme des
  départements égale le total régional localisé. Écart contrôlé à chaque exécution : **0,0000 €**.

Les codes sont dédoublonnés après suppression des zéros de tête (une opération porte `75` **et**
`075`, sinon Paris compte double). En revanche **aucun code erroné n'est corrigé** (`2`, `3`,
`3.2153009259259258`, `97`) : le faire supposerait de réécrire la source sur hypothèse. Ils sont
recensés et isolés hors Île-de-France.

## 4.3 Appariement INSEE par libellé, sans forçage

Le jeu n'a **aucun code commune**. Procédure : éclatement de la localisation sur « : », puis
normalisation des deux côtés (majuscules, sans accent, tirets et apostrophes en espaces), puis
jointure sur le référentiel francilien, puis répartition du montant à parts égales entre les
libellés cités.

Deux garde-fous : les **4 homonymes franciliens** (Blandy, Marolles-en-Brie, Mondreville,
Saint-Martin-des-Champs) sont écartés faute de pouvoir les départager ; les localisations **non
communales ne sont pas rattachées de force**, elles sont comptées puis exclues.

Couverture obtenue : 287 communes, 610 opérations, mais **26,0 % du montant UE** — chiffre affiché
dans les résultats plutôt que dissimulé derrière un coefficient.

## 4.4 Quatre coefficients de corrélation, pas un

Un coefficient unique aurait été trompeur. Deux périmètres (communes financées / toutes les
communes, celles sans opération valant zéro) × deux variables (montant total / montant par
habitant) × Pearson et Spearman. L'écart entre Pearson (−0,07) et Spearman (−0,42) est lui-même
une information : la distribution est trop asymétrique pour que Pearson soit pertinent. Le montant
par habitant est indispensable, sans quoi la corrélation mesure surtout la taille démographique.

## 4.5 Méthode de production des restitutions de la question 4

Comparer une programmation avancée (liste arrêtée en mai 2022) à une programmation jeune (septembre
2025) exige deux précautions :

1. **Alignement sur l'année de programmation** : l'année de début de chaque opération devient un
   rang (année 1 = 2014 ou 2021), puis les montants sont cumulés. La comparaison n'est tenue pour
   licite que **jusqu'à la 4ᵉ année**. Au-delà, la courbe 21-27 est **interrompue** sur le
   graphique — la prolonger à plat aurait suggéré un arrêt de la programmation.
2. **Priorité aux indicateurs insensibles au stade d'avancement** : médiane et moyenne par
   opération, taux de cofinancement, répartition par fonds. Ils restent interprétables même sur
   des listes incomplètes, contrairement aux totaux.

Trois figures en découlent : volumes par fonds (barres groupées), cumul à millésime identique
(courbes), distribution du montant par opération (boîtes à moustaches, extrêmes masqués, moyenne
en losange). Toutes en PNG, intégrées aux PDF, sans dépendance en ligne.

Le périmètre 21-27 est le seul programme régional francilien du fichier national (« Programme
régional Île-de-France et bassin de la Seine FEDER-FSE+ 2021-2027 », 140 opérations sur 5 148) ;
une assertion arrête le script si le filtre en capturait plusieurs.

# 5. Contrôles exécutés

Chaque script imprime ses contrôles ; un échec interrompt le traitement. Journal complet dans
`sorties/journal_execution.txt`.

| Contrôle | Résultat |
|:---|:---|
| Nombre d'opérations chargées | 1 121, conforme à l'API |
| Répartition par fonds recoupée avec les facettes de l'API | FSE 787 / FEDER 313 / IEJ 21, conforme |
| Conservation du montant après prorata (assertion) | écart 0,0000 € |
| Montant UE total vs description de la source | 693,2 M€ vs « plus de 600 M€ », cohérent |
| Effectifs FEDER par département vs comptage brut (assertion) | conforme |
| Robustesse du classement Q3 à la convention | même trio en mono-départemental |
| Codes INSEE retenus tous franciliens | vérifié par filtre |
| Taux d'appariement affiché, non appariés comptés | 287 communes, 26,0 % du montant |
| Unicité du programme régional 21-27 (assertion) | un seul libellé |

# 6. Reproduire

```bash
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
.venv/bin/python src/telecharger.py      # ~59 Mo, quelques minutes
.venv/bin/python src/commun.py           # contrôles du socle
.venv/bin/python src/q1_analyse.py
.venv/bin/python src/q2_qualite.py
.venv/bin/python src/q3_feder.py
.venv/bin/python src/q4_evolution.py

pandoc RESULTATS.md -o RESULTATS.pdf --pdf-engine=xelatex \
  -V lang=fr -V geometry:margin=2cm -V fontsize=10pt \
  -V mainfont="Helvetica Neue" -V monofont="Menlo"
```

Les sources brutes (59 Mo) ne sont pas jointes : `src/telecharger.py` les récupère à l'identique.

# 7. Arbitrages assumés

1. **Aucune valeur erronée corrigée.** Lire `3` comme `93` au vu de la localisation « SAINT DENIS »
   serait probablement juste, mais introduirait une hypothèse non tracée dans les chiffres publiés.
2. **La répartition à parts égales est une convention, pas une mesure.** Une clé à la population
   serait plus réaliste, mais rien dans le jeu n'indique la localisation réelle de la dépense : ce
   serait une fausse précision.
3. **Pas d'appariement phonétique** des communes : il aurait amélioré la couverture au prix
   d'erreurs invérifiables. Une couverture honnête de 26 % est préférée à une couverture optimiste.
4. **La question 4 mesure des volumes publiés, pas des taux d'absorption** : les dotations
   programmées sont absentes des deux fichiers et exigeraient une troisième source.
5. **La question 1 a été traitée à la maille demandée tout en signalant qu'elle n'est pas la
   bonne.** Une lecture départementale serait plus solide ; une lecture par catégorie
   d'intervention serait la plus pertinente, mais reste impossible (champ renseigné à 20,1 %).

Ordre de traitement retenu pour qu'un rendu interrompu reste cohérent : socle et contrôles, puis
question 3 (la plus directe), questions 1 et 2 qui partagent ce socle, enfin question 4 qui mobilise
une source supplémentaire. Les deux documents ont été rédigés au fil des résultats.

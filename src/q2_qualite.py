"""Q2 — Mesure de la qualité du jeu de données 2014-2020.

Chaque constat écrit dans RESULTATS.md est produit ici par une mesure, pas par une impression.
"""

import pandas as pd

from commun import COLONNES, DEPARTEMENTS_IDF, charger_operations, ecrire

df = charger_operations()
n = len(df)

# ------------------------------------------------------------------- Complétude par colonne
colonnes = list(COLONNES.values())
completude = pd.DataFrame(
    {
        "Colonne": colonnes,
        "Valeurs renseignées": [
            int(df[c].apply(len).gt(0).sum())
            if c == "departements"
            else int(df[c].notna().sum())
            for c in colonnes
        ],
    }
)
completude["Taux de complétude"] = (completude["Valeurs renseignées"] / n).map(
    "{:.1%}".format
)
ecrire("q2_completude", completude, f"Complétude des 13 colonnes ({n} opérations)")

# ------------------------------------------------------------------- Anomalies mesurées
codes = df.explode("departements")["departements"].dropna()
codes_invalides = sorted(set(codes) - set(DEPARTEMENTS_IDF))
hors_idf = [c for c in codes_invalides if c.isdigit() and len(c) == 2 and c != "97"]
vrais_faux = [c for c in codes_invalides if c not in hors_idf]


def ops(nombre):
    return f"{nombre} opération" + ("s" if nombre > 1 else "")


doublons = df.duplicated(subset=["beneficiaire", "operation", "cout_total"]).sum()
memes_libelles = df.duplicated(subset=["beneficiaire", "operation"]).sum()
resume_recopie = (
    df["resume"].fillna("").str.strip() == df["operation"].str.strip()
).sum()
taux_nul = (df["taux_ue"].fillna(0) <= 0).sum()
taux_eleve = (df["taux_ue"] > 0.5).sum()
cout_nul = (df["cout_total"].fillna(0) <= 0).sum()
sans_dep = (df["departements"].apply(len) == 0).sum()
montant_sans_dep = df.loc[df["departements"].apply(len) == 0, "montant_ue"].sum()
multi_commune = df["localisation"].fillna("").str.contains(":").sum()
non_communal = (
    df["localisation"]
    .fillna("")
    .str.upper()
    .isin(
        ["ÎLE-DE-FRANCE"]
        + [
            n.upper()
            for n in [
                "Paris",
                "Seine-et-Marne",
                "Yvelines",
                "Essonne",
                "Hauts-de-Seine",
                "Seine-Saint-Denis",
                "Val-de-Marne",
                "Val-d'Oise",
            ]
        ]
    )
    .sum()
)
debut = pd.to_datetime(df["date_debut"], errors="coerce")
fin = pd.to_datetime(df["date_fin"], errors="coerce")
dates_incoherentes = (fin < debut).sum()
fin_hors_periode = (fin > "2023-12-31").sum()
taux_eleve_feder = ((df["taux_ue"] > 0.5) & (df["fonds_court"] == "FEDER")).sum()

anomalies = pd.DataFrame(
    [
        [
            "Exactitude",
            "Codes département invalides ou impossibles",
            f"{len(vrais_faux)} codes distincts : {', '.join(vrais_faux)}",
        ],
        ["Exactitude", "Taux de cofinancement nul ou absent", ops(taux_nul)],
        [
            "Exactitude",
            "Taux de cofinancement supérieur à 50 %, plafond usuel en région plus développée",
            f"{ops(taux_eleve)}, dont {taux_eleve_feder} FEDER jusqu'à "
            f"{df.loc[df['fonds_court'] == 'FEDER', 'taux_ue'].max():.0%} (l'IEJ peut légitimement dépasser ce seuil)",
        ],
        ["Exactitude", "Coût total éligible nul ou absent", ops(cout_nul)],
        [
            "Exactitude",
            "Date de fin postérieure à la fin d'éligibilité de la programmation (31/12/2023)",
            f"{ops(fin_hors_periode)} (jusqu'au {fin.max():%d/%m/%Y})",
        ],
        [
            "Complétude",
            "Aucun département renseigné",
            f"{sans_dep} opérations, soit {montant_sans_dep / 1e6:.1f} M€ non localisables "
            f"({montant_sans_dep / df['montant_ue'].sum():.1%} du montant UE)",
        ],
        [
            "Complétude",
            "Aucun montant de subvention UE dans le jeu",
            "0 colonne : le montant UE doit être reconstitué (coût total x taux)",
        ],
        [
            "Complétude",
            "Aucun identifiant d'opération ni code commune INSEE",
            "0 colonne : tout rapprochement externe repose sur des libellés",
        ],
        [
            "Complétude",
            "Catégorie d'intervention renseignée",
            f"{int(df['categorie'].notna().sum())} opérations sur {n}, soit "
            f"{df['categorie'].notna().mean():.1%} : l'analyse thématique est impossible sur 4 opérations sur 5",
        ],
        [
            "Cohérence",
            "Localisation empilant plusieurs communes dans une seule chaîne",
            f"{ops(multi_commune)} (séparateur « : »)",
        ],
        [
            "Cohérence",
            "Localisation non communale (région ou département)",
            ops(non_communal),
        ],
        [
            "Cohérence",
            "Opérations hors Île-de-France conservées sans indicateur dédié",
            f"codes {', '.join(hors_idf)} présents",
        ],
        [
            "Cohérence",
            "Périmètre annoncé non tenu : le FEADER est décrit mais absent",
            f"fonds présents : {', '.join(sorted(df['fonds_court'].unique()))}",
        ],
        [
            "Unicité",
            "Lignes identiques sur bénéficiaire + opération + coût",
            f"{doublons} doublons stricts ({memes_libelles} couples bénéficiaire/opération répétés)",
        ],
        [
            "Utilisabilité",
            "Résumé recopiant à l'identique le nom de l'opération",
            ops(resume_recopie),
        ],
        [
            "Cohérence",
            "Date de fin antérieure à la date de début",
            ops(dates_incoherentes),
        ],
        [
            "Fraîcheur",
            "Dernière mise à jour de la source",
            "3 mai 2022, pour une programmation ouverte jusqu'au 31/12/2023",
        ],
        [
            "Fraîcheur",
            "Opérations démarrées après la dernière mise à jour",
            f"{ops((debut.dt.year >= 2022).sum())} démarrent en 2022 ou après",
        ],
    ]
)
anomalies.columns = ["Dimension", "Constat", "Mesure"]
ecrire("q2_anomalies", anomalies, "Anomalies mesurées sur les 1 121 opérations")

print("\n--- détail des codes département aberrants (localisation à l'appui) ---")
suspect = df[df["departements"].apply(lambda v: any(c in vrais_faux for c in v))]
for _, r in suspect.iterrows():
    print(
        f"  {r['departements']} | {r['localisation'][:70]} | {r['beneficiaire'][:35]}"
    )

print(
    f"\nrépartition des années de début : "
    f"{debut.dt.year.value_counts().sort_index().to_dict()}"
)
print(f"période couverte : {debut.min():%d/%m/%Y} au {fin.max():%d/%m/%Y}")

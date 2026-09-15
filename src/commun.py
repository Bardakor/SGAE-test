"""Chargement et normalisation des opérations 2014-2020 (socle des quatre analyses).

Deux conventions structurent tout le reste et sont justifiées dans METHODOLOGIE.md :
  - le montant UE n'existe pas dans la source, il est reconstitué (coût total x taux) ;
  - le département est multivalué, le montant est donc réparti au prorata égal.
"""

import json
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DATA = RACINE / "data"
SORTIES = RACINE / "sorties"

# Les 13 colonnes de la source, renommées en noms courts.
COLONNES = {
    "nom_du_beneficiaire_beneficiary_name": "beneficiaire",
    "nom_de_l_operation_operation_name": "operation",
    "resume_de_l_operation_operation_summary": "resume",
    "date_du_debut_de_l_operation_operation_start_date": "date_debut",
    "date_de_fin_de_l_operation_operation_end_date": "date_fin",
    "total_des_depenses_eligibles_attribue_a_l_operation_total_eligible_expenditure_allocated_to_the_oper": "cout_total",
    "taux_de_cofinancement_par_l_union_europeenne_union_co_financing_rate": "taux_ue",
    "emplacement_de_l_operation_operation_location_indicator": "localisation",
    "investissement_territorial_integre_integrated_territorial_investment": "iti",
    "departement_territory": "departements",
    "pays_country": "pays",
    "denomination_de_la_categorie_d_intervention_dont_releve_l_operation_category_of_intervention": "categorie",
    "fonds_funds": "fonds",
}

DEPARTEMENTS_IDF = ["75", "77", "78", "91", "92", "93", "94", "95"]

NOMS_DEPARTEMENTS = {
    "75": "Paris",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
}


def charger_operations():
    """Retourne une ligne par opération, avec le montant UE reconstitué."""
    with open(DATA / "operations_idf_2014_2020.json", encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f)).rename(columns=COLONNES)
    df["montant_ue"] = df["cout_total"] * df["taux_ue"]
    df["annee_debut"] = pd.to_datetime(df["date_debut"], errors="coerce").dt.year
    df["fonds_court"] = (
        df["fonds"]
        .str.replace("’", "'", regex=False)
        .replace(
            {
                "Fonds social européen (FSE)": "FSE",
                "Fonds européen de développement régional (Feder)": "FEDER",
                "Initiative pour l'emploi des jeunes": "IEJ",
            }
        )
    )
    # Le champ département est parfois absent : une liste vide vaut mieux qu'un None à propager.
    df["departements"] = df["departements"].apply(
        lambda v: normaliser_departements(v) if isinstance(v, list) else []
    )
    return df


def normaliser_departements(codes):
    """Aligne les formats ('075' et '75' désignent Paris) et déduplique, sans corriger les codes faux.

    Une opération porte '75' et '075' : sans cette étape elle est comptée deux fois dans Paris.
    Les codes manifestement erronés ('3', '2', '3.2153...') sont laissés tels quels et
    recensés par q2_qualite.py — les corriger supposerait de réécrire la source.
    """
    vus = []
    for code in codes:
        code = str(code).strip()
        code = code.lstrip("0") if len(code.lstrip("0")) >= 2 else code
        if code not in vus:
            vus.append(code)
    return vus


def eclater_departements(df):
    """Une ligne par couple (opération, département), avec le montant réparti au prorata égal.

    Le champ source est une liste : une opération régionale cite les huit départements.
    Le comptage compte donc l'opération dans chacun ; le montant, lui, est divisé pour
    que la somme des départements reste égale au total régional.
    """
    d = df.copy()
    d["nb_departements"] = d["departements"].apply(len)
    d = d[d["nb_departements"] > 0].explode("departements")
    d["montant_ue_prorata"] = d["montant_ue"] / d["nb_departements"]
    localisable = df.loc[df["departements"].apply(len) > 0, "montant_ue"].sum()
    assert abs(d["montant_ue_prorata"].sum() - localisable) < 1, "le prorata ne conserve pas le montant"
    return d.rename(columns={"departements": "departement"})


def normaliser_libelle(serie):
    """Majuscules sans accent ni ponctuation, pour apparier des libellés de communes."""
    sans_accent = (
        serie.astype(str)
        .str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("ascii")
    )
    return (
        sans_accent.str.upper()
        .str.replace(r"[-'’.]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def euros(serie):
    """Montant en euros, séparateur de milliers par espace (lisible dans le rendu)."""
    return serie.round(0).map(lambda v: f"{v:,.0f}".replace(",", " "))


def ecrire(nom, df, titre=None, floatfmt=",.2f"):
    """Écrit un tableau dans sorties/ en markdown et en csv, et l'affiche."""
    SORTIES.mkdir(exist_ok=True)
    md = df.to_markdown(index=False, floatfmt=floatfmt)
    (SORTIES / f"{nom}.md").write_text(md + "\n", encoding="utf-8")
    df.to_csv(SORTIES / f"{nom}.csv", index=False, encoding="utf-8")
    if titre:
        print(f"\n### {titre}")
    print(md)


if __name__ == "__main__":
    df = charger_operations()
    print(f"{len(df)} opérations chargées, {len(df.columns)} colonnes")
    print("\nrépartition par fonds (attendu FSE 787 / FEDER 313 / IEJ 21) :")
    print(df["fonds_court"].value_counts().to_string())
    print(f"\ncoût total éligible : {df['cout_total'].sum() / 1e6:.1f} M€")
    print(f"montant UE reconstitué : {df['montant_ue'].sum() / 1e6:.1f} M€")
    print(
        f"taux de cofinancement : min {df['taux_ue'].min():.3f} / max {df['taux_ue'].max():.3f}"
    )
    print(
        f"opérations sans département renseigné : {(df['departements'].apply(len) == 0).sum()}"
    )
    ecl = eclater_departements(df)
    print(f"\néclatement : {len(ecl)} couples (opération, département)")
    localisables = df[df["departements"].apply(len) > 0]["montant_ue"].sum()
    ecart = abs(ecl["montant_ue_prorata"].sum() - localisables)
    print(f"contrôle de conservation du montant après prorata : écart = {ecart:.4f} €")
    print(
        f"montant UE non rattachable à un département : {(df['montant_ue'].sum() - localisables) / 1e6:.1f} M€"
    )

"""Q1 — Top 10 des opérations, groupement par département, croisement avec le revenu INSEE."""

import zipfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from commun import (
    DATA,
    DEPARTEMENTS_IDF,
    NOMS_DEPARTEMENTS,
    SORTIES,
    charger_operations,
    eclater_departements,
    ecrire,
    euros,
    normaliser_libelle,
)

df = charger_operations()

# ---------------------------------------------------------------- 1. Top 10 des opérations
top = df.nlargest(10, "montant_ue").copy()
top10 = pd.DataFrame(
    {
        "Bénéficiaire": top["beneficiaire"].str.slice(0, 38),
        "Opération": top["operation"].str.slice(0, 48),
        "Fonds": top["fonds_court"].values,
        "Coût total éligible (M€)": (top["cout_total"] / 1e6).round(2).values,
        "Taux UE": top["taux_ue"].round(3).values,
        "Montant UE (M€)": (top["montant_ue"] / 1e6).round(2).values,
    }
)
ecrire("q1_top10_operations", top10, "Top 10 des opérations par montant UE reconstitué")
print(
    f"\npoids du top 10 : {top['montant_ue'].sum() / df['montant_ue'].sum():.1%} "
    f"du montant UE total ({df['montant_ue'].sum() / 1e6:.1f} M€)"
)

# Le classement change-t-il si l'on trie sur le coût total plutôt que sur le montant UE ?
top_cout = set(df.nlargest(10, "cout_total")["operation"])
print(
    f"opérations communes aux deux classements (montant UE / coût total) : "
    f"{len(top_cout & set(top['operation']))}/10"
)

# --------------------------------------------------- 2. Groupement par département (tous fonds)
ecl = eclater_departements(df)
par_dep = (
    ecl.groupby("departement")
    .agg(
        nb_operations=("operation", "size"),
        montant_reparti=("montant_ue_prorata", "sum"),
    )
    .reset_index()
)
par_dep["nom"] = par_dep["departement"].map(NOMS_DEPARTEMENTS)
idf = par_dep[par_dep["nom"].notna()].sort_values("montant_reparti", ascending=False)

fonds_par_dep = (
    ecl[ecl["departement"].isin(DEPARTEMENTS_IDF)].pivot_table(
        index="departement",
        columns="fonds_court",
        values="montant_ue_prorata",
        aggfunc="sum",
        fill_value=0,
    )
    / 1e6
).round(2)

tableau_dep = pd.DataFrame(
    {
        "Département": (idf["departement"] + " " + idf["nom"]).values,
        "Opérations": idf["nb_operations"].values,
        "Montant UE réparti (M€)": (idf["montant_reparti"] / 1e6).round(2).values,
        "Part du total localisé": (
            idf["montant_reparti"] / idf["montant_reparti"].sum()
        )
        .map("{:.1%}".format)
        .values,
        "Montant moyen par opération (€)": euros(
            idf["montant_reparti"] / idf["nb_operations"]
        ).values,
    }
)
ecrire(
    "q1_par_departement",
    tableau_dep,
    "Fonds européens 2014-2020 par département francilien",
)

ecrire(
    "q1_par_departement_et_fonds",
    fonds_par_dep.reset_index().rename(columns={"departement": "Département"}),
    "Montant UE réparti par département et par fonds (M€)",
)

hors = par_dep[par_dep["nom"].isna()]
non_localise = df["montant_ue"].sum() - ecl["montant_ue_prorata"].sum()
print(
    f"\nhors Île-de-France : {int(hors['nb_operations'].sum())} rattachements, "
    f"{hors['montant_reparti'].sum() / 1e6:.2f} M€"
)
print(
    f"non rattachable à un département : {non_localise / 1e6:.1f} M€ "
    f"({non_localise / df['montant_ue'].sum():.1%} du montant UE)"
)

# ------------------------------------------- 3. Croisement avec le revenu médian INSEE (FiLoSoFi)
with zipfile.ZipFile(DATA / "insee_filosofi_2017_communes.zip").open(
    "FILO2017_DEC_COM.xlsx"
) as f:
    insee = pd.read_excel(f, sheet_name="ENSEMBLE", skiprows=5)
insee["CODGEO"] = insee["CODGEO"].astype(str)
insee = insee[insee["CODGEO"].str[:2].isin(DEPARTEMENTS_IDF)]
insee = insee[
    ~insee["CODGEO"].str.match(r"751\d\d")
]  # arrondissements : Paris est déjà agrégé
insee["cle"] = normaliser_libelle(insee["LIBGEO"])
ambigus = insee["cle"].duplicated(keep=False)
print(
    f"\nréférentiel INSEE : {len(insee)} communes franciliennes, "
    f"revenu médian renseigné pour {insee['Q217'].notna().sum()}"
)
if ambigus.any():
    print(f"  libellés ambigus écartés : {sorted(insee.loc[ambigus, 'LIBGEO'])}")
insee = insee[~ambigus]

# La localisation est du texte libre, plusieurs communes étant empilées avec « : ».
loc = df[["operation", "montant_ue", "localisation"]].copy()
loc["items"] = loc["localisation"].fillna("").str.split(":")
loc = loc.explode("items")
loc["cle"] = normaliser_libelle(loc["items"])
loc = loc[loc["cle"] != ""]
loc["montant_partage"] = loc["montant_ue"] / loc.groupby("operation")["cle"].transform(
    "size"
)

apparie = loc.merge(
    insee[["CODGEO", "LIBGEO", "cle", "Q217", "NBPERS17"]], on="cle", how="left"
)
communales = apparie[apparie["CODGEO"].notna()]
print(
    f"appariement des localisations : {communales['cle'].nunique()} communes reconnues, "
    f"{communales['operation'].nunique()} opérations sur {len(df)} "
    f"({communales['montant_partage'].sum() / df['montant_ue'].sum():.1%} du montant UE)"
)
print(
    "  principales localisations non appariées (non communales ou hors référentiel) :"
)
print(
    "   ",
    ", ".join(apparie[apparie["CODGEO"].isna()]["cle"].value_counts().head(8).index),
)

communes = (
    communales.groupby(["CODGEO", "LIBGEO"])
    .agg(montant_ue=("montant_partage", "sum"), nb_operations=("operation", "nunique"))
    .reset_index()
    .merge(insee[["CODGEO", "Q217", "NBPERS17"]], on="CODGEO")
)
communes["montant_par_habitant"] = communes["montant_ue"] / communes["NBPERS17"]

# Deuxième lecture : toutes les communes franciliennes, celles sans opération valant zéro.
toutes = insee[["CODGEO", "LIBGEO", "Q217", "NBPERS17"]].merge(
    communes[["CODGEO", "montant_ue"]], on="CODGEO", how="left"
)
toutes["montant_ue"] = toutes["montant_ue"].fillna(0)
toutes["montant_par_habitant"] = toutes["montant_ue"] / toutes["NBPERS17"]


def spearman(x, y):
    """Corrélation de rang, calculée comme un Pearson sur les rangs (évite une dépendance)."""
    return x.rank().corr(y.rank())


lignes = []
for libelle, jeu in [
    (f"communes financées (n={len(communes)})", communes),
    (f"toutes les communes franciliennes (n={len(toutes)})", toutes),
]:
    for variable, etiquette in [
        ("montant_ue", "montant UE total"),
        ("montant_par_habitant", "montant UE par habitant"),
    ]:
        lignes.append(
            {
                "Périmètre": libelle,
                "Variable corrélée au revenu médian": etiquette,
                "Pearson": jeu[variable].corr(jeu["Q217"]).round(3),
                "Spearman": round(spearman(jeu[variable], jeu["Q217"]), 3),
            }
        )
ecrire(
    "q1_correlation_revenu",
    pd.DataFrame(lignes),
    "Corrélation entre fonds européens et revenu médian déclaré (FiLoSoFi 2017)",
    floatfmt=".3f",
)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
for ax, (variable, titre) in zip(
    axes,
    [
        ("montant_ue", "Montant UE total par commune (€)"),
        ("montant_par_habitant", "Montant UE par habitant (€)"),
    ],
):
    ax.scatter(communes["Q217"], communes[variable], s=18, alpha=0.6, color="#1f4e79")
    ax.set_yscale("log")
    ax.set_xlabel("Revenu médian déclaré par UC en 2017 (€)")
    ax.set_ylabel(titre)
    r = communes[variable].corr(communes["Q217"])
    rho = spearman(communes[variable], communes["Q217"])
    ax.set_title(f"Pearson {r:.2f} | Spearman {rho:.2f}", fontsize=10)
    ax.grid(alpha=0.25)
fig.suptitle(
    f"Fonds européens 2014-2020 et revenu médian — {len(communes)} communes franciliennes financées",
    fontsize=11,
)
fig.tight_layout()
fig.savefig(SORTIES / "q1_correlation_revenu.png", dpi=150)
print("\nfigure écrite : sorties/q1_correlation_revenu.png")

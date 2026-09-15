"""Q4 — Évolution de la mobilisation des fonds européens par la Région Île-de-France
entre les programmations 2014-2020 et 2021-2027.

Les deux fichiers fournissent le coût total éligible et le taux de cofinancement : le montant UE
est donc reconstitué de la même façon des deux côtés, ce qui rend la comparaison homogène.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from commun import DATA, SORTIES, charger_operations, ecrire, euros

BLEU, ORANGE = "#1f4e79", "#e07b39"

# ------------------------------------------------------------------- Chargement des deux périodes
a = charger_operations()[
    ["operation", "fonds_court", "cout_total", "taux_ue", "montant_ue", "annee_debut"]
]
a["periode"] = "2014-2020"

b = pd.read_excel(
    DATA / "operations_feder_fse_ftj_2021_2027.xlsx",
    sheet_name="Liste des opérations septembre ",
)
b = b[b["Libellé Programme"].str.contains("Île-de-France", case=False, na=False)]
print(f"programme retenu pour 2021-2027 : {b['Libellé Programme'].unique()[0]}")
assert b["Libellé Programme"].nunique() == 1, (
    "plusieurs programmes capturés par le filtre"
)

b = pd.DataFrame(
    {
        "operation": b["Intitulé du projet"],
        "fonds_court": b["Fonds"],
        "cout_total": b["Total des dépenses éligibles"],
        "taux_ue": b["Taux de cofinancement"],
        "montant_ue": b["Total des dépenses éligibles"] * b["Taux de cofinancement"],
        "annee_debut": pd.to_datetime(b["Date de début de l'opération"]).dt.year,
    }
)
b["periode"] = "2021-2027"

tout = pd.concat([a, b], ignore_index=True)
DEBUT = {"2014-2020": 2014, "2021-2027": 2021}
tout["annee_programmation"] = tout["annee_debut"] - tout["periode"].map(DEBUT) + 1

# ------------------------------------------------------------------- Tableau de synthèse
synthese = tout.groupby("periode").agg(
    operations=("operation", "size"),
    cout_total=("cout_total", "sum"),
    montant_ue=("montant_ue", "sum"),
    moyen=("montant_ue", "mean"),
    median=("montant_ue", "median"),
)
synthese["taux_ue_moyen"] = synthese["montant_ue"] / synthese["cout_total"]
tableau = pd.DataFrame(
    {
        "Programmation": synthese.index,
        "Opérations publiées": synthese["operations"].values,
        "Coût total éligible (M€)": (synthese["cout_total"] / 1e6).round(1).values,
        "Montant UE (M€)": (synthese["montant_ue"] / 1e6).round(1).values,
        "Taux UE moyen": [f"{v:.1%}" for v in synthese["taux_ue_moyen"]],
        "Montant UE moyen par opération (€)": euros(synthese["moyen"]).values,
        "Montant UE médian par opération (€)": euros(synthese["median"]).values,
    }
)
ecrire("q4_synthese", tableau, "Deux programmations, état des listes publiées")

# ------------------------------------------------------------------- Graphique 1 : volumes par fonds
fonds_ordre = ["FEDER", "FSE", "IEJ", "FSE+"]
eff = (
    tout.pivot_table(
        index="fonds_court",
        columns="periode",
        values="operation",
        aggfunc="size",
        fill_value=0,
    )
    .reindex(fonds_ordre)
    .fillna(0)
)
mnt = (
    tout.pivot_table(
        index="fonds_court",
        columns="periode",
        values="montant_ue",
        aggfunc="sum",
        fill_value=0,
    )
    .reindex(fonds_ordre)
    .fillna(0)
    / 1e6
)

print("\nrépartition par fonds :")
print(pd.concat({"opérations": eff, "montant UE (M€)": mnt}, axis=1).to_string())

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
for ax, donnees, titre in [
    (axes[0], eff, "Nombre d'opérations publiées"),
    (axes[1], mnt, "Montant UE reconstitué (M€)"),
]:
    x = range(len(donnees))
    ax.bar(
        [i - 0.2 for i in x], donnees["2014-2020"], 0.4, label="2014-2020", color=BLEU
    )
    ax.bar(
        [i + 0.2 for i in x], donnees["2021-2027"], 0.4, label="2021-2027", color=ORANGE
    )
    ax.set_xticks(list(x), donnees.index)
    ax.set_title(titre, fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    for i, (v1, v2) in enumerate(zip(donnees["2014-2020"], donnees["2021-2027"])):
        ax.text(
            i - 0.2,
            v1,
            f"{v1:,.0f}".replace(",", " "),
            ha="center",
            va="bottom",
            fontsize=8,
        )
        ax.text(
            i + 0.2,
            v2,
            f"{v2:,.0f}".replace(",", " "),
            ha="center",
            va="bottom",
            fontsize=8,
        )
axes[0].legend(fontsize=9)
fig.suptitle("Île-de-France : listes d'opérations publiées par fonds", fontsize=12)
fig.tight_layout()
fig.savefig(SORTIES / "q4_volumes_par_fonds.png", dpi=150)

# ------------------------------------- Graphique 2 : cumul à millésime de programmation identique
cumul = (
    tout[tout["annee_programmation"].between(1, 7)]
    .pivot_table(
        index="annee_programmation",
        columns="periode",
        values="montant_ue",
        aggfunc="sum",
        fill_value=0,
    )
    .reindex(range(1, 8), fill_value=0)
    .cumsum()
    / 1e6
)
# La 5e année 21-27 (2025) n'est observée que jusqu'en septembre, les suivantes pas du tout :
# prolonger la courbe donnerait l'illusion d'un arrêt de la programmation.
cumul.loc[6:, "2021-2027"] = None

fig, ax = plt.subplots(figsize=(8, 4.6))
ax.plot(
    cumul.index,
    cumul["2014-2020"],
    marker="o",
    color=BLEU,
    label="2014-2020 (état mai 2022)",
)
ax.plot(
    cumul.index,
    cumul["2021-2027"],
    marker="o",
    color=ORANGE,
    label="2021-2027 (état sept. 2025)",
)
ax.axvline(5, color="grey", linestyle=":", linewidth=1)
ax.annotate(
    "horizon d'observation\nde la programmation\n21-27 (sept. 2025)",
    xy=(5.15, cumul["2014-2020"].max() * 0.25),
    fontsize=8,
    color="grey",
)
ax.set_xlabel(
    "Année de la programmation (1 = 2014 ou 2021, d'après la date de début d'opération)"
)
ax.set_ylabel("Montant UE cumulé (M€)")
ax.set_title("Mobilisation cumulée à millésime de programmation identique", fontsize=11)
ax.legend(fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(SORTIES / "q4_cumul_millesime.png", dpi=150)

n4 = cumul.loc[4]
print(
    f"\ncumul à la 4ᵉ année : 2014-2020 = {n4['2014-2020']:.1f} M€, "
    f"2021-2027 = {n4['2021-2027']:.1f} M€ "
    f"(soit {n4['2021-2027'] / n4['2014-2020']:.0%} du rythme précédent)"
)
eff4 = tout[tout["annee_programmation"] <= 4].groupby("periode").size()
print(f"opérations démarrées dans les 4 premières années : {eff4.to_dict()}")

# ------------------------------------------------------------------- Graphique 3 : taille des opérations
fig, ax = plt.subplots(figsize=(8, 4.6))
donnees = [tout.loc[tout["periode"] == p, "montant_ue"] / 1e3 for p in DEBUT]
ax.boxplot(
    donnees,
    tick_labels=list(DEBUT),
    showfliers=False,
    medianprops=dict(color="black"),
    widths=0.5,
)
for i, serie in enumerate(donnees, start=1):
    ax.scatter(
        [i],
        [serie.mean()],
        marker="D",
        color=ORANGE,
        zorder=3,
        label="moyenne" if i == 1 else None,
    )
ax.set_ylabel("Montant UE par opération (k€, valeurs extrêmes masquées)")
ax.set_title("Des opérations moins nombreuses mais nettement plus grosses", fontsize=11)
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(SORTIES / "q4_taille_operations.png", dpi=150)

print(
    "\nfigures écrites : q4_volumes_par_fonds.png, q4_cumul_millesime.png, q4_taille_operations.png"
)

# Réserve de comparabilité : le fichier 21-27 est national, la part IdF y est minoritaire.
national = pd.read_excel(
    DATA / "operations_feder_fse_ftj_2021_2027.xlsx",
    sheet_name="Liste des opérations septembre ",
)
print(
    f"\nfichier 21-27 : {len(national)} opérations toutes régions, dont {len(b)} "
    f"pour le programme francilien ({len(b) / len(national):.1%})"
)
print(
    f"localisation 21-27 : département renseigné pour "
    f"{national['Département de l’opération'].notna().sum()}/{len(national)} lignes au national"
)

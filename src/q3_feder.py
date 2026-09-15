"""Q3 — Les 3 départements franciliens avec le plus d'opérations FEDER 2014-2020,
et le montant moyen par opération pour chacun."""

import pandas as pd

from commun import (
    NOMS_DEPARTEMENTS,
    charger_operations,
    eclater_departements,
    ecrire,
    euros,
)

df = charger_operations()
feder = df[df["fonds_court"] == "FEDER"]
nb_multi = feder["departements"].apply(len).gt(1).sum()
print(
    f"{len(feder)} opérations FEDER sur {len(df)} au total, "
    f"dont {nb_multi} rattachées à plusieurs départements"
)

ecl = eclater_departements(feder)

par_dep = (
    ecl.groupby("departement")
    .agg(
        nb_operations=("operation", "size"),
        montant_reparti=("montant_ue_prorata", "sum"),
        moyen_integral=("montant_ue", "mean"),
    )
    .reset_index()
    .sort_values("nb_operations", ascending=False)
)
par_dep["moyen_reparti"] = par_dep["montant_reparti"] / par_dep["nb_operations"]
par_dep["nom"] = par_dep["departement"].map(NOMS_DEPARTEMENTS)

francilien = par_dep[par_dep["nom"].notna()]

tableau = pd.DataFrame(
    {
        "Département": (francilien["departement"] + " " + francilien["nom"]).values,
        "Opérations FEDER": francilien["nb_operations"].values,
        "Montant UE réparti (M€)": (francilien["montant_reparti"] / 1e6)
        .round(2)
        .values,
        "Montant moyen par opération (€)": euros(francilien["moyen_integral"]).values,
        "Variante au prorata (€)": euros(francilien["moyen_reparti"]).values,
    }
)

ecrire(
    "q3_feder_par_departement", tableau, "FEDER 2014-2020 par département francilien"
)

print("\n>>> Réponse Q3")
for _, r in francilien.head(3).iterrows():
    print(
        f"  {r['departement']} {r['nom']} : {int(r['nb_operations'])} opérations FEDER, "
        f"montant UE moyen par opération {r['moyen_integral']:,.0f} € "
        f"(au prorata : {r['moyen_reparti']:,.0f} €)".replace(",", " ")
    )

# Contrôle de robustesse : même classement si l'on ne garde que les opérations mono-départementales.
mono = (
    ecl[ecl["nb_departements"] == 1]
    .groupby("departement")
    .size()
    .sort_values(ascending=False)
)
mono_idf = mono[mono.index.isin(NOMS_DEPARTEMENTS)]
print(
    "\nclassement sur les seules opérations mono-départementales :",
    ", ".join(f"{d} ({n})" for d, n in mono_idf.head(3).items()),
)

# Contrôle : les effectifs reproduisent le comptage brut du champ multivalué.
attendu = feder.explode("departements")["departements"].value_counts().sort_index()
obtenu = par_dep.set_index("departement")["nb_operations"].sort_index()
assert obtenu.equals(attendu), "effectifs incohérents avec la source"
print("contrôle des effectifs : conforme au comptage brut de la source")

hors_idf = par_dep[par_dep["nom"].isna()]
print(
    f"\nrattachements hors Île-de-France recensés (voir Q2) : "
    f"{', '.join(hors_idf['departement'])}"
)

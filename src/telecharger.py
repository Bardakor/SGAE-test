"""Télécharge les trois sources de l'étude dans data/ et journalise ce qui a été récupéré.

Les fichiers déjà présents ne sont pas retéléchargés (relancer après un rm pour rafraîchir).
"""

import urllib.request
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

SOURCES = {
    "operations_idf_2014_2020.json": "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/gestion-des-fonds-europeens-liste-des-operations/exports/json",
    "insee_filosofi_2017_communes.zip": "https://www.insee.fr/fr/statistiques/fichier/4291712/indic-struct-distrib-revenu-2017-COMMUNES.zip",
    "operations_feder_fse_ftj_2021_2027.xlsx": "https://www.europe-en-france.gouv.fr/sites/default/files/2025-09/20250908_liste_operations_feder_fse_ftj.xls.xlsx",
}


def main():
    DATA.mkdir(exist_ok=True)
    journal = []
    for nom, url in SOURCES.items():
        cible = DATA / nom
        if not cible.exists():
            print(f"téléchargement : {nom}")
            urllib.request.urlretrieve(url, cible)
        taille = cible.stat().st_size / 1e6
        horodatage = datetime.fromtimestamp(cible.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M"
        )
        journal.append(f"| {nom} | {taille:.1f} Mo | {horodatage} | {url} |")
        print(f"  {nom} : {taille:.1f} Mo (récupéré le {horodatage})")

    entete = "| Fichier | Taille | Récupéré le | Source |\n|---|---|---|---|"
    (DATA.parent / "sorties" / "journal_telechargement.md").write_text(
        entete + "\n" + "\n".join(journal) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

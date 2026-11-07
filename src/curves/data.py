import re
from pathlib import Path
import numpy as np
import pandas as pd


def mat(nom_colonne):
    """Maturité en années d'une colonne de taux spot (None si ce n'en est pas une).

    Exemple : '... .SR_2Y8M)' -> 2 + 8/12.
    """
    m = re.search(r"\.SR_(.*)\)$", nom_colonne)  # se termine par .SR_xxx)
    if not m:
        return None
    annees = re.search(r"(\d+)Y", m.group(1))     # nombre suivi de Y
    mois = re.search(r"(\d+)M", m.group(1))       # nombre suivi de M
    return (int(annees.group(1)) if annees else 0) + (int(mois.group(1)) if mois else 0) / 12


def charger_courbe(chemin):
    """Lit le CSV de la BCE et renvoie les taux spot AAA.

    Retourne un DataFrame : une ligne par date, une colonne par maturité
    (en années, de la plus courte à la plus longue). Les taux sont en
    décimal par an (0.03 = 3 %), convertis ici depuis les pourcentages
    du fichier.
    """
    df = pd.read_csv(Path(chemin))
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df.set_index("DATE")

    T = pd.Series({c: mat(c) for c in df.columns}).dropna()  # écarte TIME PERIOD et SRS_...

    courbe = (df[T.index]                    
              .rename(columns=T.to_dict())   
              .sort_index(axis=1) / 100) # % -> décimal
    return courbe

def _code(nom):
    """'... (YC....BETA0)' -> 'BETA0' ; renvoie le nom tel quel s'il n'y a pas de code."""
    m = re.search(r"\.([A-Z]+\d)\)$", nom)
    return m.group(1) if m else nom


def charger_parametres(chemin):
    """Lit les paramètres de Svensson publiés par la BCE.

    Une ligne par date, colonnes BETA0..BETA3, TAU1, TAU2.
    BETA0 à BETA3 sont en décimal par an (convertis depuis les %),
    TAU1 et TAU2 sont des durées en années, non converties.
    """
    param = pd.read_csv(Path(chemin)).rename(columns=_code)
    param["DATE"] = pd.to_datetime(param["DATE"])
    param = param.set_index("DATE").drop(columns="TIME PERIOD")
    cols_beta = ["BETA0", "BETA1", "BETA2", "BETA3"]
    param[cols_beta] = param[cols_beta] / 100
    return param


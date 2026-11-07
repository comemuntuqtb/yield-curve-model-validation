import numpy as np
import pandas as pd

def rmse(residus):
    """Racine de la moyenne des carrés des résidus.

    Même unité que les résidus. Le signe disparaît à cause du carré :
    la RMSE mesure l'amplitude des erreurs, pas leur biais.
    """
    residus = np.asarray(residus)
    return np.sqrt(np.mean(residus ** 2))

#sans prendre en arg la matrice des ratios des seuils dépassés
# def stats_par_tranche(res, bornes):
#     """Biais, écart-type et RMSE par tranche de colonnes.

#     res : DataFrame de résidus (observé - modèle), une ligne par observation
#         (par exemple une date), une colonne par point de l'axe (par exemple
#         une maturité). Les noms de colonnes sont des nombres.
#     bornes : liste croissante de bornes, par exemple [0, 2, 5, 10, 20, 30].
#         Chaque tranche est ]lo, hi] (même convention que choisir_caches).

#     Retourne un DataFrame indexé par tranche, avec les colonnes "biais"
#     (moyenne, signe conservé), "ecart_type" (ddof=0, calculé sur toutes les
#     cellules du bloc) et "rmse", dans l'unité des résidus.
#     Identité exacte : rmse**2 = biais**2 + ecart_type**2.
#     """
#     colonnes = res.columns.to_numpy(dtype=float)
#     valeurs = res.to_numpy()
#     lignes = {}
#     for lo, hi in zip(bornes[:-1], bornes[1:]):
#         masque = (colonnes > lo) & (colonnes <= hi)
#         if not masque.any():
#             raise ValueError(f"Aucune colonne dans ]{lo}, {hi}]")
#         bloc = valeurs[:, masque]
#         lignes[f"]{lo}, {hi}]"] = {"biais": bloc.mean(),
#                                   "ecart_type": bloc.std(),
#                                   "rmse": rmse(bloc)}
#     return pd.DataFrame(lignes).T

def stats_par_tranche(res, bornes, ratio=None):
    """Biais, écart-type, RMSE (et dépassements) par tranche de colonnes.

    res : DataFrame de résidus (observé - modèle), une ligne par observation
        (par exemple une date), une colonne par point de l'axe (par exemple
        une maturité). Les noms de colonnes sont des nombres.
    bornes : liste croissante de bornes, par exemple [0, 2, 5, 10, 20, 30].
        Chaque tranche est ]lo, hi] (même convention que choisir_caches).
    ratio : DataFrame facultatif, de mêmes lignes et colonnes que res
        (par exemple |résidu| / seuil). S'il est fourni, ajoute la colonne
        "depassement" : proportion de cellules du bloc avec ratio > 1.

    Retourne un DataFrame indexé par tranche, avec les colonnes "biais"
    (moyenne, signe conservé), "ecart_type" (ddof=0, sur toutes les cellules
    du bloc), "rmse" (dans l'unité des résidus) et, si ratio est fourni,
    "depassement" (entre 0 et 1).
    Identité exacte : rmse**2 = biais**2 + ecart_type**2.
    """
    colonnes = res.columns.to_numpy(dtype=float)
    valeurs = res.to_numpy()
    if ratio is not None:
        if not (ratio.index.equals(res.index) and ratio.columns.equals(res.columns)):
            raise ValueError("ratio doit avoir les mêmes lignes et colonnes que res.")
        valeurs_ratio = ratio.to_numpy()
    lignes = {}
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        masque = (colonnes > lo) & (colonnes <= hi)
        if not masque.any():
            raise ValueError(f"Aucune colonne dans ]{lo}, {hi}]")
        bloc = valeurs[:, masque]
        ligne = {"biais": bloc.mean(),
                 "ecart_type": bloc.std(),
                 "rmse": rmse(bloc)}
        if ratio is not None:
            ligne["depassement"] = (valeurs_ratio[:, masque] > 1).mean()
        lignes[f"]{lo}, {hi}]"] = ligne
    return pd.DataFrame(lignes).T

def quantiles_par_tranche(res, bornes, quantiles=(0.5, 0.75, 0.9, 0.95)):
    """Quantiles de |résidu| par tranche de colonnes.

    res : DataFrame de résidus (observé - modèle), colonnes = points de l'axe
        (par exemple des maturités), noms numériques.
    bornes : liste croissante de bornes ; chaque tranche est ]lo, hi].
    quantiles : niveaux entre 0 et 1.

    Retourne un DataFrame indexé par tranche, une colonne par quantile
    ("q50", "q75", ...), dans l'unité des résidus. Les quantiles portent sur
    toutes les cellules du bloc, en valeur absolue.
    """
    colonnes = res.columns.to_numpy(dtype=float)
    valeurs = np.abs(res.to_numpy())
    lignes = {}
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        masque = (colonnes > lo) & (colonnes <= hi)
        if not masque.any():
            raise ValueError(f"Aucune colonne dans ]{lo}, {hi}]")
        bloc = valeurs[:, masque].ravel()
        lignes[f"]{lo}, {hi}]"] = {f"q{round(q * 100)}": np.quantile(bloc, q) for q in quantiles}
    return pd.DataFrame(lignes).T

def autocorrelation_par_tranche(res, bornes):
    """Autocorrélation à un retard de la série moyenne par tranche.

    res : DataFrame de résidus (observé - modèle), une ligne par date (index
        trié dans le temps), colonnes = points de l'axe (noms numériques).
    bornes : liste croissante de bornes ; chaque tranche est ]lo, hi].

    Pour chaque tranche : série à une valeur par date (moyenne signée des
    colonnes de la tranche), puis rho = corrélation entre la série et la série
    décalée d'un cran, n_eff = n (1 - rho) / (1 + rho) (approximation AR(1),
    peu fiable quand rho est proche de 1).
    Retourne un DataFrame indexé par tranche : n, rho, n_eff.
    """
    colonnes = res.columns.to_numpy(dtype=float)
    valeurs = res.to_numpy()
    lignes = {}
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        masque = (colonnes > lo) & (colonnes <= hi)
        if not masque.any():
            raise ValueError(f"Aucune colonne dans ]{lo}, {hi}]")
        serie = pd.Series(valeurs[:, masque].mean(axis=1), index=res.index)
        rho = serie.autocorr(lag=1)          # Pearson : moyennes retirées automatiquement
        n = len(serie)
        lignes[f"]{lo}, {hi}]"] = {"n": n, "rho": rho, "n_eff": n * (1 - rho) / (1 + rho)}
    return pd.DataFrame(lignes).T
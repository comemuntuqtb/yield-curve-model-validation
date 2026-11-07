import numpy as np
import pandas as pd
import statsmodels.api as sm


def newey_west_biais(x, n_lags=None):
    """Test de biais moyen robuste à l'autocorrélation (Newey-West) via statsmodels.

    x : série à une valeur par date (tableau 1D, trié dans le temps).
    n_lags : nombre de jour retards ; par défaut floor(4 (n/100)^(2/9)) : environ 6 à 9 retard
    Régression de x sur une constante : le coefficient est la moyenne, son
    erreur-type est l'erreur-type HAC (noyau de Bartlett, sans correction de
    petit échantillon). p-valeur bilatérale, approximation normale.
    Retourne un dict : n, n_lags, biais, se, t, p.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n_lags is None:
        n_lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    fit = sm.OLS(x, np.ones(n)).fit(cov_type="HAC",
                                    cov_kwds={"maxlags": n_lags, "use_correction": False}) 
    return {"n": n, "n_lags": n_lags, "biais": float(fit.params[0]),
            "se": float(fit.bse[0]), "t": float(fit.tvalues[0]), "p": float(fit.pvalues[0])}


def test_biais_par_tranche(res, bornes, n_lags=None):
    """Test de biais Newey-West par tranche, sur la série moyenne par date.

    res : DataFrame de résidus (une ligne par date triée, colonnes numériques).
    Retourne un DataFrame indexé par tranche (n, n_lags, biais, se, t, p),
    biais et se dans l'unité des résidus.
    """
    colonnes = res.columns.to_numpy(dtype=float)
    valeurs = res.to_numpy()
    lignes = {}
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        masque = (colonnes > lo) & (colonnes <= hi)
        if not masque.any():
            raise ValueError(f"Aucune colonne dans ]{lo}, {hi}]")
        lignes[f"]{lo}, {hi}]"] = newey_west_biais(valeurs[:, masque].mean(axis=1), n_lags)
    return pd.DataFrame(lignes).T
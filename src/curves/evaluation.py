from src.validation.residue import rmse
import pandas as pd
import numpy as np
def evaluer_date(T, taux_obs, masque_cache, fit, rate):
    """Ajuste un modèle de courbe sur les points d'ancrage et l'évalue sur les points cachés.

    Paramètres
    ----------
    T : tableau de maturités en années (toute la grille).
    taux_obs : tableau de taux observés pour une date, en décimal par an.
    masque_cache : tableau de booléens, True pour les maturités cachées.
        Il doit être le même pour tous les modèles comparés.
    fit : fonction d'ajustement, par exemple fit_ns ou fit_sv.
        Appelée fit(T_ancrage, taux_ancrage), elle renvoie un objet dont
        l'attribut .x contient les paramètres.
    rate : fonction de taux du modèle, par exemple ns_rate ou sv_rate.
        Appelée rate(T, *params), elle renvoie les taux du modèle.

    Retourne
    -------
    Un dictionnaire avec :
        "params" : paramètres ajustés (res.x)
        "rmse_ancrage" : RMSE sur les points d'ajustement (décimal par an)
        "rmse_cache" : RMSE sur les points cachés (décimal par an)
        "residus_cache" : résidus sur les points cachés, observé - modèle
    """

    y = taux_obs                       # taux observés de la date
    T_ancrage, T_cache = T[~masque_cache], T[masque_cache]
    y_ancrage, y_cache = y[~masque_cache], y[masque_cache]

    res = fit(T_ancrage, y_ancrage)                # ajustement sur l'ancrage seulement
    residus_cache = y_cache - rate(T_cache, *res.x)   # observé - modèle, points jamais vus


    return {"params": res.x,
            "rmse_ancrage": rmse(res.fun),
            "rmse_cache": rmse(residus_cache),
            "residus_cache": residus_cache}
    
def ajuster_historique(courbe, fit, rate, nom_params, x_depart=None, pas_affichage=500):
    """Ajuste un modèle de courbe date par date, en partant de la veille.

    courbe : DataFrame (dates x maturités en années), taux en décimal.
    fit : fit_ns ou fit_sv, appelée fit(T, taux_obs, x_prev=...).
    rate : ns_rate ou sv_rate.
    nom_params : noms des paramètres, dans l'ordre de res.x.
    x_depart : paramètres de départ pour la première date (facultatif).

    Retourne un DataFrame indexé par date : une colonne par paramètre,
    "rmse_pb" (toute la courbe, en pb), "succes" (convergence de scipy)
    et "repli" (grille complète relancée).
    """
    T = courbe.columns.to_numpy(dtype=float)
    x_prev = x_depart
    lignes = []

    for i, (date, taux) in enumerate(courbe.iterrows()):
        y = taux.to_numpy(dtype=float)
        res = fit(T, y, x_prev=x_prev)
        x_prev = res.x                                  # départ du lendemain
        lignes.append({**dict(zip(nom_params, res.x)),
                       "rmse_pb": rmse(y - rate(T, *res.x)) * 1e4,
                       "succes": bool(res.success),
                       "repli": bool(res.repli)})
        if pas_affichage and (i + 1) % pas_affichage == 0:
            print(f"{i + 1}/{len(courbe)} dates ({date.date()})")

    return pd.DataFrame(lignes, index=courbe.index)

def residus_historique(courbe, hist, rate, nom_params):
    """Résidus observé - modèle pour toutes les dates et toutes les maturités. On les recalcules

    courbe : DataFrame (dates x maturités en années), taux en décimal.
    hist : DataFrame de paramètres (sortie de ajuster_historique), même index.
    rate : ns_rate ou sv_rate.
    nom_params : noms des colonnes de paramètres, dans l'ordre attendu par rate.

    Retourne un DataFrame de même forme que courbe (décimal par an).
    """
    if not courbe.index.equals(hist.index):
        raise ValueError("Les dates de courbe et de hist ne correspondent pas.")
    T = courbe.columns.to_numpy(dtype=float)                       # (n_mat,)
    params = [hist[p].to_numpy()[:, None] for p in nom_params]     # chacun (n_dates, 1)
    taux_modele = rate(T, *params)                                 # (n_dates, n_mat)
    return courbe - taux_modele

def seuil_taux(T, tolerance_prix=0.001, plancher_pb=4.0):
    """Seuil d'erreur de taux admissible à chaque maturité (décimal par an).

    seuil(T) = max(tolerance_prix / T, plancher), convention continue.
    T : tableau de maturités en années. plancher_pb : plancher en points de base.
    """
    T = np.asarray(T, dtype=float)
    return np.maximum(tolerance_prix / T, plancher_pb * 1e-4)


def ratio_erreur_seuil(res, tolerance_prix=0.001, plancher_pb=4.0):
    """Ratio |résidu| / seuil pour chaque couple (date, maturité).

    res : DataFrame de résidus (observé - modèle), colonnes = maturités en années.
    Un ratio > 1 signifie que l'erreur dépasse le seuil admissible.
    Retourne un DataFrame de même forme que res.
    """
    seuil = seuil_taux(res.columns.to_numpy(dtype=float), tolerance_prix, plancher_pb)  # (n_mat,)
    return res.abs() / seuil        # (n_dates, n_mat) / (n_mat,) : broadcasting
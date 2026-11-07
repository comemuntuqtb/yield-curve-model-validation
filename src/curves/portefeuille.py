import numpy as np
import pandas as pd


def flux_obligations(maturites, coupon=0.03, nominal=100.0):
    """Matrice (n_obligations, t_max) des flux aux dates t = 1, ..., t_max (coupon annuel).

    maturites : liste d'entiers (années). Le nominal est remboursé à la dernière date.
    """
    t_max = int(max(maturites))
    flux = np.zeros((len(maturites), t_max))
    for i, m in enumerate(maturites):
        flux[i, :m] = coupon * nominal
        flux[i, m - 1] += nominal
    return flux


def choc_parallele(pb):
    """Choc parallèle de pb points de base sur tous les taux (fonction de t)."""
    return lambda t: pb * 1e-4 * np.ones_like(t)


def choc_pente(pb_par_an, pivot):
    """Choc de pente : pb_par_an points de base par année d'écart au pivot (en années)."""
    return lambda t: pb_par_an * 1e-4 * (t - pivot)


def prix_obligations(hist, rate, noms_params, flux, choc=None):
    """Prix de chaque obligation à chaque date, courbe continue : somme des flux x exp(-r(t) t).

    hist : DataFrame de paramètres (une ligne par date, sortie de ajuster_historique).
    rate : ns_rate ou sv_rate. noms_params : colonnes de hist, dans l'ordre de rate.
    flux : matrice (n_obligations, t_max). choc : fonction de t (décimal) ajoutée aux taux, ou None.
    Retourne un DataFrame (dates x obligations).
    """
    t = np.arange(1, flux.shape[1] + 1, dtype=float)                 # (t_max,)
    params = [hist[p].to_numpy()[:, None] for p in noms_params]      # chacun (n_dates, 1)
    r = rate(t, *params)                                             # (n_dates, t_max)
    if choc is not None:
        r = r + choc(t)
    return pd.DataFrame(np.exp(-r * t) @ flux.T, index=hist.index)


def erreurs_valorisation(hist_ref, rate_ref, noms_ref, hist_mod, rate_mod, noms_mod, flux, choc):
    """Erreur de valeur et erreur de sensibilité du modèle par rapport à la référence.

    Les deux historiques doivent avoir les mêmes dates.
    Retourne deux DataFrames (dates x obligations + colonne "portefeuille", poids égaux) :
    - valeur : prix_mod / prix_ref - 1 (courbe inchangée) ;
    - sensibilite : (variation relative de prix sous choc avec le modèle)
                    - (variation relative de prix sous choc avec la référence).
    """
    if not hist_ref.index.equals(hist_mod.index):
        raise ValueError("Les deux historiques doivent avoir les mêmes dates.")
    p_ref = prix_obligations(hist_ref, rate_ref, noms_ref, flux)
    p_mod = prix_obligations(hist_mod, rate_mod, noms_mod, flux)
    c_ref = prix_obligations(hist_ref, rate_ref, noms_ref, flux, choc)
    c_mod = prix_obligations(hist_mod, rate_mod, noms_mod, flux, choc)
    for p in (p_ref, p_mod, c_ref, c_mod):
        p["portefeuille"] = p.sum(axis=1)                            # nominaux égaux
    valeur = p_mod / p_ref - 1
    sensibilite = (c_mod / p_mod - 1) - (c_ref / p_ref - 1)
    return valeur, sensibilite

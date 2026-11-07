import numpy as np
import itertools
from scipy.optimize import least_squares

def sv_rate(T, beta0, beta1, beta2, beta3, tau1, tau2):
    """Calcul le taux du modèle de svensson en prenant un entrée un tableau

    Returns:
        taux_sv
    """
    x1 = T / tau1
    x2 = T / tau2
    A1 = (1 - np.exp(-x1)) / x1
    A2 = (1 - np.exp(-x2)) / x2         
    B1 = A1 - np.exp(-x1)
    B2 = A2 - np.exp(-x2)
    r = beta0 + beta1 * A1 + beta2 * B1 + beta3 * B2
    return r

def _residus(params, T, taux_obs):
    """Résidus de Svensson, à minimiser par moindres carrés.

    Convention : résidu = observé - modèle.

    Paramètres
    ----------
    params : liste [beta0, beta1, beta2, beta3, tau1, tau2]
        Les inconnues, en décimal par an pour les beta et en années pour tau pour scipy.optimize.least_squares.
    T : tableau de maturités en années (donnée fixe).
    taux_obs : tableau de taux observés en décimal par an (donnée fixe).

    Retourne
    -------
    Tableau de même taille que T : un résidu par maturité.
    """
    
    beta0, beta1, beta2, beta3, tau1,tau2 = params
    taux_mdl = sv_rate(T, beta0, beta1, beta2, beta3, tau1,tau2)
    return taux_obs - taux_mdl


# anciennes fonctions avec grille de taux plus petite
# def fit_sv(T, taux_obs, x_prev=None, seuil_repli_pb=0.05):
#     """Ajuste Svensson à la courbe d'une date, avec plusieurs points de départ.
#     Car selon les tau de départs on a des RMSE différénts et on ne retrouve pas les param de la BCE.
    

#     Si x_prev (paramètres de la veille) est fourni, on essaie d'abord ce seul
#     départ. Si la RMSE obtenue est <= seuil_repli_pb (en points de base), on
#     s'arrête là. Sinon, repli : grille complète (tau1, tau2), x_prev inclus,
#     et on garde le plus petit cost. Le seuil est une règle technique de repli,
#     pas un critère de validation.

#     Retourne le résultat de least_squares (.x = 6 paramètres), avec un
#     attribut .repli (True si la grille complète a été relancée après échec
#     du départ de la veille).
#     """
#     bornes = ([-np.inf]*4 + [1e-6]*2, [np.inf]*6)

#     resultats = []
#     if x_prev is not None:
#         res = least_squares(_residus, list(x_prev), args=(T, taux_obs), bounds=bornes)
#         if np.sqrt(np.mean(res.fun ** 2)) * 1e4 <= seuil_repli_pb:
#             res.repli = False
#             return res
#         resultats.append(res)

#     beta0 = taux_obs[T > 20].mean()                 # niveau long terme
#     beta1 = taux_obs[T < 1].mean() - beta0          # court terme - long terme
#     departs = [[beta0, beta1, 0.0, 0.0, t1, t2]
#                for t1, t2 in itertools.product(np.geomspace(0.5, 8, 4),
#                                                np.geomspace(3, 30, 4))
#                if not np.isclose(t1, t2)]
#     resultats += [least_squares(_residus, x0, args=(T, taux_obs), bounds=bornes)
#                   for x0 in departs]

#     res = min(resultats, key=lambda r: r.cost)
#     res.repli = x_prev is not None      # première date : pas de repli, c'est la voie normale
#     return res

# #la grille précédente était plus petite que celle de la BCE qui nous donnaient des résidus élevées sur 77 dates
# def fit_sv_grille_large(T, taux_obs, taus=None):
#     """Ajuste Svensson depuis une grille large de départs, sans paramètres BCE.

#     taus : valeurs de tau testées pour tau1 ET tau2 (toutes les paires ordonnées,
#         sauf tau1 = tau2). Par défaut : 8 valeurs de 0,25 à 30 ans (échelle géométrique).
#     Retourne le résultat de least_squares de plus petit cost (.x = 6 paramètres).
#     """
#     if taus is None:
#         taus = np.geomspace(0.25, 30, 8)
#     beta0 = taux_obs[T > 20].mean()
#     beta1 = taux_obs[T < 1].mean() - beta0
#     departs = [[beta0, beta1, 0.0, 0.0, t1, t2]
#                for t1, t2 in itertools.product(taus, taus) if not np.isclose(t1, t2)]
#     bornes = ([-np.inf] * 4 + [1e-6] * 2, [np.inf] * 6)
#     resultats = [least_squares(_residus, x0, args=(T, taux_obs), bounds=bornes) for x0 in departs]
#     return min(resultats, key=lambda r: r.cost)

TAUS_GRILLE = np.geomspace(0.25, 30, 8)      # même plage pour tau1 et tau2 (grille large)
BORNES_SV = ([-np.inf] * 4 + [1e-6] * 2, [np.inf] * 6)


def _departs_grille(T, taux_obs, taus=TAUS_GRILLE):
    """Points de départ : toutes les paires ordonnées (tau1, tau2) de taus, sauf tau1 = tau2."""
    beta0 = taux_obs[T > 20].mean()
    beta1 = taux_obs[T < 1].mean() - beta0
    return [[beta0, beta1, 0.0, 0.0, t1, t2]
            for t1, t2 in itertools.product(taus, taus) if not np.isclose(t1, t2)]


def fit_sv_grille_large(T, taux_obs, taus=TAUS_GRILLE):
    """Ajuste Svensson depuis la grille large de départs, sans x_prev."""
    resultats = [least_squares(_residus, x0, args=(T, taux_obs), bounds=BORNES_SV)
                 for x0 in _departs_grille(T, taux_obs, taus)]
    return min(resultats, key=lambda r: r.cost)


def fit_sv(T, taux_obs, x_prev=None, seuil_repli_pb=0.05, taus=TAUS_GRILLE):
    """Ajuste Svensson à la courbe d'une date.

    Si x_prev est fourni, on essaie d'abord ce seul départ ; si la RMSE obtenue
    est <= seuil_repli_pb, on s'arrête (res.repli = False). Sinon (ou si x_prev
    est None), grille large (tau1, tau2) ∈ taus x taus, x_prev inclus, et on
    garde le plus petit cost. res.repli vaut True si la grille a été relancée
    après échec du départ de la veille (False pour la première date).
    """
    resultats = []
    if x_prev is not None:
        res = least_squares(_residus, list(x_prev), args=(T, taux_obs), bounds=BORNES_SV)
        if np.sqrt(np.mean(res.fun ** 2)) * 1e4 <= seuil_repli_pb:
            res.repli = False
            return res
        resultats.append(res)
    resultats += [least_squares(_residus, x0, args=(T, taux_obs), bounds=BORNES_SV)
                  for x0 in _departs_grille(T, taux_obs, taus)]
    res = min(resultats, key=lambda r: r.cost)
    res.repli = x_prev is not None
    return res
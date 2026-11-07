import numpy as np
from scipy.optimize import least_squares

def ns_rate(T, beta0, beta1, beta2, tau):
    """Calcul le taux du modèle NS en prenant un entrée un tableau

    Returns:
        taux_ns
    """
    x=T/tau
    A=(1-np.exp(-x))/x
    B=A-np.exp(-x)
    r=beta0+beta1*A+beta2*B
    return r

def _residus(params, T, taux_obs):
    """Résidus de Nelson-Siegel, à minimiser par moindres carrés.

    Convention : résidu = observé - modèle.

    Paramètres
    ----------
    params : liste [beta0, beta1, beta2, tau]
        Les inconnues, en décimal par an pour les beta et en années pour tau pour scipy.optimize.least_squares.
    T : tableau de maturités en années (donnée fixe).
    taux_obs : tableau de taux observés en décimal par an (donnée fixe).

    Retourne
    -------
    Tableau de même taille que T : un résidu par maturité.
    """
    
    beta0, beta1, beta2, tau = params
    taux_mdl = ns_rate(T, beta0, beta1, beta2, tau)
    return taux_obs - taux_mdl


def fit_ns(T, taux_obs, x_prev=None):
    """Ajuste Nelson-Siegel à la courbe d'une date par moindres carrés.

    Même signature que fit_sv. Deux départs : le départ standard et, si fourni,
    x_prev (paramètres de la veille) ; on garde le plus petit cost.
    Retourne le résultat de least_squares (.x = [beta0, beta1, beta2, tau]),
    avec un attribut .repli = False (Nelson-Siegel n'a pas de repli).
    """
    beta0 = taux_obs[T > 20].mean()                 # niveau long terme
    beta1 = taux_obs[T < 1].mean() - beta0          # court terme - long terme
    departs = [[beta0, beta1, 0., 2.]] #beta2 à 0 on commence avec une courbe sans bosse et taux =2 car on a la bosse à tau*1.8
    if x_prev is not None:
        departs.append(list(x_prev))
    bornes = ([-np.inf, -np.inf, -np.inf, 1e-6],    # minimums
              [np.inf, np.inf, np.inf, np.inf])     # maximums : seul tau > 0 est borné
    resultats = [least_squares(_residus, x0, args=(T, taux_obs), bounds=bornes)
                 for x0 in departs]
    res = min(resultats, key=lambda r: r.cost)
    res.repli = False
    return res
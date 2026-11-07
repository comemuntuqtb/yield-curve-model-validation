import numpy as np
import pandas as pd

from src.curves.nelson_siegel import ns_rate
from src.curves.portefeuille import (choc_parallele, choc_pente, flux_obligations,
                                     prix_obligations)

NOMS_NS = ["beta0", "beta1", "beta2", "tau"]


def _courbe_plate(taux=0.03):
    return pd.DataFrame({"beta0": [taux], "beta1": [0.0], "beta2": [0.0], "tau": [2.0]},
                        index=pd.date_range("2020-01-01", periods=1))


def test_prix_courbe_plate_continu():
    flux = flux_obligations([3], coupon=0.05)
    prix = prix_obligations(_courbe_plate(), ns_rate, NOMS_NS, flux).iloc[0, 0]
    attendu = 5 * (np.exp(-0.03) + np.exp(-0.06) + np.exp(-0.09)) + 100 * np.exp(-0.09)
    assert abs(prix - attendu) < 1e-9
    assert abs(prix - 105.5238) < 1e-4


def test_choc_parallele_courbe_plate():
    flux = flux_obligations([3], coupon=0.05)
    prix = prix_obligations(_courbe_plate(), ns_rate, NOMS_NS, flux, choc_parallele(100)).iloc[0, 0]
    attendu = 5 * (np.exp(-0.04) + np.exp(-0.08) + np.exp(-0.12)) + 100 * np.exp(-0.12)
    assert abs(prix - attendu) < 1e-9


def test_choc_pente_nul_au_pivot():
    t = np.array([1.0, 10.0, 20.0])
    assert np.allclose(choc_pente(5, 10)(t), [-45e-4, 0.0, 50e-4])


def test_flux():
    f = flux_obligations([2, 3], coupon=0.03)
    assert f.shape == (2, 3)
    assert np.allclose(f[0], [3, 103, 0]) and np.allclose(f[1], [3, 3, 103])

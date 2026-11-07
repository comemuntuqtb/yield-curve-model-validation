from src.curves.svensson import sv_rate
from src.curves.nelson_siegel import ns_rate
import numpy as np

#test les limites du model Svensson quand T tend vers 0 ou très grand
#avec python3 -m pytest
def test_limites_svensson():
    b0, b1, b2, b3, tau1, tau2 = 0.03, -0.02, 0.01, 0.05, 2, 10
    assert np.isclose(sv_rate(1e-6, b0, b1, b2, b3, tau1, tau2), b0 + b1)
    assert np.isclose(sv_rate(1e9, b0, b1, b2, b3, tau1, tau2), b0)


def test_svensson_contient_ns():
    T = np.array([0.25, 1, 5, 10, 30.0])
    b0, b1, b2, tau1, tau2 = 0.03, -0.02, 0.01, 2, 10
    assert np.allclose(sv_rate(T, b0, b1, b2, 0.0, tau1, tau2),
                       ns_rate(T, b0, b1, b2, tau1))

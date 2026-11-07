from src.curves.nelson_siegel import ns_rate
import numpy as np

#test les limites du model NS quand T tend vers 0 ou très grand
#avec python3 -m pytest
def test_limites_ns():
    b0, b1, b2, tau = 0.03, -0.02, 0.01, 2
    assert np.isclose(ns_rate(1e-6, b0, b1, b2, tau), b0 + b1)
    assert np.isclose(ns_rate(1e6, b0, b1, b2, tau), b0)
    

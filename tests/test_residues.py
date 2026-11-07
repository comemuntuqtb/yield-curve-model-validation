import numpy as np
from src.validation.residue import rmse


def test_rmse():
    # carrés : 1, 4, 4 -> moyenne 3 -> racine sqrt(3)
    assert np.isclose(rmse([1, -2, 2]), np.sqrt(3))
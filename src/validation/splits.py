import numpy as np


def choisir_caches(positions, bornes, n_parts=3, seed=42):
    """Tire des points à cacher, répartis régulièrement sur chaque tranche.

    positions : pd.Series. L'index identifie chaque point, la valeur donne sa
        position sur un axe (ici, la maturité en années).
    bornes : liste de bornes des tranches, par exemple [0, 2, 5, 10, 20, 30].
    n_parts : chaque tranche est découpée en n_parts parts égales, et on tire
        un point dans chacune.

    Les deux extrémités de l'axe ne sont jamais tirées (points d'ancrage).
    Le tirage est reproductible grâce à seed.
    Retourne (caches, ancrage) : deux listes d'identifiants (index).
    """
    rng = np.random.default_rng(seed)
    interieur = positions[(positions > positions.min()) & (positions < positions.max())]
    caches = []

    for lo, hi in zip(bornes[:-1], bornes[1:]):
        parts = np.linspace(lo, hi, n_parts + 1)
        for lo_part, hi_part in zip(parts[:-1], parts[1:]):
            dispo = interieur[(interieur > lo_part) & (interieur <= hi_part)].index
            if len(dispo) == 0:
                raise ValueError(f"Aucun point dans ]{lo_part:.2f}, {hi_part:.2f}]")
            caches += list(rng.choice(dispo, size=1, replace=False))

    ancrage = [c for c in positions.index if c not in caches]
    return caches, ancrage
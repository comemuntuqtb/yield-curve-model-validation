import pandas as pd


def synthese_historique(hist, nom_tau, seuil_repli_pb=0.05):
    """Résume un historique d'ajustement (sortie de ajuster_historique).

    hist : DataFrame indexé par date, avec les colonnes "rmse_pb", "succes",
        "repli" et les paramètres.
    nom_tau : liste des noms des colonnes tau (["tau"] ou ["tau1", "tau2"]).
    Retourne une Series : une ligne par indicateur.
    """
    betas = [c for c in hist.columns if c.startswith("beta")]
    r = hist["rmse_pb"]
    s = {
        "dates": len(hist),
        "RMSE moyenne (pb)": r.mean(),
        "RMSE médiane (pb)": r.median(),
        "RMSE quantile 95 % (pb)": r.quantile(0.95),
        "RMSE max (pb)": r.max(),
        "date du max": r.idxmax().date(),
        f"dates RMSE > {seuil_repli_pb} pb": int((r > seuil_repli_pb).sum()),
        "dates RMSE > 5 pb": int((r > 5).sum()),
        "dates RMSE > 10 pb": int((r > 10).sum()),
        "succes = False": int((~hist["succes"]).sum()),
        "replis": int(hist["repli"].sum()),
        "dates |beta| > 20 % (non lisible)": int((hist[betas].abs() > 0.20).any(axis=1).sum()),
    }
    for t in nom_tau:
        s[f"{t} > 20 ans"] = int((hist[t] > 20).sum())
    if len(nom_tau) == 2:
        ratio = hist[nom_tau[0]] / hist[nom_tau[1]]
        s["tau1/tau2 entre 0,77 et 1,3"] = int(ratio.between(0.77, 1.3).sum())
        s["tau1 > tau2 (étiquettes inversées)"] = int((ratio > 1).sum())
    return pd.Series(s)


def rmse_par_annee(hist_ns, hist_sv):
    """RMSE moyenne (pb) par année civile, un modèle par colonne."""
    return pd.DataFrame({"NS": hist_ns["rmse_pb"].groupby(hist_ns.index.year).mean(),
                         "SV": hist_sv["rmse_pb"].groupby(hist_sv.index.year).mean()}).round(3)
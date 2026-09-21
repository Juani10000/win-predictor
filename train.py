import datetime
import math
import os
import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
    ExtraTreesClassifier,
    VotingClassifier
)

RUTA_DATASET = "dataset_historico.csv"
RUTA_MODELO = "modelo_ia_lpf.pkl"

ANIO_ACTUAL = datetime.datetime.now().year
TEMPORADAS = list(range(2022, ANIO_ACTUAL + 1))


# =====================================================================
# SISTEMA DE RATING ELO DINÁMICO
# =====================================================================
class EloSystem:
    def __init__(self, k_factor=32, home_advantage=60, default_elo=1500.0):
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.default_elo = default_elo
        self.ratings = {}

    def get_elo(self, team_id):
        return self.ratings.get(str(team_id), self.default_elo)

    def expected_score(self, elo_a, elo_b):
        return 1.0 / (1.0 + math.pow(10, (elo_b - elo_a) / 400.0))

    def update_ratings(self, loc_id, vis_id, g_loc, g_vis):
        loc_id, vis_id = str(loc_id), str(vis_id)
        elo_loc = self.get_elo(loc_id)
        elo_vis = self.get_elo(vis_id)

        exp_loc = self.expected_score(elo_loc + self.home_advantage, elo_vis)
        exp_vis = 1.0 - exp_loc

        if g_loc > g_vis:
            act_loc, act_vis = 1.0, 0.0
        elif g_loc == g_vis:
            act_loc, act_vis = 0.5, 0.5
        else:
            act_loc, act_vis = 0.0, 1.0

        diff_goles = abs(g_loc - g_vis)
        multiplier = math.log(max(diff_goles, 1) + 1) * (2.2 / ((elo_loc - elo_vis) * 0.001 + 2.2))

        self.ratings[loc_id] = elo_loc + self.k_factor * multiplier * (act_loc - exp_loc)
        self.ratings[vis_id] = elo_vis + self.k_factor * multiplier * (act_vis - exp_vis)


# =====================================================================
# DESCARGA DE HISTORIAL
# =====================================================================
def descargar_historial_multitemporada():
    url_tabla = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    try:
        r = requests.get(url_tabla, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception:
        return []

    children = data.get("children", []) or [data]
    team_ids = set()
    for grupo in children:
        for entry in grupo.get("standings", {}).get("entries", []):
            t_id = str(entry.get("team", {}).get("id"))
            if t_id:
                team_ids.add(t_id)

    partidos_map = {}
    print(f"Descargando historial para las temporadas {TEMPORADAS}...")

    for year in TEMPORADAS:
        for t_id in team_ids:
            url_sched = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{t_id}/schedule?season={year}"
            try:
                r_s = requests.get(url_sched, timeout=5)
                if r_s.status_code == 200:
                    for ev in r_s.json().get("events", []):
                        if ev.get("status", {}).get("type", {}).get("completed", False):
                            p_id = str(ev.get("id"))
                            if p_id in partidos_map:
                                continue

                            fecha_str = ev.get("date")
                            comps = ev["competitions"][0]["competitors"]
                            if comps[0].get("homeAway") == "home":
                                loc_id = str(comps[0].get("team", {}).get("id"))
                                vis_id = str(comps[1].get("team", {}).get("id"))
                                g_loc = int(comps[0].get("score", {}).get("value", 0))
                                g_vis = int(comps[1].get("score", {}).get("value", 0))
                            else:
                                loc_id = str(comps[1].get("team", {}).get("id"))
                                vis_id = str(comps[0].get("team", {}).get("id"))
                                g_loc = int(comps[1].get("score", {}).get("value", 0))
                                g_vis = int(comps[0].get("score", {}).get("value", 0))

                            res = 1 if g_loc > g_vis else (0 if g_loc == g_vis else 2)
                            partidos_map[p_id] = {
                                "id_partido": p_id,
                                "fecha": fecha_str,
                                "temporada": year,
                                "loc_id": loc_id,
                                "vis_id": vis_id,
                                "g_loc": g_loc,
                                "g_vis": g_vis,
                                "resultado": res
                            }
            except Exception:
                continue

    partidos_lista = list(partidos_map.values())
    partidos_lista.sort(key=lambda x: x["fecha"])
    return partidos_lista


def calcular_forma_ponderada(ultimos, ppm_fallback):
    if not ultimos:
        return ppm_fallback
    sub_u = ultimos[-5:]
    pesos = np.arange(1, len(sub_u) + 1)
    return float(np.average(sub_u, weights=pesos))


# =====================================================================
# CONSTRUCCIÓN DEL DATASET CON 14 FEATURES
# =====================================================================
def construir_dataset_cronologico(partidos):
    filas = []
    stats_equipos = {}
    elo_sys = EloSystem()
    temporada_actual = None

    for p in partidos:
        temp = p["temporada"]

        if temp != temporada_actual:
            if temporada_actual is not None:
                for tid, st in stats_equipos.items():
                    pj = max(st["pj_tot"], 1)
                    pj_l = max(st["pj_loc"], 1)
                    pj_v = max(st["pj_vis"], 1)

                    ppm = st["pts_tot"] / pj
                    gf_p = st["gf_tot"] / pj
                    gc_p = st["gc_tot"] / pj
                    ppm_l = st["pts_loc"] / pj_l
                    ppm_v = st["pts_vis"] / pj_v

                    stats_equipos[tid] = {
                        "pj_tot": 3, "pts_tot": ppm * 3,
                        "gf_tot": gf_p * 3, "gc_tot": gc_p * 3,
                        "pj_loc": 2, "pts_loc": ppm_l * 2,
                        "pj_vis": 2, "pts_vis": ppm_v * 2,
                        "ultimos": st["ultimos"][-3:] if st["ultimos"] else []
                    }
            temporada_actual = temp

        loc_id = p["loc_id"]
        vis_id = p["vis_id"]

        for tid in [loc_id, vis_id]:
            if tid not in stats_equipos:
                stats_equipos[tid] = {
                    "pj_tot": 0, "pts_tot": 0, "gf_tot": 0, "gc_tot": 0,
                    "pj_loc": 0, "pts_loc": 0, "pj_vis": 0, "pts_vis": 0,
                    "ultimos": []
                }

        st_loc = stats_equipos[loc_id]
        st_vis = stats_equipos[vis_id]

        pj_l, pj_v = st_loc["pj_tot"], st_vis["pj_tot"]

        ppm_loc = (st_loc["pts_tot"] + 1.0) / (pj_l + 1.0) if pj_l < 3 else st_loc["pts_tot"] / pj_l
        ppm_vis = (st_vis["pts_tot"] + 1.0) / (pj_v + 1.0) if pj_v < 3 else st_vis["pts_tot"] / pj_v

        dg_loc = (st_loc["gf_tot"] - st_loc["gc_tot"]) / (pj_l + 1.0) if pj_l < 3 else (st_loc["gf_tot"] - st_loc["gc_tot"]) / pj_l
        dg_vis = (st_vis["gf_tot"] - st_vis["gc_tot"]) / (pj_v + 1.0) if pj_v < 3 else (st_vis["gf_tot"] - st_vis["gc_tot"]) / pj_v

        forma_loc = calcular_forma_ponderada(st_loc["ultimos"], ppm_loc)
        forma_vis = calcular_forma_ponderada(st_vis["ultimos"], ppm_vis)

        pj_loc_cancha = st_loc["pj_loc"]
        pj_vis_cancha = st_vis["pj_vis"]

        ppm_loc_cancha = (st_loc["pts_loc"] + 1.0) / (pj_loc_cancha + 1.0) if pj_loc_cancha < 2 else st_loc["pts_loc"] / pj_loc_cancha
        ppm_vis_cancha = (st_vis["pts_vis"] + 1.0) / (pj_vis_cancha + 1.0) if pj_vis_cancha < 2 else st_vis["pts_vis"] / pj_vis_cancha

        # Cálculo de Rating Elo antes del partido
        elo_loc = elo_sys.get_elo(loc_id)
        elo_vis = elo_sys.get_elo(vis_id)
        dif_elo = (elo_loc + elo_sys.home_advantage) - elo_vis

        filas.append({
            "id_partido": p["id_partido"],
            "ppm_loc": ppm_loc,
            "ppm_vis": ppm_vis,
            "ppm_loc_cancha": ppm_loc_cancha,
            "ppm_vis_cancha": ppm_vis_cancha,
            "dg_loc": dg_loc,
            "dg_vis": dg_vis,
            "forma_loc": forma_loc,
            "forma_vis": forma_vis,
            "dif_ppm": ppm_loc - ppm_vis,
            "dif_dg": dg_loc - dg_vis,
            "dif_forma": forma_loc - forma_vis,
            "elo_loc": elo_loc,
            "elo_vis": elo_vis,
            "dif_elo": dif_elo,
            "resultado": p["resultado"]
        })

        res = p["resultado"]
        pts_l = 3 if res == 1 else (1 if res == 0 else 0)
        pts_v = 3 if res == 2 else (1 if res == 0 else 0)

        # Actualización acumulativa
        st_loc["pj_tot"] += 1; st_loc["pts_tot"] += pts_l; st_loc["gf_tot"] += p["g_loc"]; st_loc["gc_tot"] += p["g_vis"]
        st_loc["pj_loc"] += 1; st_loc["pts_loc"] += pts_l; st_loc["ultimos"].append(pts_l)

        st_vis["pj_tot"] += 1; st_vis["pts_tot"] += pts_v; st_vis["gf_tot"] += p["g_vis"]; st_vis["gc_tot"] += p["g_loc"]
        st_vis["pj_vis"] += 1; st_vis["pts_vis"] += pts_v; st_vis["ultimos"].append(pts_v)

        # Actualizar Elo dinámico con el resultado
        elo_sys.update_ratings(loc_id, vis_id, p["g_loc"], p["g_vis"])

    return pd.DataFrame(filas), elo_sys


def ejecutar_auto_aprendizaje():
    partidos = descargar_historial_multitemporada()
    if not partidos:
        print("No se encontraron partidos.")
        return

    df, elo_sys = construir_dataset_cronologico(partidos)
    df.to_csv(RUTA_DATASET, index=False)

    columnas_features = [
        "ppm_loc", "ppm_vis",
        "ppm_loc_cancha", "ppm_vis_cancha",
        "dg_loc", "dg_vis",
        "forma_loc", "forma_vis",
        "dif_ppm", "dif_dg", "dif_forma",
        "elo_loc", "elo_vis", "dif_elo"
    ]

    X = df[columnas_features]
    y = df["resultado"]

    m1_gb = HistGradientBoostingClassifier(
        max_iter=150, learning_rate=0.03, max_depth=4, l2_regularization=1.5,
        class_weight='balanced', random_state=42
    )

    m2_rf = RandomForestClassifier(
        n_estimators=150, max_depth=5, class_weight='balanced', random_state=42
    )

    m3_et = ExtraTreesClassifier(
        n_estimators=150, max_depth=5, class_weight='balanced', random_state=42
    )

    modelo_ensamble = VotingClassifier(
        estimators=[('hist_gb', m1_gb), ('rf', m2_rf), ('et', m3_et)],
        voting='soft'
    )

    modelo_ensamble.fit(X, y)

    # Guarda tanto el modelo entrenado como los Elos calculados en un paquete dict
    paquete_modelo = {
        "modelo": modelo_ensamble,
        "elos": elo_sys.ratings
    }

    joblib.dump(paquete_modelo, RUTA_MODELO)
    print(f"Ensamble (14 vars + Elo) reentrenado con éxito ({len(df)} partidos). Guardado en '{RUTA_MODELO}'.")

if __name__ == "__main__":
    ejecutar_auto_aprendizaje()

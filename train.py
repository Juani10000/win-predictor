import datetime
import os
import joblib
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

RUTA_DATASET = "dataset_historico.csv"
RUTA_MODELO = "modelo_ia_lpf.pkl"

def obtener_datos_espn():
    """Obtiene la tabla actual y el historial de partidos finalizados desde ESPN."""
    url_tabla = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    r = requests.get(url_tabla, timeout=10)
    if r.status_code != 200:
        return None, []
    
    data = r.json()
    children = data.get("children", []) or [data]
    
    equipos = {}
    for grupo in children:
        for entry in grupo.get("standings", {}).get("entries", []):
            team = entry.get("team", {})
            t_id = str(team.get("id"))
            nombre = team.get("displayName")
            stats = {s.get("name"): s.get("value", 0) for s in entry.get("stats", [])}
            
            equipos[t_id] = {
                "nombre": nombre,
                "pts": int(stats.get("points", 0)),
                "pj": int(stats.get("gamesPlayed", 0)),
                "dg": int(stats.get("pointsFor", 0)) - int(stats.get("pointsAgainst", 0))
            }

    # Obtener resultados finalizados
    partidos_finalizados = []
    for t_id in equipos.keys():
        url_sched = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{t_id}/schedule"
        r_s = requests.get(url_sched, timeout=5)
        if r_s.status_code == 200:
            for ev in r_s.json().get("events", []):
                if ev.get("status", {}).get("type", {}).get("completed", False):
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

                    if loc_id in equipos and vis_id in equipos:
                        # Resultado: 1 = Gana Local, 0 = Empate, 2 = Gana Visitante
                        res = 1 if g_loc > g_vis else (0 if g_loc == g_vis else 2)
                        partidos_finalizados.append({
                            "id_partido": ev.get("id"),
                            "loc_id": loc_id,
                            "vis_id": vis_id,
                            "resultado": res
                        })
    return equipos, partidos_finalizados

def extraer_features_seguras(loc_info, vis_info):
    """
    Calcula variables aplicando suavizado si el torneo recién empieza (PJ < 3).
    Evita divisiones por cero o estadísticas distorsionadas en las primeras fechas.
    """
    pj_loc = int(loc_info.get("pj", 0))
    pts_loc = float(loc_info.get("pts", 0))
    dg_loc = float(loc_info.get("dg", 0))

    pj_vis = int(vis_info.get("pj", 0))
    pts_vis = float(vis_info.get("pts", 0))
    dg_vis = float(vis_info.get("dg", 0))

    if pj_loc < 3:
        ppm_loc = (pts_loc + 1.0) / (pj_loc + 1.0)
        dg_prom_loc = dg_loc / (pj_loc + 1.0)
    else:
        ppm_loc = pts_loc / pj_loc
        dg_prom_loc = dg_loc / pj_loc

    if pj_vis < 3:
        ppm_vis = (pts_vis + 1.0) / (pj_vis + 1.0)
        dg_prom_vis = dg_vis / (pj_vis + 1.0)
    else:
        ppm_vis = pts_vis / pj_vis
        dg_prom_vis = dg_vis / pj_vis

    return {
        "ppm_loc": ppm_loc,
        "ppm_vis": ppm_vis,
        "dg_loc": dg_prom_loc,
        "dg_vis": dg_prom_vis,
        "dif_ppm": ppm_loc - ppm_vis
    }

def ejecutar_auto_aprendizaje():
    equipos, partidos = obtener_datos_espn()
    if not equipos or not partidos:
        print("No se pudieron obtener datos de ESPN.")
        return

    filas = []
    for p in partidos:
        f = extraer_features_seguras(equipos[p["loc_id"]], equipos[p["vis_id"]])
        f["id_partido"] = p["id_partido"]
        f["resultado"] = p["resultado"]
        filas.append(f)

    df_nuevo = pd.DataFrame(filas).drop_duplicates(subset=["id_partido"])

    # Actualizar Dataset en disco
    if os.path.exists(RUTA_DATASET):
        df_existente = pd.read_csv(RUTA_DATASET)
        df_total = pd.concat([df_existente, df_nuevo]).drop_duplicates(subset=["id_partido"])
    else:
        df_total = df_nuevo

    df_total.to_csv(RUTA_DATASET, index=False)
    print(f"Dataset actualizado con {len(df_total)} partidos reales.")

    # Reentrenar Modelo de Machine Learning
    X = df_total.drop(columns=["id_partido", "resultado"])
    y = df_total["resultado"]

    modelo = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    modelo.fit(X, y)
    
    # Guardar modelo entrenado
    joblib.dump(modelo, RUTA_MODELO)
    print("Modelo 'modelo_ia_lpf.pkl' reentrenado y guardado con éxito.")

if __name__ == "__main__":
    ejecutar_auto_aprendizaje()

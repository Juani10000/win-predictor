import datetime
import os
import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

RUTA_DATASET = "dataset_historico.csv"
RUTA_MODELO = "modelo_ia_lpf.pkl"

# Encabezados de navegador completo para evitar bloqueos HTTP 403 en GitHub Actions
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# IDs de respaldo de la LPF en caso de bloqueo HTTP en el endpoint de la tabla de posiciones
EQUIPOS_LPF_FALLBACK = {
    "1", "2", "3", "6", "8", "9", "10", "11", "12", "13", "14", "16", "17", "18", 
    "24", "26", "2524", "3271", "3272", "3593", "5121", "8291", "10849", "10850", 
    "10851", "19182", "19183", "20630"
}

ANIO_ACTUAL = datetime.datetime.now().year
VENTANA_ANIOS = 5
TEMPORADAS = list(range(ANIO_ACTUAL - VENTANA_ANIOS + 1, ANIO_ACTUAL + 1))


def obtener_ids_equipos(session):
    team_ids = set()
    
    # Intento 1: Obtener desde Standings
    url_tabla = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    try:
        r = session.get(url_tabla, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            children = data.get("children", []) or [data]
            for grupo in children:
                for entry in grupo.get("standings", {}).get("entries", []):
                    t_id = str(entry.get("team", {}).get("id"))
                    if t_id:
                        team_ids.add(t_id)
        else:
            print(f"Aviso: Standings respondió HTTP {r.status_code}. Intentando método alternativo...")
    except Exception as e:
        print(f"Excepción al conectar con Standings: {e}")

    # Intento 2: Si Standings falló o vino vacío, intentar con el endpoint /teams
    if not team_ids:
        url_teams = "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams"
        try:
            r = session.get(url_teams, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                sports = data.get("sports", [])
                if sports:
                    leagues = sports[0].get("leagues", [])
                    if leagues:
                        for tm in leagues[0].get("teams", []):
                            t_id = str(tm.get("team", {}).get("id"))
                            if t_id:
                                team_ids.add(t_id)
        except Exception as e:
            print(f"Excepción al conectar con Teams: {e}")

    # Intento 3: Si ambos fallan (403), usar el conjunto de IDs por defecto
    if not team_ids:
        print("Usando lista de respaldos de IDs de la Liga Profesional...")
        team_ids = EQUIPOS_LPF_FALLBACK

    return team_ids


def descargar_historial_multitemporada():
    session = requests.Session()
    team_ids = obtener_ids_equipos(session)
    partidos_map = {}
    
    print(f"Descargando historial para {len(team_ids)} equipos en las temporadas {TEMPORADAS}...")

    for year in TEMPORADAS:
        for t_id in team_ids:
            url_sched = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{t_id}/schedule?season={year}"
            try:
                r_s = session.get(url_sched, headers=HEADERS, timeout=7)
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


def construir_dataset_cronologico(partidos):
    filas = []
    stats_equipos = {}
    temporada_actual = None

    for p in partidos:
        temp = p["temporada"]
        if temp != temporada_actual:
            temporada_actual = temp
            stats_equipos = {}

        loc_id = p["loc_id"]
        vis_id = p["vis_id"]

        for tid in [loc_id, vis_id]:
            if tid not in stats_equipos:
                stats_equipos[tid] = {"pj": 0, "pts": 0, "gf": 0, "gc": 0, "ultimos": []}

        st_loc = stats_equipos[loc_id]
        st_vis = stats_equipos[vis_id]

        pj_l = st_loc["pj"]
        pj_v = st_vis["pj"]

        ppm_loc = (st_loc["pts"] + 1.0) / (pj_l + 1.0) if pj_l < 3 else st_loc["pts"] / pj_l
        ppm_vis = (st_vis["pts"] + 1.0) / (pj_v + 1.0) if pj_v < 3 else st_vis["pts"] / pj_v

        dg_loc = (st_loc["gf"] - st_loc["gc"]) / (pj_l + 1.0) if pj_l < 3 else (st_loc["gf"] - st_loc["gc"]) / pj_l
        dg_vis = (st_vis["gf"] - st_vis["gc"]) / (pj_v + 1.0) if pj_v < 3 else (st_vis["gf"] - st_vis["gc"]) / pj_v

        forma_loc = np.mean(st_loc["ultimos"][-5:]) if st_loc["ultimos"] else ppm_loc
        forma_vis = np.mean(st_vis["ultimos"][-5:]) if st_vis["ultimos"] else ppm_vis

        filas.append({
            "id_partido": p["id_partido"],
            "ppm_loc": ppm_loc,
            "ppm_vis": ppm_vis,
            "dg_loc": dg_loc,
            "dg_vis": dg_vis,
            "forma_loc": forma_loc,
            "forma_vis": forma_vis,
            "dif_ppm": ppm_loc - ppm_vis,
            "resultado": p["resultado"]
        })

        res = p["resultado"]
        pts_l = 3 if res == 1 else (1 if res == 0 else 0)
        pts_v = 3 if res == 2 else (1 if res == 0 else 0)

        st_loc["pj"] += 1
        st_loc["pts"] += pts_l
        st_loc["gf"] += p["g_loc"]
        st_loc["gc"] += p["g_vis"]
        st_loc["ultimos"].append(pts_l)

        st_vis["pj"] += 1
        st_vis["pts"] += pts_v
        st_vis["gf"] += p["g_vis"]
        st_vis["gc"] += p["g_loc"]
        st_vis["ultimos"].append(pts_v)

    return pd.DataFrame(filas)


def ejecutar_auto_aprendizaje():
    partidos = descargar_historial_multitemporada()
    if not partidos:
        raise RuntimeError("No se pudieron descargar partidos. Verifica la conectividad de red.")

    df = construir_dataset_cronologico(partidos)
    df.to_csv(RUTA_DATASET, index=False)

    X = df[["ppm_loc", "ppm_vis", "dg_loc", "dg_vis", "forma_loc", "forma_vis", "dif_ppm"]]
    y = df["resultado"]

    modelo = Pipeline([
        ('scaler', StandardScaler()),
        ('lr', LogisticRegression(C=0.5, max_iter=1000, class_weight='balanced'))
    ])
    modelo.fit(X, y)

    joblib.dump(modelo, RUTA_MODELO)
    print(f"Modelo reentrenado exitosamente con {len(df)} partidos. Guardado en '{RUTA_MODELO}'.")

if __name__ == "__main__":
    ejecutar_auto_aprendizaje()

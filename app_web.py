import pandas as pd
import requests
import streamlit as st

# URL de ejemplo para Liga Profesional (ajustá a tu torneo si es otro)
URL_API_ESPN = (
    "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
)
RUTA_CSV = "datos_procesados.csv"


def obtener_tabla_actualizada():
    # 1. Cargamos el CSV base como respaldo por si se corta internet
    try:
        df = pd.read_csv(RUTA_CSV)
    except Exception:
        df = pd.DataFrame()

    # 2. Consultamos a ESPN en vivo
    try:
        respuesta = requests.get(URL_API_ESPN, timeout=5)
        if respuesta.status_code == 200:
            datos_json = respuesta.json()
            entradas = datos_json["children"][0]["standings"]["entries"]

            stats_frescas = {}
            for entry in entradas:
                equipo = entry["team"]["displayName"]
                stats = {
                    s["name"]: s["value"]
                    for s in entry["stats"]
                    if "name" in s and "value" in s
                }
                stats_frescas[equipo] = {
                    "Puntos": stats.get("points", 0),
                    "PJ": stats.get("gamesPlayed", 0),
                    "GF": stats.get("pointsFor", 0),
                    "GC": stats.get("pointsAgainst", 0),
                    "DG": stats.get("pointDifferential", 0),
                }

            # 3. Actualizamos los datos del DataFrame en vivo
            for equipo, datos in stats_frescas.items():
                mask = df["Equipo"] == equipo
                if mask.any():
                    df.loc[mask, "Puntos"] = datos["Puntos"]
                    df.loc[mask, "PJ"] = datos["PJ"]
                    df.loc[mask, "GF"] = datos["GF"]
                    df.loc[mask, "GC"] = datos["GC"]
                    df.loc[mask, "DG"] = datos["DG"]

            # Recalculamos xG si usás esa columna
            if "GF" in df.columns and "PJ" in df.columns:
                df["xG"] = (df["GF"] / df["PJ"].replace(0, 1) * 0.95).round(2)

            # Ordenamos la tabla de posiciones correctamente
            df = df.sort_values(
                by=["Puntos", "DG", "GF"], ascending=[False, False, False]
            ).reset_index(drop=True)

    except Exception:
        # Si la API de ESPN falla, simplemente sigue mostrando el CSV base sin romper la app
        pass

    return df


# --- CÓDIGO DE VISUALIZACIÓN EN STREAMLIT ---
st.title("⚽ Tabla de Posiciones en Vivo")

# Botón para que vos o el usuario fuercen la recarga al instante
if st.button("🔄 Actualizar ahora"):
    st.cache_data.clear()

tabla_final = obtener_tabla_actualizada()
st.dataframe(tabla_final, use_container_width=True)

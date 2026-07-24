import numpy as np
import pandas as pd

print(
    "🔄 Procesando racha y forma reciente de los equipos (Últimos 5 partidos)..."
)

# 1. Cargar partidos descargados de la API
df = pd.read_csv("datos/liga_argentina.csv")

# Asegurar orden cronológico por fecha
df["Fecha"] = pd.to_datetime(df["Fecha"])
df = df.sort_values("Fecha").reset_index(drop=True)

# Mapeo de resultado para el modelo (1: Local, 0: Empate, 2: Visitante)
mapeo_resultados = {"L": 1, "E": 0, "V": 2}
df["resultado_num"] = df["Resultado"].map(mapeo_resultados)


# Función para calcular la racha/forma de un equipo ANTES de un partido específico
def obtener_estadisticas_previas(df_partidos, fecha, equipo, ultimos_n=5):
    # Buscar partidos anteriores de este equipo
    partidos_previos = df_partidos[
        (df_partidos["Fecha"] < fecha)
        & (
            (df_partidos["Local"] == equipo)
            | (df_partidos["Visitante"] == equipo)
        )
    ].tail(ultimos_n)

    if len(partidos_previos) == 0:
        return 1.0, 1.0, 1.0  # Valores por defecto si es el primer partido

    goles_favor = []
    goles_contra = []
    puntos = []

    for _, fila in partidos_previos.iterrows():
        es_local = fila["Local"] == equipo
        gf = fila["Goles_Local"] if es_local else fila["Goles_Visitante"]
        gc = fila["Goles_Visitante"] if es_local else fila["Goles_Local"]
        res = fila["Resultado"]

        if (es_local and res == "L") or (not es_local and res == "V"):
            pts = 3
        elif res == "E":
            pts = 1
        else:
            pts = 0

        goles_favor.append(gf)
        goles_contra.append(gc)
        puntos.append(pts)

    return np.mean(goles_favor), np.mean(goles_contra), np.mean(puntos)


# Crear listas para almacenar las nuevas métricas
gf_local, gc_local, pts_local = [], [], []
gf_visita, gc_visita, pts_visita = [], [], []

print("⏳ Calculando métricas de racha fecha por fecha...")

for idx, fila in df.iterrows():
    fecha = fila["Fecha"]
    local = fila["Local"]
    visita = fila["Visitante"]

    # Racha local
    g_fav_l, g_con_l, p_l = obtener_estadisticas_previas(df, fecha, local)
    gf_local.append(g_fav_l)
    gc_local.append(g_con_l)
    pts_local.append(p_l)

    # Racha visitante
    g_fav_v, g_con_v, p_v = obtener_estadisticas_previas(df, fecha, visita)
    gf_visita.append(g_fav_v)
    gc_visita.append(g_con_v)
    pts_visita.append(p_v)

df["local_gf_5"] = gf_local
df["local_gc_5"] = gc_local
df["local_pts_5"] = pts_local

df["visita_gf_5"] = gf_visita
df["visita_gc_5"] = gc_visita
df["visita_pts_5"] = pts_visita

# Codificar nombres de equipos
equipos = pd.concat([df["Local"], df["Visitante"]]).unique()
mapa_equipos = {equipo: i for i, equipo in enumerate(equipos)}
df["local_cod"] = df["Local"].map(mapa_equipos)
df["visitante_cod"] = df["Visitante"].map(mapa_equipos)

# Guardar en archivo procesado
df.to_csv("datos/datos_procesados.csv", index=False)

print(
    "✅ ¡Métricas de racha calculadas con éxito y guardadas en 'datos_procesados.csv'!"
)
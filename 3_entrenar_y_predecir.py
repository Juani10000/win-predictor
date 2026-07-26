import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

print("Entrenando modelo avanzado con Jerarquía, Ajuste por Rival y Decaimiento Temporal...")

# =====================================================================
# 1. DICCIONARIO Y FUNCIÓN DE JERARQUÍA DE PLANTELES
# =====================================================================
JERARQUIA_EQUIPOS = {
    "River Plate": 9.5, "Boca Juniors": 9.2, "Racing Club": 8.5,
    "San Lorenzo": 8.0, "Independiente": 8.0, "Estudiantes": 7.8,
    "Talleres": 7.8, "Vélez Sarsfield": 7.5, "Lanús": 7.5,
    "Huracán": 7.2, "Rosario Central": 7.2, "Argentinos Juniors": 7.0,
    "Godoy Cruz": 7.0, "Belgrano": 6.8, "Newell's": 6.8,
    "Defensa y Justicia": 6.8, "Unión": 6.5, "Platense": 6.5,
    "Gimnasia LP": 6.5, "Instituto": 6.3, "Banfield": 6.3,
    "Tigre": 6.2, "Barracas Central": 6.0, "Central Córdoba": 6.0,
    "Sarmiento": 5.8, "Deportivo Riestra": 5.8, "Independiente Rivadavia": 5.8,
    "Atlético Tucumán": 6.2, "Aldosivi": 5.5, "San Martín (SJ)": 5.5
}

def obtener_jerarquia(nombre_equipo):
    if not isinstance(nombre_equipo, str):
        return 6.5
    nombre_norm = nombre_equipo.lower().strip()
    for eq, rating in JERARQUIA_EQUIPOS.items():
        if eq.lower() in nombre_norm or nombre_norm in eq.lower():
            return rating
    return 6.5


# =====================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS
# =====================================================================
df = pd.read_csv("datos/datos_procesados.csv")

# Asignar Jerarquía de Plantel
df["local_jerarquia"] = df["Local"].apply(obtener_jerarquia)
df["visitante_jerarquia"] = df["Visitante"].apply(obtener_jerarquia)

# Ajuste de Racha por Rival
df["local_pts_ajustados_5"] = df["local_pts_5"] * (df["visitante_jerarquia"] / 10.0)
df["visita_pts_ajustados_5"] = df["visita_pts_5"] * (df["local_jerarquia"] / 10.0)

# =====================================================================
# ---> NUEVO: DECAIMIENTO TEMPORAL (TIME DECAY) <---
# Creamos un array exponencial que va de -3 a 0. 
# Al aplicarle np.exp(), nos da pesos que van desde ~0.05 hasta 1.0
# Asumimos que el CSV está ordenado cronológicamente (los últimos son los más nuevos)
# =====================================================================
pesos_temporales = np.exp(np.linspace(-3, 0, len(df)))
df["peso_temporal"] = pesos_temporales

# 3. Definir las variables explicativas (Features) y el objetivo (Target)
features = [
    "local_cod",
    "visitante_cod",
    "local_jerarquia",
    "visitante_jerarquia",
    "local_gf_5",
    "local_gc_5",
    "local_pts_ajustados_5",
    "visita_gf_5",
    "visita_gc_5",
    "visita_pts_ajustados_5",
]

X = df[features]
y = df["resultado_num"]
pesos = df["peso_temporal"]

# =====================================================================
# 4. ENTRENAR EL MODELO
# Le pasamos el argumento sample_weight para que aplique el decaimiento
# =====================================================================
modelo = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
modelo.fit(X, y, sample_weight=pesos)

print("Modelo entrenado y calibrado correctamente con Time Decay.")

# Lista de equipos
equipos_unicos = sorted(pd.concat([df["Local"], df["Visitante"]]).unique())
mapa_equipos = {equipo: i for i, equipo in enumerate(equipos_unicos)}

# Función para calcular la racha más reciente de un equipo
def obtener_racha_actual(equipo):
    partidos = df[(df["Local"] == equipo) | (df["Visitante"] == equipo)].tail(5)
    if len(partidos) == 0:
        return 1.0, 1.0, 1.0

    gf, gc, pts = 0, 0, 0
    for _, row in partidos.iterrows():
        if row["Local"] == equipo:
            gf += row["Goles_Local"]
            gc += row["Goles_Visitante"]
            if row["Resultado"] == "L":
                pts += 3
            elif row["Resultado"] == "E":
                pts += 1
        else:
            gf += row["Goles_Visitante"]
            gc += row["Goles_Local"]
            if row["Resultado"] == "V":
                pts += 3
            elif row["Resultado"] == "E":
                pts += 1

    n = len(partidos)
    return gf / n, gc / n, pts / n

def predecir_partido(local, visitante):
    if local not in mapa_equipos or visitante not in mapa_equipos:
        print("Uno o ambos equipos no existen en la base de datos.")
        return

    l_gf, l_gc, l_pts = obtener_racha_actual(local)
    v_gf, v_gc, v_pts = obtener_racha_actual(visitante)

    jer_local = obtener_jerarquia(local)
    jer_visita = obtener_jerarquia(visitante)

    # Puntos ajustados por la jerarquía del rival
    l_pts_ajustado = l_pts * (jer_visita / 10.0)
    v_pts_ajustado = v_pts * (jer_local / 10.0)

    partido_nuevo = pd.DataFrame(
        [
            {
                "local_cod": mapa_equipos[local],
                "visitante_cod": mapa_equipos[visitante],
                "local_jerarquia": jer_local,
                "visitante_jerarquia": jer_visita,
                "local_gf_5": l_gf,
                "local_gc_5": l_gc,
                "local_pts_ajustados_5": l_pts_ajustado,
                "visita_gf_5": v_gf,
                "visita_gc_5": v_gc,
                "visita_pts_ajustados_5": v_pts_ajustado,
            }
        ]
    )

    # Predecir
    prediccion = modelo.predict(partido_nuevo)[0]
    probs = modelo.predict_proba(partido_nuevo)[0]

    res_txt = {
        1: f"Gana {local} (Local)",
        0: "Empate",
        2: f"Gana {visitante} (Visitante)",
    }

    print(f"\nPronóstico Avanzado: {local} vs {visitante}")
    print(f"Jerarquía Plantel -> {local}: {jer_local} | {visitante}: {jer_visita}")
    print(f"Racha Local ({local}): {l_pts:.1f} pts/partido (Ajustado por Rival: {l_pts_ajustado:.2f})")
    print(f"Racha Visitante ({visitante}): {v_pts:.1f} pts/partido (Ajustado por Rival: {v_pts_ajustado:.2f})")
    print(f"Resultado esperado: {res_txt[prediccion]}")
    print("Probabilidades realistas del Modelo (con Time Decay):")

    clases = modelo.classes_
    mapa_clases = {0: "Empate", 1: f"Gana {local}", 2: f"Gana {visitante}"}
    for idx, c in enumerate(clases):
        print(f"   - {mapa_clases.get(c, c)}: {probs[idx]*100:.1f}%")

if __name__ == "__main__":
    predecir_partido("Boca Juniors", "Independiente Rivadavia")

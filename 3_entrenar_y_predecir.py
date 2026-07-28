import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

print("🧠 Entrenando modelo avanzado con rachas y prevención de sobreajuste...")

# 1. Cargar los datos procesados con rachas
df = pd.read_csv("datos/datos_procesados.csv")

# 2. Definir las variables explicativas (Features) y el objetivo (Target)
features = [
    "local_cod",
    "visitante_cod",
    "local_gf_5",
    "local_gc_5",
    "local_pts_5",
    "visita_gf_5",
    "visita_gc_5",
    "visita_pts_5",
]
X = df[features]
y = df["resultado_num"]

# 3. Entrenar el modelo limitando la profundidad para EVITAR el 100% de sobreajuste
modelo = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
modelo.fit(X, y)

print("✅ Modelo entrenado y calibrado correctamente.")

# Lista de equipos
equipos_unicos = sorted(pd.concat([df["Local"], df["Visitante"]]).unique())
mapa_equipos = {equipo: i for i, equipo in enumerate(equipos_unicos)}


# Función para calcular la racha más reciente de un equipo
def obtener_racha_actual(equipo):
    partidos = df[(df["Local"] == equipo) | (df["Visitante"] == equipo)].tail(5)
    if len(partidos) == 0:
        return 1.0, 1.0, 1.0

    gf, gc, pts = [], [], []
    for _, fila in partidos.iterrows():
        es_local = fila["Local"] == equipo
        g_fav = fila["Goles_Local"] if es_local else fila["Goles_Visitante"]
        g_con = fila["Goles_Visitante"] if es_local else fila["Goles_Local"]
        res = fila["Resultado"]

        if (es_local and res == "L") or (not es_local and res == "V"):
            p = 3
        elif res == "E":
            p = 1
        else:
            p = 0

        gf.append(g_fav)
        gc.append(g_con)
        pts.append(p)

    return np.mean(gf), np.mean(gc), np.mean(pts)


def predecir(local, visitante):
    if local not in mapa_equipos or visitante not in mapa_equipos:
        print(
            f"❌ Error: Uno de los equipos ('{local}' o '{visitante}') no existe en la lista."
        )
        return

    # Obtener racha actual de ambos
    l_gf, l_gc, l_pts = obtener_racha_actual(local)
    v_gf, v_gc, v_pts = obtener_racha_actual(visitante)

    # Crear la fila para predecir
    partido_nuevo = pd.DataFrame(
        [
            {
                "local_cod": mapa_equipos[local],
                "visitante_cod": mapa_equipos[visitante],
                "local_gf_5": l_gf,
                "local_gc_5": l_gc,
                "local_pts_5": l_pts,
                "visita_gf_5": v_gf,
                "visita_gc_5": v_gc,
                "visita_pts_5": v_pts,
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

    print(f"\n📊 Pronóstico Avanzado: {local} vs {visitante}")
    print(
        f"🔥 Racha Local ({local}): {l_pts:.1f} pts/partido | {l_gf:.1f} goles favor/partido"
    )
    print(
        f"🔥 Racha Visitante ({visitante}): {v_pts:.1f} pts/partido | {v_gf:.1f} goles favor/partido"
    )
    print(f"🔮 Resultado esperado: {res_txt[prediccion]}")
    print("📈 Probabilidades realistas del modelo:")

    clases = list(modelo.classes_)
    if 1 in clases:
        print(f"   - Victoria Local ({local}): {probs[clases.index(1)]*100:.1f}%")
    if 0 in clases:
        print(f"   - Empate: {probs[clases.index(0)]*100:.1f}%")
    if 2 in clases:
        print(
            f"   - Victoria Visitante ({visitante}): {probs[clases.index(2)]*100:.1f}%"
        )


# --- PRUEBAS DE PARTIDOS ---
predecir("Racing Club", "Independiente")
predecir("Boca Juniors", "River Plate")

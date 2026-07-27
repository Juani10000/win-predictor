import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score
import joblib

print("🧠 Entrenando modelo avanzado con rachas, prevención de sobreajuste y Auto-Tuning...")

# 1. Cargar los datos procesados con rachas
path_datos = "datos/datos_procesados.csv"

if not os.path.exists(path_datos):
    print(f"❌ Error: No se encontró el archivo {path_datos}")
    exit(1)

df = pd.read_csv(path_datos)

# ------------------------------------------------------------------
# 🛡️ MALLA DE SEGURIDAD (Evita KeyError si el CSV viene incompleto)
# ------------------------------------------------------------------
columnas_requeridas = {
    "local_cod": 0,
    "visitante_cod": 0,
    "local_gf_5": 0.0,
    "local_gc_5": 0.0,
    "local_pts_5": 0.0,
    "visita_gf_5": 0.0,
    "visita_gc_5": 0.0,
    "visita_pts_5": 0.0,
    "resultado_num": 0,
    "Local": "Desconocido",
    "Visitante": "Desconocido",
    "Goles_Local": 0,
    "Goles_Visitante": 0,
    "Resultado": "E"
}

for col, val_defecto in columnas_requeridas.items():
    if col not in df.columns:
        df[col] = val_defecto
# ------------------------------------------------------------------

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

# 3. Separar datos para evaluación
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Evaluamos modelo previo si existe
archivo_modelo = "modelo_entrenado.pkl"
precision_vieja = 0.0

if os.path.exists(archivo_modelo):
    try:
        modelo_viejo = joblib.load(archivo_modelo)
        pred_viejas = modelo_viejo.predict(X_test)
        precision_vieja = accuracy_score(y_test, pred_viejas)
        print(f"👴 Modelo guardado anterior: Precisión del {precision_vieja*100:.1f}%")
    except Exception:
        precision_vieja = 0.0

# Auto-Tuning: Prueba combinaciones para encontrar la mejor
parametros = {
    'n_estimators': [50, 100],
    'max_depth': [3, 5, 7]
}

buscador = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_grid=parametros,
    cv=3,
    scoring='accuracy',
    n_jobs=-1
)
buscador.fit(X_train, y_train)

modelo = buscador.best_estimator_
pred_nuevas = modelo.predict(X_test)
precision_nueva = accuracy_score(y_test, pred_nuevas)

print(f"🚀 Modelo nuevo entrenado: Precisión del {precision_nueva*100:.1f}%")

# Guardar solo si es mejor o si es el primero
if precision_nueva >= precision_vieja:
    joblib.dump(modelo, archivo_modelo)
    print(f"💾 Modelo guardado exitosamente en '{archivo_modelo}'.")
else:
    print("🛡️ Se mantiene el modelo anterior por tener mejor precisión.")
    modelo = joblib.load(archivo_modelo)

# =====================================================================
# 📋 TUS FUNCIONES DE RACHAS Y PREDECIR (RESTAURADAS)
# =====================================================================

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
    print(f"🔮 Resultado esperado: {res_txt.get(prediccion, 'Desconocido')}")
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

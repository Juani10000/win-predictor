import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV, train_test_split

print("🧠 Entrenando modelo avanzado con auto-mejora (Auto-Tuning) y rachas...")

# 1. Cargar los datos procesados con rachas
path_datos = "datos/datos_procesados.csv"

if not os.path.exists(path_datos):
    print(f"❌ Error: No se encontró el archivo {path_datos}")
    exit(1)

df = pd.read_csv(path_datos)

# ------------------------------------------------------------------
# 🛡️ ESCUDO PROTECTOR (Evita KeyError si faltan columnas en el CSV)
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
    "Local": "Sin Nombre",
    "Visitante": "Sin Nombre",
    "Goles_Local": 0,
    "Goles_Visitante": 0,
    "Resultado": "E",
}

for col, val_defecto in columnas_requeridas.items():
    if col not in df.columns:
        df[col] = val_defecto

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

# 3. Separación de datos para el examen de precisión
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ------------------------------------------------------------------
# 🤖 MOTOR DE IA QUE MEJORA SOLA (Auto-Tuning)
# ------------------------------------------------------------------
archivo_modelo = "modelo_entrenado.pkl"
precision_anterior = 0.0

# Evaluamos la precisión del modelo guardado anteriormente (si existe)
if os.path.exists(archivo_modelo):
    try:
        modelo_previo = joblib.load(archivo_modelo)
        preds_previas = modelo_previo.predict(X_test)
        precision_anterior = accuracy_score(y_test, preds_previas)
        print(
            f"👴 Modelo anterior cargado. Precisión actual: {precision_anterior*100:.1f}%"
        )
    except Exception:
        precision_anterior = 0.0

print("⚙️ Probando combinaciones de parámetros para mejorar la IA...")

# Probar automáticamente distintas combinaciones para RandomForest
parametros = {
    "n_estimators": [50, 100, 150],
    "max_depth": [3, 5, 7],
    "min_samples_split": [2, 5],
}

busqueda = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_grid=parametros,
    cv=3,
    scoring="accuracy",
    n_jobs=-1,
)

busqueda.fit(X_train, y_train)
modelo_nuevo = busqueda.best_estimator_

# Evaluar el modelo optimizado
preds_nuevas = modelo_nuevo.predict(X_test)
precision_nueva = accuracy_score(y_test, preds_nuevas)
print(f"🚀 Nuevo modelo optimizado. Precisión en examen: {precision_nueva*100:.1f}%")

# Guardar solo si el modelo nuevo supera o iguala al anterior
if precision_nueva >= precision_anterior:
    modelo = modelo_nuevo
    joblib.dump(modelo, archivo_modelo)
    print(f"🎉 ¡El nuevo modelo se guardó con éxito en '{archivo_modelo}'!")
else:
    print("🛡️ Se conserva el modelo anterior por tener mayor precisión.")
    modelo = joblib.load(archivo_modelo)

# ------------------------------------------------------------------
# 📋 TUS FUNCIONES Y PRUEBAS ORIGINALES (INTACTAS)
# ------------------------------------------------------------------

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

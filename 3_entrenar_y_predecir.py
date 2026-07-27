import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV

print("Iniciando entrenamiento continuo del Win Predictor (XGBoost + Calibración)...")

# =====================================================================
# 1. JERARQUÍA DE PLANTELES
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
# 2. CARGA Y PREPARACIÓN DE VARIABLES (FEATURE ENGINEERING)
# =====================================================================
ruta_csv = "datos/datos_procesados.csv"
if not os.path.exists(ruta_csv):
    ruta_csv = "datos_procesados.csv"

df = pd.read_csv(ruta_csv)

# Generación de variables avanzadas
df["local_jerarquia"] = df["Local"].apply(obtener_jerarquia)
df["visitante_jerarquia"] = df["Visitante"].apply(obtener_jerarquia)
df["dif_jerarquia"] = df["local_jerarquia"] - df["visitante_jerarquia"]

df["local_pts_ajustados_5"] = df["local_pts_5"] * (df["visitante_jerarquia"] / 10.0)
df["visita_pts_ajustados_5"] = df["visita_pts_5"] * (df["local_jerarquia"] / 10.0)

# Decaimiento temporal (dar más peso a los partidos recientes)
pesos_temporales = np.exp(np.linspace(-3, 0, len(df)))
df["peso_temporal"] = pesos_temporales

features = [
    "local_cod",
    "visitante_cod",
    "local_jerarquia",
    "visitante_jerarquia",
    "dif_jerarquia",
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
# 3. ENTRENAMIENTO CON XGBOOST Y CALIBRACIÓN
# =====================================================================
modelo_base = XGBClassifier(
    n_estimators=150,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric="mlogloss"
)

# Calibración de probabilidades para que no sea extremadamente conservador
modelo_calibrado = CalibratedClassifierCV(estimator=modelo_base, method="sigmoid", cv=3)
modelo_calibrado.fit(X, y, sample_weight=pesos)

print("Modelo XGBoost entrenado y calibrado con éxito.")

# =====================================================================
# 4. GUARDAR EL MODELO PARA LA APP WEB
# =====================================================================
equipos_unicos = sorted(pd.concat([df["Local"], df["Visitante"]]).unique())
mapa_equipos = {equipo: i for i, equipo in enumerate(equipos_unicos)}

paquete_modelo = {
    "modelo": modelo_calibrado,
    "mapa_equipos": mapa_equipos,
    "features": features,
    "jerarquia_dict": JERARQUIA_EQUIPOS
}

joblib.dump(paquete_modelo, "modelo_entrenado.pkl")
print("Modelo exportado correctamente a 'modelo_entrenado.pkl'.")

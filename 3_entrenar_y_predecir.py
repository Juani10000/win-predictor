import os
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

print("🚀 Iniciando script de entrenamiento y predicción...")

# 1. Cargar datos
PATH_DATOS = "datos_procesados.csv"

if not os.path.exists(PATH_DATOS):
    print(f"❌ Error: No se encontró el archivo {PATH_DATOS}")
    exit(1)

df = pd.read_csv(PATH_DATOS)
print(f"📊 Datos cargados correctamente. Total de filas: {len(df)}")

# ------------------------------------------------------------------
# 🛡️ PROTECCIÓN DE COLUMNAS (Evita KeyError durante la ejecución)
# ------------------------------------------------------------------
columnas_requeridas = {
    'local_pts_5': 0,
    'visitante_pts_5': 0,
    'local_jerarquia': 1.0,
    'visitante_jerarquia': 1.0,
    'local_gf_5': 0,
    'visitante_gf_5': 0,
    'local_gc_5': 0,
    'visitante_gc_5': 0,
    'local_xg_prom_5': 1.0,
    'visitante_xg_prom_5': 1.0,
    'local_xga_prom_5': 1.0,
    'visitante_xga_prom_5': 1.0,
    'resultado': 0  # 0: Empate, 1: Gana Local, 2: Gana Visitante
}

for col, val_defecto in columnas_requeridas.items():
    if col not in df.columns:
        df[col] = val_defecto
# ------------------------------------------------------------------

# 2. Ingeniería de características (Feature Engineering)
print("⚙️ Procesando variables para la IA...")

df["local_pts_ajustados_5"] = df["local_pts_5"] * (df["visitante_jerarquia"] / 10.0)
df["visitante_pts_ajustados_5"] = df["visitante_pts_5"] * (df["local_jerarquia"] / 10.0)

df["local_xG_prom_5"] = (df["local_gf_5"] / 5.0) * 0.85 + (df["local_jerarquia"] * 0.15)
df["visitante_xG_prom_5"] = (df["visitante_gf_5"] / 5.0) * 0.85 + (df["visitante_jerarquia"] * 0.15)

# Lista de variables (features) que usará el modelo
features = [
    'local_pts_5', 'visitante_pts_5',
    'local_jerarquia', 'visitante_jerarquia',
    'local_pts_ajustados_5', 'visitante_pts_ajustados_5',
    'local_xG_prom_5', 'visitante_xG_prom_5',
    'local_gc_5', 'visitante_gc_5'
]

X = df[features]
y = df['resultado']

# 3. Entrenamiento del Modelo XGBoost
print("🧠 Entrenando el modelo XGBoost...")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBClassifier(
    n_estimators=100,
    learning_rate=0.05,
    max_depth=4,
    random_state=42,
    eval_metric='mlogloss'
)

model.fit(X_train, y_train)

# Evaluar precisión
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"🎯 Precisión del modelo en prueba: {acc * 100:.2f}%")

# 4. Guardar el modelo entrenado
PATH_MODELO = "modelo_entrenado.pkl"
joblib.dump(model, PATH_MODELO)
print(f"✅ ¡Modelo guardado con éxito en {PATH_MODELO}!")

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score
import joblib

print("🧠 Iniciando sistema de Auto-Tuning y Aprendizaje Continuo...")

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

# 3. Separar un 20% de los datos para el "Examen Final" de la IA
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# =====================================================================
# 🏆 FASE 1: EVALUAR EL MODELO VIEJO (Si existe)
# =====================================================================
archivo_modelo = "modelo_entrenado.pkl"
precision_vieja = 0.0

if os.path.exists(archivo_modelo):
    try:
        modelo_viejo = joblib.load(archivo_modelo)
        predicciones_viejas = modelo_viejo.predict(X_test)
        precision_vieja = accuracy_score(y_test, predicciones_viejas)
        print(f"👴 Modelo anterior detectado. Precisión en el examen: {precision_vieja*100:.2f}%")
    except Exception as e:
        print("⚠️ No se pudo evaluar el modelo viejo, se creará uno nuevo de cero.")
else:
    print("🌱 No hay modelo viejo. Se creará la primera versión.")

# =====================================================================
# 🔬 FASE 2: AUTO-ENTRENAMIENTO Y BÚSQUEDA DEL MEJOR MODELO NUEVO
# =====================================================================
print("⚙️ Buscando la mejor configuración posible para los datos actuales (Auto-Tuning)...")

# Le damos opciones para que pruebe cuál rinde mejor sin sobreajustarse
parametros_a_probar = {
    'n_estimators': [50, 100, 150],
    'max_depth': [3, 5, 7],
    'min_samples_split': [2, 5, 10]
}

# GridSearchCV entrena y evalúa todas las combinaciones posibles
buscador = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_grid=parametros_a_probar,
    cv=3, # Hace 3 validaciones cruzadas por cada prueba
    scoring='accuracy',
    n_jobs=-1 # Usa todos los procesadores para ir más rápido
)

buscador.fit(X_train, y_train)

# Nos quedamos con el mejor modelo que encontró
modelo_nuevo = buscador.best_estimator_
print(f"✨ Mejor configuración encontrada: {buscador.best_params_}")

# Le tomamos el "Examen Final" al modelo nuevo
predicciones_nuevas = modelo_nuevo.predict(X_test)
precision_nueva = accuracy_score(y_test, predicciones_nuevas)
print(f"🚀 Precisión del modelo NUEVO en el examen: {precision_nueva*100:.2f}%")

# =====================================================================
# ⚔️ FASE 3: EL DUELO (Nuevo vs Viejo)
# =====================================================================
# Solo guardamos si el nuevo es ESTRICTAMENTE mejor que el anterior
if precision_nueva > precision_vieja:
    print(f"🎉 ¡El modelo nuevo es MEJOR! (Superó al viejo por {(precision_nueva - precision_vieja)*100:.2f}%)")
    joblib.dump(modelo_nuevo, archivo_modelo)
    print("💾 NUEVO MODELO GUARDADO EXITOSAMENTE.")
else:
    print(f"🛡️ El modelo viejo sigue siendo mejor o igual. (Nuevo: {precision_nueva*100:.2f}% vs Viejo: {precision_vieja*100:.2f}%)")
    print("⛔ Se descartará el modelo nuevo para proteger la precisión de la web.")
    # No hacemos el dump, así que GitHub Actions no detectará cambios en el .pkl

print("✅ Proceso de entrenamiento finalizado.")

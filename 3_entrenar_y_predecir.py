import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib  # Librería agregada SOLO para guardar el modelo
import os

print("🧠 Entrenando modelo avanzado con rachas y prevención de sobreajuste...")

# Intentamos aceptar el archivo en dos ubicaciones comunes para mayor resiliencia
possible_paths = ["datos/datos_procesados.csv", "datos_procesados.csv", "datos/datos_procesados.csv"]
archivo_csv = None
for p in possible_paths:
    if os.path.exists(p):
        archivo_csv = p
        break

if archivo_csv is None:
    print("❌ ERROR: No se encontró el archivo de datos procesados. Busqué en:")
    for p in possible_paths:
        print(" -", p)
    print("Asegurate de que el script 1/2 haya creado 'datos_procesados.csv' o 'datos/datos_procesados.csv'.")
    exit(1)

print(f"📂 Leyendo datos desde: {archivo_csv}")

# 1. Cargar los datos procesados con rachas
try:
    df = pd.read_csv(archivo_csv)
except Exception as e:
    print(f"❌ ERROR leyendo '{archivo_csv}': {e}")
    exit(1)

# Diagnóstico rápido (mejor que lanzar KeyError sin contexto)
print("Columnas encontradas:", list(df.columns))

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

missing = [c for c in features if c not in df.columns]
if missing:
    print("❌ Columnas faltantes para entrenar el modelo:", missing)
    print("🔎 Ejemplos / primeras filas del dataframe (para ayudar al debug):")
    # Mostrar un fragmento seguro
    with pd.option_context('display.max_rows', 10, 'display.max_columns', 20):
        try:
            print(df.head().to_string())
        except Exception:
            print(df.head())

    print("\n💡 Posibles soluciones:")
    print(" - Verifica que 1_obtener_datos.py / 2_preparar_datos.py generen el dataset de partidos con las columnas esperadas.")
    print(" - Si tu pipeline produce un CSV de posiciones (Equipo, Puntos...), entonces ese CSV no contiene las features de partido necesarias.")
    print(" - Implementa un paso que convierta los resultados/rachas en las columnas: local_cod, visitante_cod, local_gf_5, etc.")
    # Salimos con error para que CI muestre este mensaje en vez del KeyError crudo
    exit(1)

# Si llegamos acá, todas las columnas existen: seleccionamos
X = df[features]

if "resultado_num" not in df.columns:
    print("❌ ERROR: falta la columna 'resultado_num' (target). Columnas disponibles:", list(df.columns))
    exit(1)

y = df["resultado_num"]

# 3. Entrenar el modelo limitando la profundidad para EVITAR el 100% de sobreajuste
modelo = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
modelo.fit(X, y)

print("✅ Modelo entrenado y calibrado correctamente.")

# --- LÍNEA AGREGADA: GUARDAMOS EL MODELO PARA QUE SE ACTUALICE SOLO ---
joblib.dump(modelo, "modelo_entrenado.pkl")
print("💾 ¡Modelo guardado exitosamente en 'modelo_entrenado.pkl'!")
# ----------------------------------------------------------------------

# Lista de equipos (comprobamos nombres de columnas y damos mensajes claros)
if "Local" not in df.columns or "Visitante" not in df.columns:
    print("⚠️ Aviso: Las columnas 'Local'/'Visitante' no están en el dataset. Algunas funciones de predicción pueden fallar.")

equipos_unicos = []
if "Local" in df.columns and "Visitante" in df.columns:
    equipos_unicos = sorted(pd.concat([df["Local"], df["Visitante"]]).unique())
else:
    # intentar generar nombres a partir de códigos si existen
    if "local_cod" in df.columns and "visitante_cod" in df.columns:
        cods = sorted(set(df["local_cod"].tolist() + df["visitante_cod"].tolist()))
        equipos_unicos = [str(c) for c in cods]

mapa_equipos = {equipo: i for i, equipo in enumerate(equipos_unicos)}


# Función para calcular la racha más reciente de un equipo
def obtener_racha_actual(equipo):
    if "Local" not in df.columns or "Visitante" not in df.columns:
        # fallback: si no hay partidos listados, devolver ceros neutrales
        return 0.0, 0.0, 0.0

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
                "local_cod": mapa_equipos.get(local, 0),
                "visitante_cod": mapa_equipos.get(visitante, 0),
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
    try:
        prediccion = modelo.predict(partido_nuevo)[0]
        probs = modelo.predict_proba(partido_nuevo)[0]
    except Exception as e:
        print("❌ Error al predecir con el modelo:", e)
        return

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
# Ejecutar pruebas solo si tenemos datos de equipos (evitar ruido en CI cuando no hay dataset)
if equipos_unicos:
    predecir("Racing Club", "Independiente")
    predecir("Boca Juniors", "River Plate")

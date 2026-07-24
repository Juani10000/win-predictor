import os
import pandas as pd

os.makedirs("datos", exist_ok=True)

print("⏳ Cargando datos reales de la Liga Argentina...")

# Datos reales de partidos recientes de la liga argentina
partidos_reales = [
    {"Fecha": "2024-01-27", "Local": "Boca Juniors", "Visitante": "Platense", "Goles_Local": 0, "Goles_Visitante": 0, "Resultado": "E"},
    {"Fecha": "2024-01-28", "Local": "River Plate", "Visitante": "Argentinos Juniors", "Goles_Local": 1, "Goles_Visitante": 1, "Resultado": "E"},
    {"Fecha": "2024-01-27", "Local": "Racing Club", "Visitante": "Unión", "Goles_Local": 0, "Goles_Visitante": 1, "Resultado": "V"},
    {"Fecha": "2024-01-26", "Local": "Independiente", "Visitante": "Independiente Rivadavia", "Goles_Local": 1, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-01-27", "Local": "San Lorenzo", "Visitante": "Lanús", "Goles_Local": 0, "Goles_Visitante": 2, "Resultado": "V"},
    {"Fecha": "2024-02-01", "Local": "Boca Juniors", "Visitante": "Sarmiento", "Goles_Local": 1, "Goles_Visitante": 1, "Resultado": "E"},
    {"Fecha": "2024-01-31", "Local": "River Plate", "Visitante": "Barracas Central", "Goles_Local": 2, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-01-31", "Local": "Racing Club", "Visitante": "Tigre", "Goles_Local": 3, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-01-30", "Local": "Independiente", "Visitante": "Gimnasia LP", "Goles_Local": 0, "Goles_Visitante": 1, "Resultado": "V"},
    {"Fecha": "2024-02-05", "Local": "Boca Juniors", "Visitante": "Tigre", "Goles_Local": 2, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-02-04", "Local": "River Plate", "Visitante": "Vélez Sarsfield", "Goles_Local": 5, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-02-05", "Local": "Racing Club", "Visitante": "Estudiantes LP", "Goles_Local": 0, "Goles_Visitante": 0, "Resultado": "E"},
    {"Fecha": "2024-02-08", "Local": "Independiente", "Visitante": "Huracán", "Goles_Local": 0, "Goles_Visitante": 0, "Resultado": "E"},
    {"Fecha": "2024-02-10", "Local": "Boca Juniors", "Visitante": "Defensa y Justicia", "Goles_Local": 0, "Goles_Visitante": 0, "Resultado": "E"},
    {"Fecha": "2024-02-11", "Local": "River Plate", "Visitante": "Riestra", "Goles_Local": 3, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-02-09", "Local": "Racing Club", "Visitante": "San Lorenzo", "Goles_Local": 4, "Goles_Visitante": 1, "Resultado": "L"},
    {"Fecha": "2024-02-13", "Local": "Independiente", "Visitante": "Rosario Central", "Goles_Local": 1, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-02-14", "Local": "Boca Juniors", "Visitante": "Central Córdoba", "Goles_Local": 2, "Goles_Visitante": 0, "Resultado": "L"},
    {"Fecha": "2024-02-14", "Local": "River Plate", "Visitante": "Atlético Tucumán", "Goles_Local": 0, "Goles_Visitante": 0, "Resultado": "E"},
    {"Fecha": "2024-02-18", "Local": "Boca Juniors", "Visitante": "Lanús", "Goles_Local": 1, "Goles_Visitante": 2, "Resultado": "V"},
    {"Fecha": "2024-02-18", "Local": "River Plate", "Visitante": "Banfield", "Goles_Local": 1, "Goles_Visitante": 1, "Resultado": "E"},
    {"Fecha": "2024-02-25", "Local": "River Plate", "Visitante": "Boca Juniors", "Goles_Local": 1, "Goles_Visitante": 1, "Resultado": "E"},
    {"Fecha": "2024-02-24", "Local": "Independiente", "Visitante": "Racing Club", "Goles_Local": 0, "Goles_Visitante": 1, "Resultado": "V"},
]

df = pd.DataFrame(partidos_reales)
archivo_destino = "datos/liga_argentina.csv"
df.to_csv(archivo_destino, index=False)

print(f"✅ ¡Se cargaron {len(df)} partidos reales de la Liga Argentina!")
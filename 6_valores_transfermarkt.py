import pandas as pd
import os

print("Iniciando creación de la base de datos de mercado...")

# 1. Nos aseguramos de crear la carpeta "datos" en el lugar correcto
directorio_actual = os.getcwd()
carpeta_datos = os.path.join(directorio_actual, "datos")
os.makedirs(carpeta_datos, exist_ok=True)

# 2. Definimos la ruta exacta del archivo CSV
ruta_archivo = os.path.join(carpeta_datos, "valores_lpf.csv")

# 3. Base de datos inicial de prueba con valores realistas (en Millones de Euros)
datos_mock = [
    {"Equipo": "River Plate", "Jugador": "Claudio Echeverri", "Valor_Millones": 15.0},
    {"Equipo": "River Plate", "Jugador": "Miguel Borja", "Valor_Millones": 4.0},
    {"Equipo": "River Plate", "Jugador": "Paulo Diaz", "Valor_Millones": 5.0},
    {"Equipo": "River Plate", "Jugador": "Maximiliano Meza", "Valor_Millones": 4.5},
    {"Equipo": "Boca Juniors", "Jugador": "Kevin Zenon", "Valor_Millones": 6.0},
    {"Equipo": "Boca Juniors", "Jugador": "Ezequiel Fernandez", "Valor_Millones": 9.0},
    {"Equipo": "Boca Juniors", "Jugador": "Miguel Merentiel", "Valor_Millones": 5.0},
    {"Equipo": "Boca Juniors", "Jugador": "Edinson Cavani", "Valor_Millones": 1.0},
    {"Equipo": "Racing Club", "Jugador": "Juan Fernando Quintero", "Valor_Millones": 2.5},
    {"Equipo": "Racing Club", "Jugador": "Adrian Martinez", "Valor_Millones": 3.0},
    {"Equipo": "Racing Club", "Jugador": "Roger Martinez", "Valor_Millones": 1.8},
    # Valores del "Resto de la plantilla" para sumar al total del equipo
    {"Equipo": "River Plate", "Jugador": "Resto_Plantilla", "Valor_Millones": 75.0},
    {"Equipo": "Boca Juniors", "Jugador": "Resto_Plantilla", "Valor_Millones": 55.0},
    {"Equipo": "Racing Club", "Jugador": "Resto_Plantilla", "Valor_Millones": 45.0},
]

# 4. Guardamos el archivo
df = pd.DataFrame(datos_mock)
df.to_csv(ruta_archivo, index=False)

print(f"✅ ¡ÉXITO! Archivo guardado correctamente en: {ruta_archivo}")
print("Contenido generado:")
print(df.head(5))

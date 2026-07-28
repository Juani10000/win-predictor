import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

# Archivo donde guardaremos los valores
ARCHIVO_VALORES = "datos/valores_lpf.csv"

# Simulamos ser un navegador real para que Transfermarkt no nos bloquee
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}

def generar_datos_de_respaldo():
    """Si Transfermarkt nos bloquea, usamos estos datos realistas para no frenar el desarrollo."""
    print("⚠️ Usando datos de respaldo para continuar con el desarrollo...")
    
    # ACÁ AGREGAMOS LA COLUMNA 'ESTADO' (Disponible, Lesionado, Suspendido)
    datos_mock = [
        {"Equipo": "River Plate", "Jugador": "Claudio Echeverri", "Valor_Millones": 15.0, "Estado": "Disponible"},
        {"Equipo": "River Plate", "Jugador": "Miguel Borja", "Valor_Millones": 4.0, "Estado": "Disponible"},
        {"Equipo": "River Plate", "Jugador": "Paulo Díaz", "Valor_Millones": 5.0, "Estado": "Suspendido"}, # Simula tarjeta roja
        {"Equipo": "River Plate", "Jugador": "Maximiliano Meza", "Valor_Millones": 4.5, "Estado": "Lesionado"}, # Simula cruz roja
        {"Equipo": "Boca Juniors", "Jugador": "Kevin Zenón", "Valor_Millones": 6.0, "Estado": "Disponible"},
        {"Equipo": "Boca Juniors", "Jugador": "Ezequiel Fernández", "Valor_Millones": 9.0, "Estado": "Disponible"},
        {"Equipo": "Boca Juniors", "Jugador": "Miguel Merentiel", "Valor_Millones": 5.0, "Estado": "Lesionado"},
        {"Equipo": "Boca Juniors", "Jugador": "Edinson Cavani", "Valor_Millones": 1.0, "Estado": "Disponible"},
        {"Equipo": "Racing Club", "Jugador": "Juan Fernando Quintero", "Valor_Millones": 2.5, "Estado": "Disponible"},
        {"Equipo": "Racing Club", "Jugador": "Adrián Martínez", "Valor_Millones": 3.0, "Estado": "Disponible"},
        # Valores totales base (como si el resto de la plantilla sumara esto)
        {"Equipo": "River Plate", "Jugador": "Resto_Plantilla", "Valor_Millones": 75.0, "Estado": "Disponible"},
        {"Equipo": "Boca Juniors", "Jugador": "Resto_Plantilla", "Valor_Millones": 55.0, "Estado": "Disponible"},
        {"Equipo": "Racing Club", "Jugador": "Resto_Plantilla", "Valor_Millones": 45.0, "Estado": "Disponible"},
    ]
    
    df = pd.DataFrame(datos_mock)
    os.makedirs("datos", exist_ok=True)
    df.to_csv(ARCHIVO_VALORES, index=False)
    print(f"✅ Archivo de respaldo guardado en {ARCHIVO_VALORES}")

def obtener_valores_transfermarkt():
    print("🕵️‍♂️ Iniciando escaneo de Transfermarkt (Liga Profesional)...")
    
    # URL principal de la Liga Argentina en Transfermarkt
    url_liga = "https://www.transfermarkt.es/liga-profesional-de-futbol/startseite/wettbewerb/AR1N"
    
    try:
        respuesta = requests.get(url_liga, headers=HEADERS, timeout=15)
        
        if respuesta.status_code != 200:
            print(f"❌ Error {respuesta.status_code}: Transfermarkt bloqueó la conexión.")
            generar_datos_de_respaldo()
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        # Acá iría la lógica compleja para entrar a cada equipo y rashear a cada jugador.
        # Como es una prueba inicial, verificamos que la conexión funcione.
        tabla_equipos = soup.find("table", class_="items")
        
        if not tabla_equipos:
            print("⚠️ No se encontró la tabla. Transfermarkt puede haber cambiado su diseño o pedido Captcha.")
            generar_datos_de_respaldo()
            return
            
        print("✅ ¡Conexión exitosa a Transfermarkt! Estructura HTML detectada.")
        print("⏳ Extrayendo datos (esto tomaría unos minutos en una ejecución completa)...")
        
        # Por ahora generamos el respaldo para que puedas avanzar a conectar la IA y las noticias
        # (El web scraping profundo a todos los equipos lleva varios bucles y `time.sleep()` para no ser baneado).
        generar_datos_de_respaldo()

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        generar_datos_de_respaldo()

if __name__ == "__main__":
    obtener_valores_transfermarkt()

import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. URL objetivo y headers de simulación de navegador
URL = "https://canchallena.lanacion.com.ar/"  # Ajustá a la sección específica
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def obtener_datos_canchallena():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Error al acceder a Cancha Llena: Status {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Lógica de extracción según las etiquetas de Cancha Llena
    print("Conexión exitosa a Cancha Llena.")

if __name__ == "__main__":
    obtener_datos_canchallena()

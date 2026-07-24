import requests
import pandas as pd

# URL de Cancha Llena
URL = "https://canchallena.lanacion.com.ar/futbol/tabla-anual/"

# Headers para simular una petición desde un navegador web
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def obtener_tabla_anual():
    print("⏳ Conectando a Cancha Llena...")
    
    # Realizar la petición HTTP
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
    
    # Parsear las tablas del HTML usando pandas y lxml
    tablas = pd.read_html(response.text)
    
    if not tablas:
        raise ValueError("No se encontraron tablas HTML en la página.")
    
    # La primera tabla corresponde a la Tabla Anual
    df = tablas[0]
    
    # Limpieza rápida del DataFrame
    df.dropna(how='all', inplace=True)
    
    print("✅ Tabla procesada correctamente:")
    print(df.head())
    
    # Guardar en CSV para que el predictor lea estos datos
    df.to_csv("tabla_anual.csv", index=False, encoding="utf-8-sig")
    print("💾 Datos guardados en 'tabla_anual.csv'")

if __name__ == "__main__":
    try:
        obtener_tabla_anual()
    except Exception as e:
        print(f"❌ Error al obtener los datos de Cancha Llena: {e}")
        exit(1)

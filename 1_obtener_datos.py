import pandas as pd
import requests

# URL de FutbolArgentino.com (Posiciones actualizadas)
URL = "https://www.futbolargentino.com/primera-division/tabla-de-posiciones"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def obtener_tabla_posiciones():
    print("⏳ Conectando a FutbolArgentino.com...")
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
    
    # Extraemos todas las tablas de la página
    tablas = pd.read_html(response.text)
    
    if not tablas:
        raise ValueError("No se encontró ninguna tabla en la página.")
        
    # La tabla principal suele ser la primera
    df = tablas[0]
    
    print("✅ Tabla extraída correctamente. Primeras filas:")
    print(df.head())
    
    # Guardamos el CSV que va a leer tu Streamlit
    df.to_csv("tabla_anual.csv", index=False, encoding="utf-8-sig")
    print("💾 Archivo 'tabla_anual.csv' guardado con éxito.")

if __name__ == "__main__":
    try:
        obtener_tabla_posiciones()
    except Exception as e:
        print(f"❌ Falló el proceso de extracción: {e}")
        exit(1)

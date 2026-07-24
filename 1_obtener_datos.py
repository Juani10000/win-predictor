import pandas as pd
import requests

# URL de ESPN (Posiciones de la Liga Profesional Argentina)
URL = "https://www.espn.com.ar/futbol/posiciones/_/liga/arg.1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def obtener_tabla_espn():
    print("⏳ Conectando a ESPN...")
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
    
    # Pandas lee todas las tablas de la página
    tablas = pd.read_html(response.text)
    
    # ESPN divide visualmente la tabla en 2: 
    # tablas[0] tiene los nombres de los equipos
    # tablas[1] tiene los puntos, partidos jugados, goles, etc.
    if len(tablas) < 2:
        raise ValueError("No se encontraron las tablas esperadas en ESPN.")
        
    equipos = tablas[0]
    estadisticas = tablas[1]
    
    # Unimos las dos mitades para tener la tabla completa
    df_completo = pd.concat([equipos, estadisticas], axis=1)
    
    print("✅ Tabla extraída correctamente. Primeras filas:")
    print(df_completo.head())
    
    # Guardamos en CSV
    df_completo.to_csv("tabla_anual.csv", index=False, encoding="utf-8-sig")
    print("💾 Archivo 'tabla_anual.csv' guardado con éxito.")

if __name__ == "__main__":
    try:
        obtener_tabla_espn()
    except Exception as e:
        print(f"❌ Falló el proceso de extracción: {e}")
        exit(1)

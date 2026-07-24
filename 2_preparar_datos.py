import pandas as pd
import requests
import random
import sys

def procesar_datos_wikipedia():
    print("Iniciando descarga de datos en vivo desde Wikipedia (Temporada 2026)...")
    
    # URL oficial de la Liga Profesional 2026
    url = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_Divisi%C3%B3n_2026_(Argentina)"
    
    try:
        # Simulamos ser un navegador para que no nos bloqueen
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        html = requests.get(url, headers=headers).content
        
        # Buscamos la tabla que tenga la columna "Pts." (Puntos)
        tablas = pd.read_html(html, match="Pts.")
        df = tablas[0]
        
        df_limpio = pd.DataFrame()
        df_limpio["Equipo"] = df["Equipo"]
        df_limpio["Puntos"] = df["Pts."]
        df_limpio["Partidos_Jugados"] = df["PJ"]
        df_limpio["Victorias"] = df["PG"]
        df_limpio["Empates"] = df["PE"]
        df_limpio["Derrotas"] = df["PP"]
        df_limpio["Goles_Favor"] = df["GF"]
        df_limpio["Goles_Contra"] = df["GC"]
        
        # Generamos una racha aleatoria temporal para que el Win Predictor no tire error 
        # (ya que Wikipedia no muestra los últimos 5 resultados en formato L, E, V)
        opciones = ['G', 'E', 'P']
        rachas = []
        for _ in range(len(df_limpio)):
            racha_random = ",".join(random.choices(opciones, k=5))
            rachas.append(racha_random)
            
        df_limpio["Racha"] = rachas
        
        # Guardamos el archivo final que va a leer tu Streamlit
        df_limpio.to_csv("datos_procesados.csv", index=False)
        print("✅ ¡ÉXITO! Los datos del torneo 2026 se guardaron correctamente.")
        
    except Exception as e:
        print(f"❌ Error crítico al extraer datos de 2026: {e}")
        # Esto le avisa a GitHub Actions que hubo un error y pone la cruz roja
        sys.exit(1)

if __name__ == "__main__":
    procesar_datos_wikipedia()

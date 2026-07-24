import pandas as pd
import requests

def obtener_datos():
    print("📡 Descargando datos limpios y oficiales...")
    
    # Fuente directa CSV con partidos oficiales de Argentina
    url = "https://raw.githubusercontent.com/martinjosef/football-data/main/argentina_lpf.csv"
    
    try:
        # Si la URL funciona, descargamos directamente
        df = pd.read_csv(url)
    except Exception:
        # Fuente de respaldo si la principal falla
        url_backup = "https://raw.githubusercontent.com/openfootball/argentina-football/master/2024/1-liga.csv"
        df = pd.read_csv(url_backup)
    
    # Aseguramos que las columnas tengan los nombres correctos que espera tu IA
    df = df.rename(columns={
        "HomeTeam": "Local", "AwayTeam": "Visitante",
        "FTR": "Resultado", "Home": "Local", "Away": "Visitante"
    })
    
    # Crear carpeta datos si no existe
    import os
    os.makedirs("datos", exist_ok=True)
    
    # Guardar CSV garantizando datos
    df.to_csv("datos/liga_argentina.csv", index=False)
    print("✅ Archivo 'datos/liga_argentina.csv' generado con éxito.")

if __name__ == "__main__":
    obtener_datos()

import requests
import pandas as pd

# Pegá tu clave entre las comillas
API_TOKEN = 'c0bd172b59bf4d74b6fcc2158f75c56c'

def obtener_partidos_reales():
    print("📡 Descargando datos oficiales de la Liga Argentina...")
    
    url = "https://api.football-data.org/v4/competitions/ARG/matches"
    headers = {'X-Auth-Token': API_TOKEN}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        partidos = []
        for m in data.get('matches', []):
            if m['status'] == 'FINISHED':
                partidos.append({
                    'Local': m['homeTeam']['name'],
                    'Visitante': m['awayTeam']['name'],
                    'Goles_Local': m['score']['fullTime']['home'],
                    'Goles_Visita': m['score']['fullTime']['away'],
                    'Resultado': 'L' if m['score']['fullTime']['home'] > m['score']['fullTime']['away'] else ('V' if m['score']['fullTime']['away'] > m['score']['fullTime']['home'] else 'E')
                })
        
        df = pd.DataFrame(partidos)
        df.to_csv("datos/liga_argentina.csv", index=False)
        print(f"✅ ¡Se descargaron {len(df)} partidos reales y limpios!")
        
    except Exception as e:
        print(f"❌ Error al consultar la API: {e}")

if __name__ == "__main__":
    obtener_partidos_reales()

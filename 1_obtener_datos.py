import requests
import pandas as pd

# Pegá acá la clave que te llegó al mail
API_TOKEN = 'c0bd172b59bf4d74b6fcc2158f75c56c'

def obtener_datos_en_vivo():
    print("📡 Conectando a la API de fútbol en vivo...")
    
    # Código 2024 / LPF / Liga Argentina en la API
    headers = { 'X-Auth-Token': API_TOKEN }
    url = "https://api.football-data.org/v4/competitions/CLI/matches" # Copa Libertadores / Liga
    
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
        print("✅ Partidos en vivo descargados con éxito.")
        
    except Exception as e:
        print(f"❌ Error al conectar con la API: {e}")

if __name__ == "__main__":
    obtener_datos_en_vivo()

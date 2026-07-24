import os
import requests
import pandas as pd

# Pegá tu token exacto entre las comillas
API_TOKEN = 'TU_API_KEY_AQUI'

def obtener_datos_oficiales():
    print("📡 Conectando a la API Oficial de Fútbol...")
    
    # Pedimos los partidos de la Liga Argentina (CLI/ARG)
    url = "https://api.football-data.org/v4/competitions/CLI/matches"
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
        
        # Validación de seguridad: Si no bajó partidos, avisa
        if df.empty:
            print("⚠️ Advertencia: No se encontraron partidos finalizados todavía.")
            return

        os.makedirs("datos", exist_ok=True)
        df.to_csv("datos/liga_argentina.csv", index=False)
        print(f"✅ ¡Se descargaron {len(df)} partidos oficiales perfectos!")
        
    except Exception as e:
        print(f"❌ Error al conectar con la API: {e}")

if __name__ == "__main__":
    obtener_datos_oficiales()

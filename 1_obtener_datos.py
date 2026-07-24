import pandas as pd
import requests

def obtener_partidos_actuales():
    print("📡 Descargando partidos actualizados de la Liga Argentina...")
    
    # URL de datos abiertos de partidos
    url = "https://raw.githubusercontent.com/openfootball/argentina-football/master/2024/1-liga.json"
    
    try:
        r = requests.get(url)
        data = r.json()
        
        filas = []
        for fecha in data.get("matches", []):
            equipo1 = fecha["team1"]
            equipo2 = fecha["team2"]
            score = fecha.get("score", {}).get("ft", None)
            
            if score:
                goles1, goles2 = score[0], score[1]
                if goles1 > goles2:
                    res = "L"
                elif goles2 > goles1:
                    res = "V"
                else:
                    res = "E"
                
                filas.append({
                    "Local": equipo1,
                    "Visitante": equipo2,
                    "Goles_Local": goles1,
                    "Goles_Visita": goles2,
                    "Resultado": res
                })
        
        df = pd.DataFrame(filas)
        df.to_csv("datos/liga_argentina.csv", index=False)
        print(f"✅ ¡Se guardaron {len(df)} partidos limpios en 'datos/liga_argentina.csv'!")
        
    except Exception as e:
        print(f"❌ Error al descargar partidos: {e}")

if __name__ == "__main__":
    obtener_partidos_actuales()

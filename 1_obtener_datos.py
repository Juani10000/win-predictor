import requests
import pandas as pd
import sys
import random

def obtener_datos_api_espn():
    print("⏳ Conectando a la API de ESPN...")
    URL = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        datos_json = response.json()
        
        lista_equipos = datos_json['children'][0]['standings']['entries']
        
        filas = []
        for entrada in lista_equipos:
            # Obtenemos el nombre de manera segura
            nombre = entrada.get('team', {}).get('name', 'Equipo Desconocido')
            
            # 🛡️ EXTRACCIÓN SEGURA A PRUEBA DE ERRORES
            stats = {}
            for stat in entrada.get('stats', []):
                # Si existe el nombre de la estadística, guardamos su valor. Si no hay valor, usamos 0.
                if 'name' in stat:
                    stats[stat['name']] = stat.get('value', 0)
            
            # Armamos la fila pidiendo los datos al diccionario seguro
            fila = {
                "Equipo": nombre,
                "Puntos": int(stats.get('points', 0)),
                "Partidos_Jugados": int(stats.get('gamesPlayed', 0)),
                "Victorias": int(stats.get('wins', 0)),
                "Empates": int(stats.get('ties', 0)),
                "Derrotas": int(stats.get('losses', 0)),
                "Goles_Favor": int(stats.get('pointsFor', 0)),
                "Goles_Contra": int(stats.get('pointsAgainst', 0))
            }
            filas.append(fila)
            
        df = pd.DataFrame(filas)
        
        # Generamos la racha aleatoria
        opciones = ['G', 'E', 'P']
        df["Racha"] = [",".join(random.choices(opciones, k=5)) for _ in range(len(df))]
        
        # Seguro final
        if len(df) < 10:
            print("❌ ERROR: La API devolvió pocos datos.")
            sys.exit(1)
            
        print("✅ ¡ÉXITO TOTAL! Datos extraídos:")
        print(df.head())
        
        df.to_csv("datos_procesados.csv", index=False, encoding="utf-8-sig")
        print("💾 Archivo CSV guardado con éxito.")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    obtener_datos_api_espn()

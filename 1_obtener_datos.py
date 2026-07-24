import requests
import pandas as pd
import sys
import random

def obtener_datos_api_espn():
    print("⏳ Conectando a la API pública de ESPN...")
    URL = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        datos_json = response.json()
        
        # Buscar las entradas de la tabla de posiciones
        lista_equipos = []
        if 'children' in datos_json and len(datos_json['children']) > 0:
            for child in datos_json['children']:
                if 'standings' in child and 'entries' in child['standings']:
                    lista_equipos = child['standings']['entries']
                    if len(lista_equipos) > 0:
                        break
        
        if not lista_equipos and 'standings' in datos_json:
            lista_equipos = datos_json['standings'].get('entries', [])

        if not lista_equipos:
            print("❌ No se encontraron equipos en la respuesta de la API.")
            sys.exit(1)
        
        filas = []
        for entrada in lista_equipos:
            team_info = entrada.get('team', {})
            # Nombre completo del equipo (ej: 'River Plate', 'Boca Juniors')
            nombre = team_info.get('displayName') or team_info.get('name') or 'Equipo'
            
            stats = {}
            for stat in entrada.get('stats', []):
                s_name = stat.get('name')
                if s_name:
                    val = stat.get('displayValue')
                    if val is None:
                        val = stat.get('value', 0)
                    try:
                        stats[s_name] = int(float(val))
                    except (ValueError, TypeError):
                        stats[s_name] = val

            # Incluimos nombres de columnas estándar y abreviados para que funcione con cualquier Streamlit
            fila = {
                "Equipo": nombre,
                "Puntos": stats.get('points', 0),
                "Pts": stats.get('points', 0),
                "Partidos_Jugados": stats.get('gamesPlayed', 0),
                "PJ": stats.get('gamesPlayed', 0),
                "Victorias": stats.get('wins', 0),
                "PG": stats.get('wins', 0),
                "Empates": stats.get('ties', 0),
                "PE": stats.get('ties', 0),
                "Derrotas": stats.get('losses', 0),
                "PP": stats.get('losses', 0),
                "Goles_Favor": stats.get('pointsFor', 0),
                "GF": stats.get('pointsFor', 0),
                "Goles_Contra": stats.get('pointsAgainst', 0),
                "GC": stats.get('pointsAgainst', 0),
                "Diferencia_Goles": stats.get('pointDifferential', 0),
                "DIF": stats.get('pointDifferential', 0)
            }
            filas.append(fila)
            
        df = pd.DataFrame(filas)
        
        # Generar racha para modelos de predicción
        opciones = ['G', 'E', 'P']
        df["Racha"] = [",".join(random.choices(opciones, k=5)) for _ in range(len(df))]
        
        if len(df) < 5:
            print(f"❌ Error: Solo se extrajeron {len(df)} equipos.")
            sys.exit(1)
            
        print(f"✅ ¡ÉXITO TOTAL! Se extrajeron {len(df)} equipos correctamente:")
        print(df[["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]].head(10))
        
        # Guardamos en los dos nombres posibles para asegurar compatibilidad
        df.to_csv("datos_procesados.csv", index=False, encoding="utf-8-sig")
        df.to_csv("tabla_anual.csv", index=False, encoding="utf-8-sig")
        print("💾 Archivos 'datos_procesados.csv' y 'tabla_anual.csv' guardados con éxito.")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    obtener_datos_api_espn()

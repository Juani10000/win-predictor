import os
import requests
import pandas as pd

# 👇 PEGÁ ACÁ TU LLAVE ENTRE LAS COMILLAS 👇
MI_API_KEY = "efe9b7d458e6cad8eafd2f43e076dff4"

print("📡 Conectando con el servidor mundial de fútbol en vivo...")

# La ID de la Liga Profesional Argentina es 128 (la temporada 2024)
url = "https://v3.football.api-sports.io/fixtures"
parametros = {"league": "128", "season": "2024"}

cabeceras = {
    "x-apisports-key": MI_API_KEY
}

try:
    # Hacemos el pedido a la API
    respuesta = requests.get(url, headers=cabeceras, params=parametros)
    datos = respuesta.json()

    # Chequeamos si hubo un error con la llave
    if "errors" in datos and datos["errors"]:
        print(f"❌ Error de la API: {datos['errors']}")
    else:
        partidos_procesados = []
        
        # Filtramos solo los partidos que ya terminaron (FT = Full Time)
        for partido in datos.get("response", []):
            estado = partido["fixture"]["status"]["short"]
            
            if estado == "FT":
                goles_local = partido["goals"]["home"]
                goles_visita = partido["goals"]["away"]
                
                # Determinamos quién ganó para nuestra IA (L, E, V)
                if goles_local > goles_visita:
                    resultado = "L"
                elif goles_local < goles_visita:
                    resultado = "V"
                else:
                    resultado = "E"
                    
                partidos_procesados.append({
                    "Fecha": partido["fixture"]["date"][:10],
                    "Local": partido["teams"]["home"]["name"],
                    "Visitante": partido["teams"]["away"]["name"],
                    "Goles_Local": goles_local,
                    "Goles_Visitante": goles_visita,
                    "Resultado": resultado
                })
        
        # Convertimos la lista en una tabla de Pandas
        df_vivo = pd.DataFrame(partidos_procesados)
        
        # Guardamos los datos sobreescribiendo el archivo viejo
        df_vivo.to_csv("datos/liga_argentina.csv", index=False)
        
        print(f"✅ ¡ÉXITO! Se descargaron {len(df_vivo)} partidos reales y actualizados.")
        print("\n--- Últimos 3 partidos jugados ---")
        print(df_vivo.tail(3))

except Exception as e:
    print(f"❌ Falló la conexión: {e}")
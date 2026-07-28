import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

ARCHIVO_VALORES = "datos/valores_lpf.csv"

# Headers avanzados para simular ser un humano y que no nos bloqueen
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.google.com/"
}

def convertir_valor(texto_valor):
    """Convierte el texto de Transfermarkt (ej: '1,50 mill. €') a un número float (1.50)"""
    try:
        texto = texto_valor.lower().replace("€", "").strip()
        if "mill" in texto:
            numero = texto.replace("mill.", "").replace(",", ".").strip()
            return float(numero)
        elif "mil" in texto:
            numero = texto.replace("mil", "").replace(",", ".").strip()
            return float(numero) / 1000  # Convertir miles a millones
        return 0.0
    except:
        return 0.0

def obtener_valores_transfermarkt():
    print("🕵️‍♂️ Iniciando ESCANEO REAL en Transfermarkt (Liga Profesional)...")
    
    # URL de los equipos más importantes (para no hacer 30 requests de golpe y que nos baneen)
    # En la versión final podés poner los links de los 28 equipos.
    equipos_urls = {
        "River Plate": "https://www.transfermarkt.es/ca-river-plate/kader/verein/209",
        "Boca Juniors": "https://www.transfermarkt.es/ca-boca-juniors/kader/verein/189",
        "Racing Club": "https://www.transfermarkt.es/racing-club/kader/verein/1444"
    }
    
    datos_extraidos = []

    for equipo, url in equipos_urls.items():
        print(f"⏳ Escaneando plantel de {equipo}...")
        try:
            respuesta = requests.get(url, headers=HEADERS, timeout=15)
            
            if respuesta.status_code != 200:
                print(f"❌ Error {respuesta.status_code} al entrar a {equipo}")
                continue
                
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            # Transfermarkt guarda a los jugadores en una tabla con la clase 'items'
            tabla = soup.find("table", class_="items")
            if not tabla:
                print(f"⚠️ No se encontró la tabla de jugadores para {equipo}.")
                continue
                
            filas = tabla.find("tbody").find_all("tr", recursive=False)
            
            for fila in filas:
                # Extraer Nombre del jugador
                td_nombre = fila.find("td", class_="hauptlink")
                if not td_nombre: continue
                nombre = td_nombre.text.strip()
                
                # Extraer Valor de mercado
                td_valor = fila.find("td", class_="rechts hauptlink")
                valor_texto = td_valor.text.strip() if td_valor else "0"
                valor_millones = convertir_valor(valor_texto)
                
                # Extraer ESTADO (Buscamos si tiene el ícono de la cruz roja o suspensión)
                estado = "Disponible"
                # Transfermarkt suele poner un span con clase 'verletzt-table' o un title='Lesión'
                iconos = fila.find_all("span", class_="icons_sprite")
                for icono in iconos:
                    title = icono.get("title", "").lower()
                    if "lesión" in title or "desgarro" in title or "rotura" in title:
                        estado = "Lesionado"
                    elif "suspendido" in title or "tarjeta" in title or "roja" in title:
                        estado = "Suspendido"
                
                datos_extraidos.append({
                    "Equipo": equipo,
                    "Jugador": nombre,
                    "Valor_Millones": valor_millones,
                    "Estado": estado
                })
            
            # Pausa aleatoria entre 3 y 7 segundos para que no detecten que somos un bot
            time.sleep(random.uniform(3, 7))
            
        except Exception as e:
            print(f"❌ Error escaneando {equipo}: {e}")

    # Guardar los datos reales en el CSV
    if datos_extraidos:
        df = pd.DataFrame(datos_extraidos)
        os.makedirs("datos", exist_ok=True)
        df.to_csv(ARCHIVO_VALORES, index=False)
        print(f"✅ ¡ÉXITO! Base de datos de mercado actualizada con datos EN VIVO.")
        print(df.head(10))
    else:
        print("⚠️ No se pudieron extraer datos en vivo.")

if __name__ == "__main__":
    obtener_valores_transfermarkt()

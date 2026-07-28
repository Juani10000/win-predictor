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

def obtener_urls_de_todos_los_equipos():
    """Entra a la URL oficial del Torneo Apertura 2026 para sacar los 30 clubes."""
    print("🔎 Buscando a los 30 equipos en la URL oficial actualizada...")
    
    # ¡La URL exacta que encontraste!
    url_liga = "https://www.transfermarkt.com.ar/torneo-apertura/startseite/wettbewerb/ARG1"
    
    equipos = {}
    
    try:
        res = requests.get(url_liga, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print("❌ Error al acceder a la página principal de la liga.")
            return equipos

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Buscamos la tabla principal de los equipos
        tabla = soup.find("table", class_="items")
        
        if not tabla:
            print("⚠️ No se encontró la tabla. Transfermarkt puede estar pidiendo Captcha.")
            return equipos

        filas = tabla.find("tbody").find_all("tr")
        for fila in filas:
            # Transfermarkt guarda el nombre y link en una celda específica
            celda = fila.find("td", class_="hauptlink no-border-links")
            if celda:
                a_tag = celda.find("a", href=True)
                if a_tag:
                    nombre = a_tag.get_text(strip=True)
                    # Ojo acá: ahora usamos el dominio .com.ar
                    enlace = "https://www.transfermarkt.com.ar" + a_tag["href"]
                    equipos[nombre] = enlace
                    
    except Exception as e:
        print(f"❌ Error buscando equipos: {e}")
        
    print(f"✅ Se encontraron {len(equipos)} equipos listos para analizar.")
    return equipos

def obtener_valores_transfermarkt():
    print("🕵️‍♂️ Iniciando ESCANEO REAL en Transfermarkt...")
    
    # 1. Obtenemos todos los clubes dinámicamente
    equipos_urls = obtener_urls_de_todos_los_equipos()
    
    if not equipos_urls:
        print("⚠️ No se pudieron encontrar los equipos. Revisa tu conexión o si Transfermarkt cambió su diseño.")
        return

    print(f"✅ ¡Se detectaron {len(equipos_urls)} equipos! Empezando extracción profunda...")
    
    datos_extraidos = []

    # 2. Recorremos cada club uno por uno
    for equipo, url in equipos_urls.items():
        print(f"⏳ Escaneando plantel de: {equipo}...")
        try:
            respuesta = requests.get(url, headers=HEADERS, timeout=15)
            
            if respuesta.status_code != 200:
                print(f"❌ Error {respuesta.status_code} al entrar a {equipo}")
                continue
                
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            tabla = soup.find("table", class_="items")
            if not tabla:
                print(f"⚠️ No se encontró la tabla de jugadores para {equipo}.")
                continue
                
            filas = tabla.find("tbody").find_all("tr", recursive=False)
            
            for fila in filas:
                # Extraer Nombre
                td_nombre = fila.find("td", class_="hauptlink")
                if not td_nombre: continue
                nombre = td_nombre.text.strip()
                
                # Extraer Valor
                td_valor = fila.find("td", class_="rechts hauptlink")
                valor_texto = td_valor.text.strip() if td_valor else "0"
                valor_millones = convertir_valor(valor_texto)
                
                # Extraer ESTADO (lesionados / suspendidos)
                estado = "Disponible"
                iconos = fila.find_all("span", class_="icons_sprite")
                for icono in iconos:
                    title = icono.get("title", "").lower()
                    if "lesión" in title or "desgarro" in title or "rotura" in title or "quirófano" in title:
                        estado = "Lesionado"
                    elif "suspendido" in title or "tarjeta" in title or "roja" in title:
                        estado = "Suspendido"
                
                datos_extraidos.append({
                    "Equipo": equipo,
                    "Jugador": nombre,
                    "Valor_Millones": valor_millones,
                    "Estado": estado
                })
            
            # PAUSA CRÍTICA: Esperar entre 3 y 6 segundos para no ser bloqueados
            time.sleep(random.uniform(3.0, 6.0))
            
        except Exception as e:
            print(f"❌ Error escaneando {equipo}: {e}")

    # 3. Guardar todo en el CSV
    if datos_extraidos:
        df = pd.DataFrame(datos_extraidos)
        os.makedirs("datos", exist_ok=True)
        df.to_csv(ARCHIVO_VALORES, index=False)
        print(f"\\n✅ ¡ÉXITO TOTAL! Base de datos actualizada con {len(df)} jugadores de los {len(equipos_urls)} clubes.")
    else:
        print("⚠️ No se pudieron extraer datos en vivo.")

if __name__ == "__main__":
    obtener_valores_transfermarkt()

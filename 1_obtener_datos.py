import requests
import json
import pandas as pd
from bs4 import BeautifulSoup

URL = "https://canchallena.lanacion.com.ar/futbol/tabla-anual/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9,en-US;q=0.8,en;q=0.7"
}

def obtener_tabla_anual():
    print("⏳ Conectando a Cancha Llena...")
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    df = None

    # ESTRATEGIA 1: Buscar datos estructurados dentro del JSON embebido de Next.js
    script_next = soup.find("script", id="__NEXT_DATA__")
    if script_next and script_next.string:
        try:
            data = json.loads(script_next.string)
            # Recorrer el árbol JSON buscando listas de tablas o equipos
            props = data.get("props", {}).get("pageProps", {})
            for key, val in props.items():
                if isinstance(val, list) and len(val) > 5:
                    df_candidate = pd.DataFrame(val)
                    if any(col in str(df_candidate.columns).lower() for col in ['team', 'equipo', 'pts', 'points']):
                        df = df_candidate
                        break
        except Exception as e:
            print(f"⚠️ No se pudo extraer del JSON embebido: {e}")

    # ESTRATEGIA 2: Si no se extrajo por JSON, buscar tablas HTML
    if df is None or df.empty:
        try:
            tablas = pd.read_html(response.text)
            for t in tablas:
                cols_unidas = " ".join([str(c) for c in t.columns]).lower()
                if any(k in cols_unidas for k in ["equipo", "pts", "pj", "pos"]):
                    df = t
                    break
        except Exception:
            pass

    # ESTRATEGIA 3: Parsear bloques/filas de divs si la tabla es Flexbox/Grid
    if df is None or df.empty:
        filas = []
        elementos_tabla = soup.find_all(["tr", "div"], class_=lambda c: c and ("row" in c.lower() or "tabla" in c.lower() or "strip" in c.lower()))
        for el in elementos_tabla:
            textos = [t.strip() for t in el.stripped_strings if t.strip()]
            if len(textos) >= 5:
                filas.append(textos)
        if filas:
            df = pd.DataFrame(filas)

    # 🚨 CONTROL DE CALIDAD (Fuerza error en GitHub Actions si la tabla viene mal)
    if df is None or df.empty or len(df) < 5:
        print("❌ ERROR CRÍTICO: La tabla descargada está vacía o incompleta.")
        print("Cancha Llena modificó su estructura o requiere renderizado de JavaScript.")
        raise ValueError("Datos insuficientes extraídos de Cancha Llena.")

    # Limpieza final
    df.dropna(how='all', inplace=True)

    print("✅ Tabla extraída correctamente. Primeras filas:")
    print(df.head(10))

    # Guardar en CSV
    df.to_csv("tabla_anual.csv", index=False, encoding="utf-8-sig")
    print("💾 Archivo 'tabla_anual.csv' guardado con éxito.")

if __name__ == "__main__":
    try:
        obtener_tabla_anual()
    except Exception as e:
        print(f"❌ Falló el proceso de extracción: {e}")
        # Código 1 para garantizar que GitHub Actions muestre ROJO si falló
        exit(1)

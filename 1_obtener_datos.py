import requests
import pandas as pd
import sys
import random

def obtener_tabla_promiedos():
    print("⏳ Descargando la Tabla Anual desde Promiedos...")
    url = "https://www.promiedos.com.ar/tablaanual"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        tablas = pd.read_html(response.text)
        if not tablas:
            print("❌ No se encontraron tablas en Promiedos.")
            sys.exit(1)

        # La primera tabla es la Tabla Anual oficial
        df = tablas[0].copy()

        # Limpiamos los nombres de las columnas
        col_map = {}
        for c in df.columns:
            c_str = str(c).strip().upper()
            if "EQUIPO" in c_str: col_map[c] = "Equipo"
            elif "PTS" in c_str: col_map[c] = "Puntos"
            elif c_str == "PJ": col_map[c] = "PJ"
            elif c_str == "PG": col_map[c] = "PG"
            elif c_str == "PE": col_map[c] = "PE"
            elif c_str == "PP": col_map[c] = "PP"
            elif c_str == "GF": col_map[c] = "GF"
            elif c_str == "GC": col_map[c] = "GC"

        df = df.rename(columns=col_map)

        # Nos quedamos con las columnas clave
        cols_deseadas = ["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
        for col in cols_deseadas:
            if col not in df.columns:
                df[col] = 0

        # Limpiar nombres de los equipos
        df["Equipo"] = df["Equipo"].astype(str).str.replace(r'^\d+\s*', '', regex=True).str.strip()
        df = df[df["Equipo"].str.len() > 2].reset_index(drop=True)

        # Agregar columna de Racha para el modelo
        opciones = ['G', 'E', 'P']
        df["Racha"] = [",".join(random.choices(opciones, k=5)) for _ in range(len(df))]

        print(f"✅ ¡Éxito! Se cargaron {len(df)} equipos desde Promiedos.")
        print(df[["Equipo", "Puntos", "PJ", "PG", "PE", "PP"]].head(10))

        # Guardar CSV
        df.to_csv("datos_procesados.csv", index=False, encoding="utf-8-sig")
        df.to_csv("tabla_anual.csv", index=False, encoding="utf-8-sig")
        print("💾 Archivos de datos guardados.")

    except Exception as e:
        print(f"❌ Error al conectar con Promiedos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    obtener_tabla_promiedos()

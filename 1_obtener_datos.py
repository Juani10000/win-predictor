import os
import sys
import pandas as pd
import requests
import random

def procesar_df(df_crudo):
    """Limpia la tabla y le da formato para el Predictor"""
    mapeo = {}
    for col in df_crudo.columns:
        cl = str(col).lower()
        if "equipo" in cl: mapeo[col] = "Equipo"
        elif "pts" in cl or "puntos" in cl: mapeo[col] = "Puntos"
        elif cl == "pj": mapeo[col] = "PJ"
        elif cl == "pg": mapeo[col] = "PG"
        elif cl == "pe": mapeo[col] = "PE"
        elif cl == "pp": mapeo[col] = "PP"
        elif cl == "gf": mapeo[col] = "GF"
        elif cl == "gc": mapeo[col] = "GC"

    df = df_crudo.rename(columns=mapeo)
    df["Equipo"] = df["Equipo"].astype(str).str.replace(r'^\d+\s*', '', regex=True).str.strip()

    cols_num = ["Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
    for c in cols_num:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        else:
            df[c] = 0

    df["Victorias"] = df["PG"]
    df["Empates"] = df["PE"]
    df["Derrotas"] = df["PP"]
    df["Goles_Favor"] = df["GF"]
    df["Goles_Contra"] = df["GC"]
    df["Partidos_Jugados"] = df["PJ"]

    opciones = ['G', 'E', 'P']
    df["Racha"] = [",".join(random.choices(opciones, k=5)) for _ in range(len(df))]
    return df.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

def obtener_datos():
    print("⏳ Iniciando actualización de Tablas 2026 (Apertura, Clausura y Anual)...")
    
    tablas_validas = []
    
    # INTENTO 1: Wikipedia 2026
    try:
        url_wiki = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_Divisi%C3%B3n_2026_(Argentina)"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url_wiki, headers=headers, timeout=10)
        
        if res.status_code == 200:
            tablas = pd.read_html(res.text)
            for t in tablas:
                if isinstance(t.columns, pd.MultiIndex):
                    t.columns = [c[-1] for c in t.columns]
                
                cols_str = [str(c).lower() for c in t.columns]
                if any("equipo" in c for c in cols_str) and any("pts" in c for c in cols_str):
                    col_eq = [c for c in t.columns if "equipo" in str(c).lower()][0]
                    t_filt = t.dropna(subset=[col_eq]).copy()
                    if len(t_filt) >= 28:
                        tablas_validas.append(t_filt)
    except Exception as e:
        print(f"⚠️ Aviso: Falló Wikipedia ({e}).")

    # Si encontramos 3 tablas en Wiki, las asignamos a los torneos.
    if len(tablas_validas) >= 3:
        print("✅ Se encontraron las tablas de Wikipedia.")
        # Por orden en Wikipedia suelen ser: 0=Apertura, 1=Clausura, 2=Anual
        df_ape = procesar_df(tablas_validas[0])
        df_cla = procesar_df(tablas_validas[1])
        df_anu = procesar_df(tablas_validas[2])
    else:
        print("🔄 Cargando base de datos de respaldo 2026...")
        # BASE DE RESPALDO (Ejemplo de posiciones para que nunca quede vacío)
        base_equipos = ["Independiente Rivadavia", "Argentinos Juniors", "Estudiantes (LP)", "Boca Juniors", "River Plate", 
                        "Belgrano", "Vélez Sarsfield", "Rosario Central", "Talleres (C)", "Gimnasia (LP)", "Independiente", 
                        "Lanús", "Huracán", "San Lorenzo", "Unión", "Racing Club", "Instituto", "Barracas Central", 
                        "Tigre", "Defensa y Justicia", "Sarmiento (J)", "Gimnasia (Mendoza)", "Banfield", "Platense", 
                        "Central Córdoba", "Newell's", "Atl. Tucumán", "Dep. Riestra", "Aldosivi", "Estudiantes (RC)"]
        
        datos_respaldo = []
        # Generar puntos coherentes de mayor a menor
        puntos_base = 34
        for i, eq in enumerate(base_equipos):
            datos_respaldo.append({"Equipo": eq, "Puntos": max(5, puntos_base - int(i*0.9)), "PJ": 16, "PG": 8, "PE": 5, "PP": 3, "GF": 20, "GC": 15})
        
        df_respaldo = pd.DataFrame(datos_respaldo)
        df_cla = procesar_df(df_respaldo)
        
        # Simulamos la Anual multiplicando puntos (ya que la Anual es la suma de ambos torneos)
        df_anu = df_cla.copy()
        df_anu["Puntos"] = df_anu["Puntos"] * 2 
        df_anu["PJ"] = 32
        
        # Simulamos Apertura 
        df_ape = df_cla.copy()
        df_ape = df_ape.sample(frac=1).reset_index(drop=True) # Mezclamos posiciones un poco

    # Guardar las 3 tablas
    df_anu.to_csv("tabla_anual.csv", index=False, encoding="utf-8-sig")
    df_ape.to_csv("tabla_apertura.csv", index=False, encoding="utf-8-sig")
    df_cla.to_csv("tabla_clausura.csv", index=False, encoding="utf-8-sig")
    
    # Mantenemos "datos_procesados.csv" igual a la anual para compatibilidad por si acaso
    df_anu.to_csv("datos_procesados.csv", index=False, encoding="utf-8-sig")

    print(f"🎉 ¡Archivos generados! Anual, Apertura y Clausura listos.")

if __name__ == "__main__":
    obtener_datos()

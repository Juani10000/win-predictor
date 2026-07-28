import os
import pandas as pd
import requests
import random
from datetime import datetime, timedelta

OUT_MATCHES = os.path.join("datos", "matches.csv")
OUT_STANDINGS = "datos_procesados.csv"

os.makedirs("datos", exist_ok=True)


def try_extract_matches_from_wikipedia():
    url_wiki = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_Divisi%C3%B3n_2026_(Argentina)"
    headers = {"User-Agent": "WinPredictorBot/1.0 (https://github.com/Juani10000/win-predictor; actions@github.com)"}
    print(f"🔎 Intentando extraer partidos reales de Wikipedia: {url_wiki}")
    try:
        res = requests.get(url_wiki, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"⚠️ Wikipedia devolvió status {res.status_code}")
            return None
        tables = pd.read_html(res.text)
        candidate_rows = []
        for t in tables:
            cols = [str(c).lower() for c in t.columns]
            # buscamos tablas que tengan dos columnas con nombres parecidos a equipos y una columna con resultado/scores
            if any('local' in c or 'equipo local' in c or 'equipo' in c for c in cols) and any('visitante' in c or 'equipo visitante' in c for c in cols):
                # buscar columna con resultado (contiene '-' o '–' o 'goles')
                score_col = None
                for c in t.columns:
                    s = str(c).lower()
                    if 'resultado' in s or 'res' in s or 'score' in s or 'goles' in s or 'resultado' in s or '-' in str(t.get(c).astype(str).head(10).to_string()):
                        score_col = c
                        break
                # heurística adicional: si tabla tiene 3 columnas aproximadas: Equipo A, Resultado, Equipo B
                if score_col is not None:
                    # identificar columnas de equipo (los que no son score)
                    team_cols = [c for c in t.columns if c != score_col]
                    if len(team_cols) >= 2:
                        left = team_cols[0]
                        right = team_cols[1]
                        # intentar parsear filas
                        for _, r in t.iterrows():
                            left_name = str(r[left]) if pd.notna(r[left]) else ''
                            right_name = str(r[right]) if pd.notna(r[right]) else ''
                            sc = str(r[score_col]) if pd.notna(r[score_col]) else ''
                            # buscar patrón de score como '2–1' o '2-1'
                            import re
                            m = re.search(r"(\d+)\s*[–-]\s*(\d+)", sc)
                            if m and left_name and right_name:
                                gf_local = int(m.group(1))
                                gf_visit = int(m.group(2))
                                fecha = None
                                # si hay columna fecha en la tabla
                                fecha_candidates = [c for c in t.columns if 'fecha' in str(c).lower()]
                                if fecha_candidates:
                                    fecha = r[fecha_candidates[0]]
                                candidate_rows.append({'fecha': fecha, 'Local': left_name.strip(), 'Visitante': right_name.strip(), 'Goles_Local': gf_local, 'Goles_Visitante': gf_visit})
        if candidate_rows:
            df_matches = pd.DataFrame(candidate_rows)
            # normalizar fecha
            if 'fecha' in df_matches.columns:
                try:
                    df_matches['fecha'] = pd.to_datetime(df_matches['fecha'], errors='coerce')
                except Exception:
                    df_matches['fecha'] = pd.NaT
            else:
                df_matches['fecha'] = pd.NaT
            print(f"✅ Encontradas {len(df_matches)} filas de partidos en Wikipedia.")
            return df_matches
        else:
            print("⚠️ No se encontraron tablas de partidos con el patrón esperado en Wikipedia.")
            return None
    except Exception as e:
        print(f"⚠️ Error al obtener/parsear Wikipedia: {e}")
        return None


def generate_synthetic_matches_from_standings(standings_df, rounds=2):
    """
    Genera un historial de partidos sintético (round-robin) basado en la tabla de posiciones.
    Devuelve DataFrame con columnas: fecha, Local, Visitante, Goles_Local, Goles_Visitante, Resultado
    """
    print("🔧 Generando partidos sintéticos (round-robin) a partir de la tabla de posiciones...")
    # normalizar nombres
    df = standings_df.copy()
    rename_map = {}
    for c in df.columns:
        lc = c.lower()
        if 'equipo' in lc:
            rename_map[c] = 'Equipo'
        if 'puntos' in lc or 'pts' in lc:
            rename_map[c] = 'Puntos'
    df = df.rename(columns=rename_map)
    if 'Equipo' not in df.columns:
        raise ValueError("La tabla de posiciones debe contener una columna 'Equipo' (o similar) para generar partidos sintéticos")

    teams = list(df['Equipo'].astype(str).str.strip())
    if not teams:
        raise ValueError("No hay equipos en la tabla de posiciones para generar partidos.")

    # limitar para CI
    if len(teams) > 14:
        teams = teams[:14]

    # generar fechas secuenciales
    start_date = datetime.now() - timedelta(days=90)
    rows = []
    for r in range(rounds):
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                home = teams[i]
                away = teams[j]
                # generar goles basados en ranking (si puntos existen)
                p_home = 0
                p_away = 0
                if 'Puntos' in df.columns:
                    mp = {row['Equipo']: float(row['Puntos']) for _, row in df.iterrows()}
                    p_home = mp.get(home, 0)
                    p_away = mp.get(away, 0)
                # ventaja local + diferencia de puntos
                base_home = max(0.2, (p_home / (p_home + p_away + 1)) * 2.5) if (p_home + p_away) > 0 else 1.0
                base_away = max(0.2, (p_away / (p_home + p_away + 1)) * 2.0) if (p_home + p_away) > 0 else 1.0
                # sample goals as poisson-like with randomness
                gf_home = max(0, int(random.gauss(base_home, 1.0)))
                gf_away = max(0, int(random.gauss(base_away, 1.0)))
                # sometimes reverse home/away for extra round
                if r % 2 == 1:
                    # swap home/away to create second leg
                    rows.append({'fecha': (start_date + timedelta(days=len(rows))).strftime('%Y-%m-%d'), 'Local': away, 'Visitante': home, 'Goles_Local': gf_away, 'Goles_Visitante': gf_home})
                else:
                    rows.append({'fecha': (start_date + timedelta(days=len(rows))).strftime('%Y-%m-%d'), 'Local': home, 'Visitante': away, 'Goles_Local': gf_home, 'Goles_Visitante': gf_away})
    df_matches = pd.DataFrame(rows)
    print(f"✅ Generados {len(df_matches)} partidos sintéticos.")
    return df_matches


def main():
    # 1) Generar/guardar la tabla de posiciones como antes
    print("⏳ Generando tabla de posiciones (standings)...")
    # Intentamos extraer la tabla de posiciones primero
    standings = None
    try:
        url = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_Divisi%C3%B3n_2026_(Argentina)"
        headers = {"User-Agent": "WinPredictorBot/1.0 (https://github.com/Juani10000/win-predictor; actions@github.com)"}
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            try:
                tablas = pd.read_html(r.text, match="Pts.")
                if tablas:
                    t = tablas[0]
                    # selección y renombrado similar al anterior script
                    m = {}
                    for c in t.columns:
                        lc = str(c).lower()
                        if 'equipo' in lc:
                            m[c] = 'Equipo'
                        if 'pts' in lc or 'puntos' in lc:
                            m[c] = 'Puntos'
                        if lc == 'pj': m[c] = 'PJ'
                        if lc == 'pg': m[c] = 'PG'
                        if lc == 'pe': m[c] = 'PE'
                        if lc == 'pp': m[c] = 'PP'
                        if lc == 'gf': m[c] = 'GF'
                        if lc == 'gc': m[c] = 'GC'
                    t = t.rename(columns=m)
                    if 'Equipo' in t.columns:
                        standings = t.copy()
                        print("✅ Tabla de posiciones extraída de Wikipedia.")
            except Exception:
                standings = None
    except Exception as e:
        print(f"⚠️ No pude obtener standings desde Wikipedia: {e}")

    # Si no hay standings, usar respaldo local (como antes)
    if standings is None:
        print("🔄 Usando respaldo interno de standings...")
        equipos = [
            "Independiente Rivadavia", "Argentinos Juniors", "Estudiantes (LP)", "Boca Juniors", "River Plate",
            "Belgrano", "Vélez Sarsfield", "Rosario Central", "Talleres (C)", "Gimnasia (LP)", "Independiente",
            "Lanús", "Huracán", "San Lorenzo", "Unión", "Racing Club", "Instituto", "Barracas Central",
            "Tigre", "Defensa y Justicia", "Sarmiento (J)", "Gimnasia (Mendoza)", "Banfield", "Platense",
            "Central Córdoba (SdE)", "Newell's Old Boys", "Atlético Tucumán", "Deportivo Riestra", "Aldosivi", "Estudiantes (RC)"
        ]
        datos_respaldo = []
        puntos = 34
        for i, eq in enumerate(equipos):
            datos_respaldo.append({"Equipo": eq, "Puntos": max(5, puntos - int(i*0.9)), "PJ": 16, "PG": 8, "PE": 5, "PP": 3, "GF": 20, "GC": 15})
        standings = pd.DataFrame(datos_respaldo)

    # standardize numeric columns
    cols_num = ["Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
    for c in cols_num:
        if c in standings.columns:
            standings[c] = pd.to_numeric(standings[c], errors='coerce').fillna(0).astype(int)
        else:
            standings[c] = 0

    # racha dummy
    opciones = ['G', 'E', 'P']
    standings['Racha'] = [",".join(random.choices(opciones, k=5)) for _ in range(len(standings))]

    standings = standings.sort_values(by='Puntos', ascending=False).reset_index(drop=True)
    # guardar standings para compatibilidad
    try:
        standings.to_csv(OUT_STANDINGS, index=False, encoding='utf-8-sig')
        print(f"📥 Guardado standings en '{OUT_STANDINGS}' ({len(standings)} equipos).")
    except Exception as e:
        print(f"⚠️ No pude guardar standings: {e}")

    # 2) Extraer/Generar partidos reales
    matches = try_extract_matches_from_wikipedia()
    if matches is None:
        try:
            matches = generate_synthetic_matches_from_standings(standings, rounds=2)
        except Exception as e:
            print(f"❌ No pude generar partido sintético: {e}")
            return

    # Normalizar columnas de matches
    # asegurar tipos y nombres
    if 'fecha' in matches.columns:
        try:
            matches['fecha'] = pd.to_datetime(matches['fecha'], errors='coerce')
        except Exception:
            matches['fecha'] = pd.NaT
    else:
        matches['fecha'] = pd.NaT

    # asegurar columnas de goles
    if 'Goles_Local' not in matches.columns and 'Goles_local' in matches.columns:
        matches['Goles_Local'] = matches['Goles_local']
    if 'Goles_Visitante' not in matches.columns and 'Goles_visitante' in matches.columns:
        matches['Goles_Visitante'] = matches['Goles_visitante']

    # rellenar si faltan
    for c in ['Local', 'Visitante', 'Goles_Local', 'Goles_Visitante']:
        if c not in matches.columns:
            matches[c] = '' if c in ['Local','Visitante'] else 0

    # inferir resultado
    def resultado_from_row(r):
        try:
            if int(r['Goles_Local']) > int(r['Goles_Visitante']):
                return 'L'
            elif int(r['Goles_Local']) == int(r['Goles_Visitante']):
                return 'E'
            else:
                return 'V'
        except Exception:
            return 'E'

    matches['Resultado'] = matches.apply(resultado_from_row, axis=1)

    # guardar matches
    try:
        matches.to_csv(OUT_MATCHES, index=False, encoding='utf-8-sig')
        print(f"📥 Guardado historial de partidos en '{OUT_MATCHES}' ({len(matches)} filas).")
    except Exception as e:
        print(f"⚠️ No pude guardar matches: {e}")


if __name__ == '__main__':
    main()

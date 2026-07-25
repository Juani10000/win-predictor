import math
import os
import re
import pandas as pd
import streamlit as st
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime

# =====================================================================
# 1. CONFIGURACIÓN Y CSS ESTILO NEÓN
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background-color: #070b14;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .neon-title {
            font-size: 44px;
            font-weight: 900;
            text-align: left;
            color: #ffffff;
            text-shadow: 0 0 10px #00f3ff, 0 0 20px #00f3ff, 0 0 30px #00f3ff;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .tech-sub {
            text-align: left;
            color: #94a3b8;
            letter-spacing: 2px;
            font-size: 15px;
            margin-bottom: 25px;
        }
        [data-testid="stMetricValue"] {
            color: #00ffcc !important;
            font-size: 36px !important;
            font-weight: 900 !important;
            text-shadow: 0 0 5px #00ffcc80;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 14px !important;
            text-transform: uppercase;
        }
        hr {
            border-top: 1px solid #1e293b;
        }
    </style>
""",
    unsafe_allow_html=True,
)
import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

@st.cache_data(ttl=3600)
def obtener_partidos_hoy_wiki():
    url = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_Divisi%C3%B3n_2026_(Argentina)"
    partidos_hoy = []
    
    # 1. Armamos la fecha de hoy con el formato de Wikipedia (ej: "25 de julio")
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    hoy = datetime.date.today()
    fecha_wiki = f"{hoy.day} de {meses[hoy.month - 1]}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Buscamos todas las filas de las tablas en la página
        filas = soup.find_all('tr')
        
        for fila in filas:
            # Extraemos el texto de cada celda de la fila
            celdas = [td.get_text(strip=True) for td in fila.find_all(['td', 'th'])]
            texto_fila = fila.get_text().lower()
            
            # 3. Si la fila tiene formato de partido (varias columnas) y menciona la fecha de hoy
            if len(celdas) >= 5 and fecha_wiki in texto_fila:
                
                # En Wikipedia el formato suele ser: [0]Local, [1]Resultado, [2]Visitante, [3]Estadio, [4]Fecha, [5]Hora
                local = celdas[0]
                visitante = celdas[2]
                
                # Filtro rápido para asegurarnos de que sean nombres de equipos y no texto basura
                if local and visitante and len(local) > 2:
                    partidos_hoy.append({
                        "Local": local,
                        "Visitante": visitante,
                        "Hora": celdas[-1] if len(celdas) >= 6 else "A conf."
                    })
                    
    except Exception as e:
        st.error(f"Error al intentar leer Wikipedia: {e}")

    # Si por algún motivo no hay partidos o no los encuentra, avisamos
    return partidos_hoy

# ---------------------------------------------------------------------
# FUNCIONES AUXILIARES PARA CÁLCULO DE POISSON (MARCADORES EXACTOS)
# ---------------------------------------------------------------------
def poisson_prob(lmbda, k):
  """Calcula la probabilidad de anotar k goles dado un xG de lmbda."""
  if lmbda <= 0:
    return 1.0 if k == 0 else 0.0
  return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)


def calcular_top_resultados(xg_loc, xg_vis):
  """Calcula la matriz de probabilidades de marcadores exactos (0 a 5 goles)."""
  scores = {}
  total_prob_matriz = 0.0

  for i in range(6):  # Goles local (0 a 5)
    for j in range(6):  # Goles visitante (0 a 5)
      p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
      scores[f"{i} - {j}"] = p * 100
      total_prob_matriz += p * 100

  # Ordenar marcadores de mayor a menor probabilidad
  sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
  top_5 = sorted_scores[:5]

  prob_top_5 = sum(p for _, p in top_5)
  prob_otro = max(0.0, 100.0 - prob_top_5)

  return top_5, prob_otro


# ---------------------------------------------------------------------
# ENCABEZADO CON LOGO
# ---------------------------------------------------------------------
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
  url_lpf = (
      "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
  )
  st.image(url_lpf, width=110)

with col_titulo:
  st.markdown(
      '<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True
  )
  st.markdown(
      '<div class="tech-sub">MOTOR DE PREDICCIÓN CON xG Y RESULTADOS'
      " EXACTOS</div>",
      unsafe_allow_html=True,
  )

st.markdown("---")

# =====================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS CON xG
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
  RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
  df = pd.read_csv(RUTA_CSV)

  if "Equipo" in df.columns:
    df["Equipo"] = (
        df["Equipo"]
        .astype(str)
        .apply(lambda x: re.sub(r"\[.*?\]|\(.*?\)", "", x).strip())
    )

  # Garantizar columna xG
  if "xG" not in df.columns and "xG_Favor" not in df.columns:
    if "GF" in df.columns and "PJ" in df.columns:
      df["xG"] = (df["GF"] / df["PJ"].replace(0, 1) * 0.95).round(2)
    else:
      df["xG"] = 1.25
  elif "xG_Favor" in df.columns and "xG" not in df.columns:
    df["xG"] = df["xG_Favor"]

  # -----------------------------------------------------------------
  # 3. TABLA DE POSICIONES SIEMPRE VISIBLE
  # -----------------------------------------------------------------
  st.markdown(
      "<h3 style='color: #cbd5e1;'>Tabla General de Posiciones & xG</h3>",
      unsafe_allow_html=True,
  )
  st.dataframe(df, use_container_width=True, hide_index=True)
  st.markdown("---")

  # -----------------------------------------------------------------
  # 4. MOTOR DE PREDICCIÓN CON xG Y TOP 5 MARCADORES
  # -----------------------------------------------------------------
  st.markdown(
      "<h3 style='color: #cbd5e1;'>Motor de Predicción de Partidos</h3>",
      unsafe_allow_html=True,
  )

  lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

  if len(lista_equipos) >= 2:
    col1, col2 = st.columns(2)
    with col1:
      local = st.selectbox("Seleccionar Local", lista_equipos, index=0)
    with col2:
      visitante = st.selectbox(
          "Seleccionar Visitante",
          lista_equipos,
          index=min(1, len(lista_equipos) - 1),
      )

    if local == visitante:
      st.error("SISTEMA BLOQUEADO: Seleccione escuadras diferentes.")
    else:
      row_loc = df[df["Equipo"] == local].iloc[0]
      row_vis = df[df["Equipo"] == visitante].iloc[0]

      pts_loc = (
          float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
      )
      pts_vis = (
          float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
      )
      pj_loc = (
          max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
      )
      pj_vis = (
          max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
      )

      xg_loc_base = float(row_loc.get("xG", 1.25))
      xg_vis_base = float(row_vis.get("xG", 1.10))

      # xG Proyectado para el partido (+10% ventaja de localia)
      xg_proyectado_local = round(xg_loc_base * 1.10, 2)
      xg_proyectado_visi = round(xg_vis_base * 0.95, 2)

      # Promedio ponderado (Puntos + xG)
      prom_loc = ((pts_loc / pj_loc) * 0.6) + (xg_proyectado_local * 0.4)
      prom_vis = ((pts_vis / pj_vis) * 0.6) + (xg_proyectado_visi * 0.4)

      diferencia = abs(prom_loc - prom_vis)
      prob_empate = max(18.0, min(33.0, 28.5 - (diferencia * 6.0)))

      resto = 100.0 - prob_empate
      total_prom = prom_loc + prom_vis

      if total_prom > 0:
        prob_loc = (prom_loc / total_prom) * resto
        prob_vis = (prom_vis / total_prom) * resto
      else:
        prob_loc = resto / 2
        prob_vis = resto / 2

      st.markdown(
          f"<h2 style='text-align: center; color: #fff; margin-top:"
          f" 25px;'>{local.upper()} vs {visitante.upper()}</h2>",
          unsafe_allow_html=True,
      )

      # Bloque de xG Proyectado
      col_xg1, col_xg2 = st.columns(2)
      with col_xg1:
        st.info(f"xG Proyectado {local}: **{xg_proyectado_local}**")
      with col_xg2:
        st.info(f"xG Proyectado {visitante}: **{xg_proyectado_visi}**")

      # Métricas de 1X2
      m1, m2, m3 = st.columns(3)
      m1.metric(label=f"Victoria {local}", value=f"{prob_loc:.1f}%")
      m2.metric(label="Probabilidad Empate", value=f"{prob_empate:.1f}%")
      m3.metric(label=f"Victoria {visitante}", value=f"{prob_vis:.1f}%")

      # Barras visuales
      st.markdown(
          "<br><p style='color: #94a3b8;'>Distribución de probabilidad"
          " 1X2:</p>",
          unsafe_allow_html=True,
      )
      c_b1, c_b2, c_b3 = st.columns(3)
      with c_b1:
        st.markdown(
            "<p style='color: #00ffcc;'>Local</p>", unsafe_allow_html=True
        )
        st.progress(int(prob_loc) / 100)
      with c_b2:
        st.markdown(
            "<p style='color: #cbd5e1;'>Empate</p>", unsafe_allow_html=True
        )
        st.progress(int(prob_empate) / 100)
      with c_b3:
        st.markdown(
            "<p style='color: #ff3366;'>Visitante</p>", unsafe_allow_html=True
        )
        st.progress(int(prob_vis) / 100)

      st.markdown("---")

      # -----------------------------------------------------------------
      # 5. TOP 5 RESULTADOS MÁS PROBABLES (CÁLCULO POISSON)
      # -----------------------------------------------------------------
      st.markdown(
          "<h4 style='color: #cbd5e1;'>Top 5 Marcadores Exactos Más"
          " Probables</h4>",
          unsafe_allow_html=True,
      )

      top_5_marcadores, prob_otro = calcular_top_resultados(
          xg_proyectado_local, xg_proyectado_visi
      )

      # Formatear datos para la tabla de marcadores
      tabla_marcadores = []
      for rank, (marcador, prob) in enumerate(top_5_marcadores, 1):
        tabla_marcadores.append({
            "Ranking": f"#{rank}",
            "Resultado Exacto (Local - Visitante)": marcador,
            "Probabilidad": f"{prob:.1f}%",
        })

      tabla_marcadores.append({
          "Ranking": "Otros",
          "Resultado Exacto (Local - Visitante)": "Cualquier otro resultado",
          "Probabilidad": f"{prob_otro:.1f}%",
      })

      df_marcadores = pd.DataFrame(tabla_marcadores)
      st.dataframe(df_marcadores, use_container_width=True, hide_index=True)

else:
  st.error(
      "Archivo de origen no encontrado. Verifique que 'datos_procesados.csv'"
      " exista."
  )
    

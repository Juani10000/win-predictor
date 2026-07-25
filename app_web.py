import math
import os
import re
import pandas as pd
import streamlit as st


# =====================================================================
# 1. FUNCIONES AUXILIARES DE CÁLCULO
# =====================================================================
def poisson_prob(lmbda, k):
  if lmbda <= 0:
    return 1.0 if k == 0 else 0.0
  return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)


def calcular_top_resultados(xg_loc, xg_vis):
  scores = {}
  for i in range(6):
    for j in range(6):
      p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
      scores[f'{i} - {j}'] = p * 100

  sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
  top_5 = sorted_scores[:5]
  prob_top_5 = sum(p for _, p in top_5)
  prob_otro = max(0.0, 100.0 - prob_top_5)

  return top_5, prob_otro


def obtener_datos_demo():
  """Genera datos de respaldo si no encuentra el archivo CSV."""
  equipos = [
      'Boca Juniors',
      'River Plate',
      'Racing Club',
      'Independiente',
      'San Lorenzo',
      'Vélez Sarsfield',
      'Estudiantes LP',
      'Talleres',
      'Rosario Central',
      'Newell\'s',
  ]
  data = {
      'Equipo': equipos,
      'PJ': [14] * 10,
      'Puntos': [28, 27, 24, 22, 21, 20, 19, 18, 16, 14],
      'GF': [22, 25, 20, 18, 15, 17, 16, 14, 12, 10],
      'xG': [1.65, 1.80, 1.45, 1.30, 1.20, 1.25, 1.15, 1.10, 0.95, 0.85],
  }
  return pd.DataFrame(data)


# =====================================================================
# 2. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# =====================================================================
st.set_page_config(page_title='Win Predictor | LPF', layout='wide')

st.markdown(
    """
    <style>
        .stApp {
            background-color: #070b19;
            color: #f1f5f9;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        .hero-title {
            font-size: 38px;
            font-weight: 900;
            letter-spacing: -0.5px;
            margin-bottom: 2px;
            background: linear-gradient(90deg, #ffffff 0%, #00f3ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
        }
        .hero-subtitle {
            color: #64748b;
            letter-spacing: 2px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 20px;
        }
        .section-header {
            font-size: 18px;
            font-weight: 700;
            color: #38bdf8;
            letter-spacing: 0.5px;
            border-left: 3px solid #00f3ff;
            padding-left: 12px;
            margin-top: 25px;
            margin-bottom: 18px;
            text-transform: uppercase;
        }
        .match-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            border: 1px solid #312e81;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-top: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
        }
        .match-title {
            font-size: 26px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .stat-card {
            background-color: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }
        .stat-label {
            font-size: 11px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .stat-value { font-size: 30px; font-weight: 900; color: #00ffcc; }
        .stat-value-alt { font-size: 30px; font-weight: 900; color: #ff3366; }
        .stat-value-draw { font-size: 30px; font-weight: 900; color: #cbd5e1; }

        div[data-baseweb="select"] > div {
            background-color: #0f172a !important;
            border-color: #334155 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
        }
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            background-color: #0f172a;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #1e293b;
        }
        .custom-table th {
            background-color: #1e293b;
            color: #94a3b8;
            padding: 12px 16px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .custom-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #1e293b;
            color: #e2e8f0;
            font-size: 14px;
        }
        .rank-top { color: #00f3ff; font-weight: bold; }
        hr {
            border: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #1e293b, transparent);
            margin: 25px 0;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# 3. CARGA DE DATOS ROBUSTA
# =====================================================================
df = None
directorio_actual = os.path.dirname(os.path.abspath(__file__))

rutas_a_probar = [
    os.path.join(directorio_actual, 'datos_procesados.csv'),
    os.path.join(directorio_actual, 'datos', 'datos_procesados.csv'),
    'datos_procesados.csv',
]

# Intentar cargar desde las rutas locales
for ruta in rutas_a_probar:
  if os.path.exists(ruta):
    try:
      df = pd.read_csv(ruta)
      break
    except Exception:
      pass

# Permite también subir el CSV manualmente desde la barra lateral si no se encontró
with st.sidebar:
  st.header('Configuración')
  uploaded_file = st.file_uploader('Cargar datos_procesados.csv', type=['csv'])
  if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

# Si todo lo anterior falla, usa datos de respaldo
if df is None:
  st.warning(
      "⚠️ No se encontró 'datos_procesados.csv'. Mostrando datos de prueba."
      ' Podés cargar tu CSV desde el menú lateral.'
  )
  df = obtener_datos_demo()

# Limpieza de nombres de equipos
if 'Equipo' in df.columns:
  df['Equipo'] = (
      df['Equipo']
      .astype(str)
      .apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
  )

if 'xG' not in df.columns and 'xG_Favor' not in df.columns:
  if 'GF' in df.columns and 'PJ' in df.columns:
    df['xG'] = (df['GF'] / df['PJ'].replace(0, 1) * 0.95).round(2)
  else:
    df['xG'] = 1.25
elif 'xG_Favor' in df.columns and 'xG' not in df.columns:
  df['xG'] = df['xG_Favor']

# =====================================================================
# 4. INTERFAZ GRÁFICA
# =====================================================================
col_logo, col_titulo = st.columns([1, 7])
with col_logo:
  url_lpf = (
      'https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png'
  )
  st.image(url_lpf, width=90)

with col_titulo:
  st.markdown(
      '<div class="hero-title">WIN PREDICTOR LPF</div>', unsafe_allow_html=True
  )
  st.markdown(
      '<div class="hero-subtitle">MODELO ANALÍTICO DE EXPECTED GOALS Y MATRIZ'
      ' DE PROBABILIDAD</div>',
      unsafe_allow_html=True,
  )

st.markdown('<hr>', unsafe_allow_html=True)

# TABLA DE POSICIONES
st.markdown(
    '<div class="section-header">TABLA GENERAL DE POSICIONES Y METRICAS DE'
    ' XG</div>',
    unsafe_allow_html=True,
)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown('<hr>', unsafe_allow_html=True)

# PREDICTOR DE PARTIDOS
st.markdown(
    '<div class="section-header">CONFIGURACIÓN DEL ENFRENTAMIENTO</div>',
    unsafe_allow_html=True,
)

lista_equipos = sorted(df['Equipo'].unique()) if 'Equipo' in df.columns else []

if len(lista_equipos) >= 2:
  col1, col2 = st.columns(2)
  with col1:
    local = st.selectbox('Equipo Local', lista_equipos, index=0)
  with col2:
    visitante = st.selectbox(
        'Equipo Visitante', lista_equipos, index=min(1, len(lista_equipos) - 1)
    )

  if local == visitante:
    st.error('Selección inválida: Elija dos equipos diferentes.')
  else:
    row_loc = df[df['Equipo'] == local].iloc[0]
    row_vis = df[df['Equipo'] == visitante].iloc[0]

    pts_loc = float(row_loc.get('Puntos', 0)) if 'Puntos' in df.columns else 0.0
    pts_vis = float(row_vis.get('Puntos', 0)) if 'Puntos' in df.columns else 0.0
    pj_loc = (
        max(float(row_loc.get('PJ', 1)), 1.0) if 'PJ' in df.columns else 1.0
    )
    pj_vis = (
        max(float(row_vis.get('PJ', 1)), 1.0) if 'PJ' in df.columns else 1.0
    )

    xg_loc_base = float(row_loc.get('xG', 1.25))
    xg_vis_base = float(row_vis.get('xG', 1.10))

    xg_proyectado_local = round(xg_loc_base * 1.10, 2)
    xg_proyectado_visi = round(xg_vis_base * 0.95, 2)

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
        f"""
            <div class="match-banner">
                <div class="match-title">{local} vs {visitante}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_xg1, col_xg2 = st.columns(2)
    with col_xg1:
      st.markdown(
          f"""
                <div class="stat-card">
                    <div class="stat-label">xG Proyectado Local ({local})</div>
                    <div style="font-size: 24px; font-weight: 800; color: #00f3ff;">{xg_proyectado_local}</div>
                </div>
            """,
          unsafe_allow_html=True,
      )
    with col_xg2:
      st.markdown(
          f"""
                <div class="stat-card">
                    <div class="stat-label">xG Proyectado Visitante ({visitante})</div>
                    <div style="font-size: 24px; font-weight: 800; color: #00f3ff;">{xg_proyectado_visi}</div>
                </div>
            """,
          unsafe_allow_html=True,
      )

    st.markdown('<br>', unsafe_allow_html=True)

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
      st.markdown(
          f"""
                <div class="stat-card">
                    <div class="stat-label">Victoria {local}</div>
                    <div class="stat-value">{prob_loc:.1f}%</div>
                </div>
            """,
          unsafe_allow_html=True,
      )
    with c_m2:
      st.markdown(
          f"""
                <div class="stat-card">
                    <div class="stat-label">Probabilidad de Empate</div>
                    <div class="stat-value-draw">{prob_empate:.1f}%</div>
                </div>
            """,
          unsafe_allow_html=True,
      )
    with c_m3:
      st.markdown(
          f"""
                <div class="stat-card">
                    <div class="stat-label">Victoria {visitante}</div>
                    <div class="stat-value-alt">{prob_vis:.1f}%</div>
                </div>
            """,
          unsafe_allow_html=True,
      )

    st.markdown('<br>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
      st.progress(int(prob_loc) / 100)
    with b2:
      st.progress(int(prob_empate) / 100)
    with b3:
      st.progress(int(prob_vis) / 100)

    st.markdown('<hr>', unsafe_allow_html=True)

    # TOP MARCADORES
    st.markdown(
        '<div class="section-header">TOP 5 MARCADORES EXACTOS MÁS'
        ' PROBABLES</div>',
        unsafe_allow_html=True,
    )

    top_5_marcadores, prob_otro = calcular_top_resultados(
        xg_proyectado_local, xg_proyectado_visi
    )

    rows_html = ''
    for rank, (marcador, prob) in enumerate(top_5_marcadores, 1):
      rank_class = 'rank-top' if rank == 1 else ''
      rows_html += f"""
                <tr>
                    <td class="{rank_class}">#{rank}</td>
                    <td style="font-weight: 600;">{marcador}</td>
                    <td style="font-weight: 700; color: #00ffcc;">{prob:.1f}%</td>
                </tr>
            """

    rows_html += f"""
            <tr>
                <td style="color: #64748b;">Otros</td>
                <td style="color: #94a3b8;">Cualquier otro marcador</td>
                <td style="font-weight: 700; color: #94a3b8;">{prob_otro:.1f}%</td>
            </tr>
        """

    table_html = f"""
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Ranking</th>
                        <th>Resultado Exacto (Local - Visitante)</th>
                        <th>Probabilidad Calculada</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        """
    st.markdown(table_html, unsafe_allow_html=True)

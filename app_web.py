import datetime
import math
import os
import re
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# =====================================================================
# 1. CONFIGURACIÓN Y CSS ESTILO GLASSMORPHISM / MODERNO
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        /* Título Principal */
        .neon-title {
            font-size: 42px;
            font-weight: 800;
            text-align: left;
            color: #ffffff;
            letter-spacing: -0.5px;
            margin-bottom: 2px;
        }
        .tech-sub {
            text-align: left;
            color: #64748b;
            letter-spacing: 1.5px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 25px;
            text-transform: uppercase;
        }
        
        /* Métricas */
        [data-testid="stMetricValue"] {
            color: #38bdf8 !important;
            font-size: 32px !important;
            font-weight: 800 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 13px !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* --- STYLING TABLA DE POSICIONES GLASSMORPHISM --- */
        .glass-card {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        }

        .custom-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 6px;
            font-size: 14px;
        }

        .custom-table th {
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 1px;
            padding: 12px 16px;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .custom-table th:first-child, .custom-table td:first-child {
            text-align: left;
        }

        .custom-table tbody tr {
            background: rgba(30, 41, 59, 0.4);
            transition: all 0.2s ease;
        }

        .custom-table tbody tr:hover {
            background: rgba(51, 65, 85, 0.6);
            transform: translateY(-1px);
        }

        .custom-table td {
            padding: 12px 16px;
            text-align: center;
            color: #cbd5e1;
            border-top: 1px solid rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .custom-table td:first-child {
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
            border-left: 1px solid rgba(255, 255, 255, 0.03);
            font-weight: 700;
            color: #f8fafc;
        }

        .custom-table td:last-child {
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            border-right: 1px solid rgba(255, 255, 255, 0.03);
        }

        .pos-badge {
            display: inline-block;
            width: 24px;
            height: 24px;
            line-height: 24px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.05);
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
            color: #94a3b8;
        }

        .pos-top {
            background: rgba(56, 189, 248, 0.2);
            color: #38bdf8;
        }

        .xg-pill {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
        }

        .form-dot {
            height: 8px;
            width: 8px;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
        }
        .dot-w { background-color: #10b981; }
        .dot-d { background-color: #f59e0b; }
        .dot-l { background-color: #ef4444; }

        hr { border-top: 1px solid #1e293b; }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# FUNCIONES AUXILIARES Y MATEMÁTICAS
# ---------------------------------------------------------------------
def calcular_peso_temporal(dias_transcurridos, half_life=30.0):
    lmbda = np.log(2) / half_life
    return float(np.exp(-lmbda * dias_transcurridos))


def poisson_prob(lmbda, k):
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)


def simular_monte_carlo(xg_loc, xg_vis, num_simulaciones=10000):
    xg_loc_sim = np.random.normal(xg_loc, xg_loc * 0.10, num_simulaciones)
    xg_vis_sim = np.random.normal(xg_vis, xg_vis * 0.10, num_simulaciones)

    xg_loc_sim = np.maximum(0.05, xg_loc_sim)
    xg_vis_sim = np.maximum(0.05, xg_vis_sim)

    goles_loc = np.random.poisson(xg_loc_sim)
    goles_vis = np.random.poisson(xg_vis_sim)

    victorias_loc = np.sum(goles_loc > goles_vis)
    empates = np.sum(goles_loc == goles_vis)
    victorias_vis = np.sum(goles_vis > goles_loc)

    prob_loc_mc = (victorias_loc / num_simulaciones) * 100
    prob_emp_mc = (empates / num_simulaciones) * 100
    prob_vis_mc = (victorias_vis / num_simulaciones) * 100

    goles_totales = goles_loc + goles_vis

    return prob_loc_mc, prob_emp_mc, prob_vis_mc, goles_totales


def calcular_top_resultados(xg_loc, xg_vis):
    scores = {}
    for i in range(6):
        for j in range(6):
            p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
            scores[f"{i} - {j}"] = p * 100

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_scores[:5]
    prob_top_5 = sum(p for _, p in top_5)
    prob_otro = max(0.0, 100.0 - prob_top_5)

    return top_5, prob_otro


def calcular_mercados_adicionales(xg_loc, xg_vis):
    prob_under_2_5 = 0.0
    prob_btts = 0.0

    for i in range(7):
        for j in range(7):
            p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
            if (i + j) < 2.5:
                prob_under_2_5 += p
            if i > 0 and j > 0:
                prob_btts += p

    prob_over_2_5 = (1.0 - prob_under_2_5) * 100
    prob_under_2_5 *= 100
    prob_btts *= 100

    return prob_over_2_5, prob_under_2_5, prob_btts


def realizar_prediccion(
    local,
    visitante,
    df,
    stats_loc,
    stats_vis,
    xg_proyectado_local,
    xg_proyectado_visi,
    factor_localia=0.15,
):
    row_loc = df[df["Equipo"] == local].iloc[0]
    row_vis = df[df["Equipo"] == visitante].iloc[0]

    pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
    pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
    pj_loc = (
        max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
    )
    pj_vis = (
        max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
    )

    prom_loc = ((pts_loc / pj_loc) * 0.4) + (xg_proyectado_local * 0.4)
    prom_vis = ((pts_vis / pj_vis) * 0.4) + (xg_proyectado_visi * 0.4)

    dias_ultimo_partido_loc = float(row_loc.get("Dias_Ultimo_Partido", 7.0))
    dias_ultimo_partido_vis = float(row_vis.get("Dias_Ultimo_Partido", 7.0))

    peso_decay_loc = calcular_peso_temporal(
        dias_ultimo_partido_loc, half_life=45.0
    )
    peso_decay_vis = calcular_peso_temporal(
        dias_ultimo_partido_vis, half_life=45.0
    )

    pts_u5_loc = float(stats_loc.get("Pts_U5", 7.5)) * peso_decay_loc
    pts_u5_vis = float(stats_vis.get("Pts_U5", 7.5)) * peso_decay_vis

    factor_forma_loc = 0.85 + (pts_u5_loc / 15.0) * 0.30
    factor_forma_vis = 0.85 + (pts_u5_vis / 15.0) * 0.30

    prom_loc *= factor_forma_loc
    prom_vis *= factor_forma_vis

    prom_loc_ajustado = prom_loc * (1.0 + (factor_localia * 0.5))
    prom_vis_ajustado = prom_vis

    score_loc = (
        (stats_loc["GF"] * 0.2)
        + (stats_loc["Pos"] * 0.05)
        + (stats_loc["VI"] * 1.2)
        + (stats_loc["TirosArco"] * 0.8)
        + (stats_loc["Fortaleza"] * 0.1)
    )
    score_vis = (
        (stats_vis["GF"] * 0.2)
        + (stats_vis["Pos"] * 0.05)
        + (stats_vis["VI"] * 1.2)
        + (stats_vis["TirosArco"] * 0.8)
        + (stats_vis["Fortaleza"] * 0.1)
    )

    ventaja_relativa = (
        (score_loc - score_vis) / (score_loc + score_vis)
        if (score_loc + score_vis) > 0
        else 0.0
    )
    ajuste_h2h = ventaja_relativa * 0.08

    prom_loc_ajustado *= 1.0 + ajuste_h2h
    prom_vis_ajustado *= 1.0 - ajuste_h2h

    prob_empate_poisson = sum(
        poisson_prob(xg_proyectado_local, k)
        * poisson_prob(xg_proyectado_visi, k)
        for k in range(5)
    )

    diferencia_xg = abs(xg_proyectado_local - xg_proyectado_visi)
    factor_paridad = max(0.85, 1.25 - (diferencia_xg * 0.4))

    prob_empate = (prob_empate_poisson * 100) * factor_paridad
    prob_empate = max(22.0, min(38.0, prob_empate))

    resto = 100.0 - prob_empate
    total_prom = prom_loc_ajustado + prom_vis_ajustado

    if total_prom > 0:
        prob_loc = (prom_loc_ajustado / total_prom) * resto
        prob_vis = (prom_vis_ajustado / total_prom) * resto
    else:
        prob_loc = resto / 2
        prob_vis = resto / 2

    return prob_loc, prob_empate, prob_vis


def buscar_equipo(nombre_buscado, lista_equipos):
    nombre_clean = nombre_buscado.lower().strip()
    if "estudiantes" in nombre_clean:
        if any(
            k in nombre_clean for k in ["rio cuarto", "río cuarto", "rc"]
        ):
            for eq in lista_equipos:
                if "rc" in eq.lower() or "rio cuarto" in eq.lower():
                    return eq
        elif "la plata" in nombre_clean or "lp" in nombre_clean.split():
            for eq in lista_equipos:
                if "estudiantes" in eq.lower() and "rc" not in eq.lower():
                    return eq

    for eq in lista_equipos:
        if nombre_clean == eq.lower().strip():
            return eq
    for eq in lista_equipos:
        if nombre_clean in eq.lower() or eq.lower() in nombre_clean:
            return eq
    return None


@st.cache_data(ttl=3600)
def obtener_partidos_hoy_auto(equipos_disponibles):
    ahora_arg = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    fecha_hoy_str = ahora_arg.strftime("%Y-%m-%d")
    fecha_espn_url = ahora_arg.strftime("%Y%m%d")

    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates={fecha_espn_url}"
    partidos_hoy = []

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "events" in data:
            for event in data["events"]:
                fecha_api = datetime.datetime.strptime(
                    event["date"], "%Y-%m-%dT%H:%MZ"
                )
                fecha_partido_arg = fecha_api - datetime.timedelta(hours=3)

                if fecha_partido_arg.strftime("%Y-%m-%d") == fecha_hoy_str:
                    comps = event["competitions"][0]["competitors"]
                    loc_raw = (
                        comps[0]["team"]["name"]
                        if comps[0]["homeAway"] == "home"
                        else comps[1]["team"]["name"]
                    )
                    vis_raw = (
                        comps[1]["team"]["name"]
                        if comps[0]["homeAway"] == "home"
                        else comps[0]["team"]["name"]
                    )
                    loc_match = buscar_equipo(loc_raw, equipos_disponibles)
                    vis_match = buscar_equipo(vis_raw, equipos_disponibles)

                    if loc_match and vis_match and loc_match != vis_match:
                        partidos_hoy.append(
                            {
                                "Local": loc_match,
                                "Visitante": vis_match,
                                "Hora": fecha_partido_arg.strftime("%H:%M"),
                            }
                        )
    except Exception:
        pass
    return partidos_hoy


@st.cache_data(ttl=3600)
def obtener_estadisticas_wiki(equipos_disponibles):
    url = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_Divisi%C3%B3n_2026_(Argentina)"
    stats_wiki = {}
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tablas = soup.find_all("table", {"class": "wikitable"})
        for tabla in tablas:
            filas = tabla.find_all("tr")
            if len(filas) > 15:
                for fila in filas[1:]:
                    celdas = [
                        td.get_text(strip=True)
                        for td in fila.find_all(["td", "th"])
                    ]
                    if len(celdas) >= 8:
                        eq_match = buscar_equipo(celdas[1], equipos_disponibles)
                        if eq_match:
                            stats_wiki[eq_match] = {
                                "GF": int(celdas[6])
                                if celdas[6].isdigit()
                                else 0,
                                "GC": int(celdas[7])
                                if celdas[7].isdigit()
                                else 0,
                                "PJ": int(celdas[2])
                                if celdas[2].isdigit()
                                else 1,
                            }
    except Exception:
        pass
    return stats_wiki


def consolidar_estadisticas(equipo, df, stats_wiki, xg_proyectado):
    row = df[df["Equipo"] == equipo].iloc[0]
    if equipo in stats_wiki:
        gf = stats_wiki[equipo]["GF"]
        pj = max(1, stats_wiki[equipo]["PJ"])
        gc = stats_wiki[equipo]["GC"]
    else:
        gf = int(row.get("GF", round(xg_proyectado * 12)))
        pj = int(row.get("PJ", 12))
        gc = int(row.get("GC", 12))
        if pj == 0:
            pj = 1

    pos = min(75, max(35, int(40 + (gf / pj * 8) + (xg_proyectado * 3))))
    vi = int(max(0, pj - int(gc * 0.8)) * 0.4)
    tiros_arco = round(xg_proyectado * 3.5 + (gf / pj * 1.5), 1)
    pases = min(92, max(60, int(pos * 1.15 + 8)))
    corners = round(
        float(row.get("Corners", 4.2))
        if "Corners" in df.columns
        else max(3.0, min(5.8, 2.2 + (xg_proyectado * 1.1) + (pos * 0.02))),
        1,
    )
    fortaleza = min(100, max(10, int(100 - ((gc / pj) * 35))))
    pts_u5 = float(
        row.get(
            "Forma_U5",
            round(min(15.0, max(1.0, (gf / pj) * 3.5 + (xg_proyectado * 2.0))), 1),
        )
    )

    dias_ultimo_partido = float(row.get("Dias_Ultimo_Partido", 7.0))
    peso_temporal = calcular_peso_temporal(dias_ultimo_partido, half_life=30.0)
    xg_ajustado = round(xg_proyectado * (0.85 + (0.15 * peso_temporal)), 2)

    return {
        "GF": gf,
        "xG": xg_ajustado,
        "Pos": pos,
        "VI": vi,
        "TirosArco": tiros_arco,
        "Pases": pases,
        "Corners": corners,
        "Fortaleza": fortaleza,
        "Pts_U5": pts_u5,
        "Peso_Temporal": round(peso_temporal, 2),
    }


def generar_radar(loc_name, vis_name, stats_loc, stats_vis):
    categories = [
        "Goles a Favor",
        "xG Proyectado",
        "Posesión (%)",
        "Vallas Invictas",
        "Tiros al Arco",
        "Eficacia Pases",
        "Fuerza Defensiva",
        "Forma Reciente",
    ]
    max_gf = max(stats_loc["GF"], stats_vis["GF"], 15) * 1.1
    max_xg = max(stats_loc["xG"], stats_vis["xG"], 2.0) * 1.2

    val_loc_norm = [
        stats_loc["GF"] / max_gf,
        stats_loc["xG"] / max_xg,
        stats_loc["Pos"] / 100,
        stats_loc["VI"] / 10,
        stats_loc["TirosArco"] / 10,
        stats_loc["Pases"] / 100,
        stats_loc["Fortaleza"] / 100,
        stats_loc["Pts_U5"] / 15,
    ]
    val_vis_norm = [
        stats_vis["GF"] / max_gf,
        stats_vis["xG"] / max_xg,
        stats_vis["Pos"] / 100,
        stats_vis["VI"] / 10,
        stats_vis["TirosArco"] / 10,
        stats_vis["Pases"] / 100,
        stats_vis["Fortaleza"] / 100,
        stats_vis["Pts_U5"] / 15,
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=val_loc_norm + [val_loc_norm[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=loc_name,
            line=dict(color="#38bdf8"),
            fillcolor="rgba(56, 189, 248, 0.15)",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=val_vis_norm + [val_vis_norm[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=vis_name,
            line=dict(color="#f43f5e"),
            fillcolor="rgba(244, 63, 94, 0.15)",
        )
    )

    fig.update_layout(
        polar=dict(
            bgcolor="#111827",
            radialaxis=dict(visible=False, range=[0, 1]),
            angularaxis=dict(color="#64748b", gridcolor="#1e293b"),
        ),
        showlegend=True,
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        font=dict(color="#94a3b8"),
        margin=dict(t=30, b=30, l=40, r=40),
    )
    return fig


# ---------------------------------------------------------------------
# NUEVA RENDERIZACIÓN DE TABLA PERSONALIZADA
# ---------------------------------------------------------------------
def renderizar_tabla_glassmorphism(df_input):
    df_display = df_input.copy()

    # Generar columnas estéticas
    if "Puntos" not in df_display.columns:
        df_display["Puntos"] = np.random.randint(12, 30, len(df_display))
    if "PJ" not in df_display.columns:
        df_display["PJ"] = 12

    df_display = df_display.sort_values(
        by=["Puntos", "xG"], ascending=[False, False]
    ).reset_index(drop=True)

    rows_html = ""
    for idx, row in df_display.iterrows():
        pos = idx + 1
        badge_class = "pos-badge pos-top" if pos <= 4 else "pos-badge"

        # Simulación de Dots de Forma Reciente
        dots_html = '<span class="form-dot dot-w"></span><span class="form-dot dot-w"></span><span class="form-dot dot-d"></span><span class="form-dot dot-w"></span><span class="form-dot dot-l"></span>'

        rows_html += f"""
        <tr>
            <td><span class="{badge_class}">{pos}</span>{row['Equipo']}</td>
            <td>{row.get('PJ', 12)}</td>
            <td><strong>{row.get('Puntos', 0)}</strong></td>
            <td><span class="xg-pill">{row.get('xG', 1.25):.2f}</span></td>
            <td>{row.get('GF', '-')}</td>
            <td>{row.get('GC', '-')}</td>
            <td>{dots_html}</td>
        </tr>
        """

    table_html = f"""
    <div class="glass-card">
        <table class="custom-table">
            <thead>
                <tr>
                    <th>Club</th>
                    <th>PJ</th>
                    <th>PTS</th>
                    <th>xG Prom.</th>
                    <th>GF</th>
                    <th>GC</th>
                    <th>Forma (U5)</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    return table_html


# =====================================================================
# INTERFAZ DE USUARIO
# =====================================================================
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image(
        "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png",
        width=90,
    )

with col_titulo:
    st.markdown(
        '<div class="neon-title">Win Predictor LPF</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tech-sub">Plataforma Analítica & Proyecciones Estocásticas</div>',
        unsafe_allow_html=True,
    )

DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")
if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)

    if "Equipo" in df.columns:

        def limpiar_nombre_equipo(x):
            s = str(x).strip()
            s_lower = s.lower()
            if "estudiantes" in s_lower:
                if any(
                    k in s_lower
                    for k in ["rio cuarto", "río cuarto", "(rc)", "estudiantes rc"]
                ):
                    return "Estudiantes RC"
                if any(k in s_lower for k in ["la plata", "(lp)"]):
                    return "Estudiantes"
            return re.sub(r"\[.*?\]|\(.*?\)", "", s).strip()

        df["Equipo"] = df["Equipo"].apply(limpiar_nombre_equipo)

    if "xG" not in df.columns:
        df["xG"] = (
            df["xG_Favor"] if "xG_Favor" in df.columns else 1.25
        )

    lista_equipos = (
        sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []
    )
    stats_wikipedia = obtener_estadisticas_wiki(lista_equipos)

    # AGENDA DE HOY
    partidos_del_dia = obtener_partidos_hoy_auto(lista_equipos)
    if partidos_del_dia:
        st.markdown(
            "<h4 style='color: #cbd5e1;'>Partidos Programados Hoy</h4>",
            unsafe_allow_html=True,
        )
        for partido in partidos_del_dia:
            st.caption(
                f"⚽ **{partido['Hora']} hs** | **{partido['Local']}** vs"
                f" **{partido['Visitante']}**"
            )
        st.divider()

    # NUEVA TABLA CON EFECTO GLASSMORPHISM
    st.markdown(
        "<h3 style='color: #f8fafc; font-weight: 700;'>Posiciones General & Performance xG</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        renderizar_tabla_glassmorphism(df), unsafe_allow_html=True
    )

    # SECTOR PREDICCIONES
    st.markdown(
        "<h3 style='color: #f8fafc; font-weight: 700;'>Simulador de Encuentros</h3>",
        unsafe_allow_html=True,
    )

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox(
                "Seleccionar Equipo Local",
                lista_equipos,
                index=0,
                key="sb_local",
            )
        with col2:
            visitante = st.selectbox(
                "Seleccionar Equipo Visitante",
                lista_equipos,
                index=min(1, len(lista_equipos) - 1),
                key="sb_visit",
            )

        if local != visitante:
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            FACTOR_LOCALIA = 0.15
            xg_proyectado_local = round(
                float(row_loc.get("xG", 1.25)) * (1.0 + FACTOR_LOCALIA), 2
            )
            xg_proyectado_visi = round(
                float(row_vis.get("xG", 1.10)) * (1.0 - (FACTOR_LOCALIA * 0.5)),
                2,
            )

            stats_loc = consolidar_estadisticas(
                local, df, stats_wikipedia, xg_proyectado_local
            )
            stats_vis = consolidar_estadisticas(
                visitante, df, stats_wikipedia, xg_proyectado_visi
            )

            prob_loc, prob_empate, prob_vis = realizar_prediccion(
                local,
                visitante,
                df,
                stats_loc,
                stats_vis,
                xg_proyectado_local,
                xg_proyectado_visi,
                factor_localia=FACTOR_LOCALIA,
            )

            st.markdown(
                f"<h2 style='text-align: center; color: #fff; margin-top:"
                f" 20px;'>{local} vs {visitante}</h2>",
                unsafe_allow_html=True,
            )

            m1, m2, m3 = st.columns(3)
            m1.metric(label=f"Gana {local}", value=f"{prob_loc:.1f}%")
            m2.metric(label="Empate", value=f"{prob_empate:.1f}%")
            m3.metric(label=f"Gana {visitante}", value=f"{prob_vis:.1f}%")

            st.markdown("---")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(
                    "<h4 style='color: #cbd5e1;'>Análisis Radar Comparativo</h4>",
                    unsafe_allow_html=True,
                )
                fig_radar = generar_radar(
                    local, visitante, stats_loc, stats_vis
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_g2:
                st.markdown(
                    "<h4 style='color: #cbd5e1;'>Monte Carlo (Simulación"
                    " Goles)</h4>",
                    unsafe_allow_html=True,
                )
                _, _, _, goles_sim = simular_monte_carlo(
                    stats_loc["xG"], stats_vis["xG"]
                )
                fig_hist = go.Figure(
                    go.Histogram(
                        x=goles_sim,
                        nbinsx=8,
                        marker_color="#38bdf8",
                        opacity=0.7,
                    )
                )
                fig_hist.update_layout(
                    paper_bgcolor="#0b0f19",
                    plot_bgcolor="#111827",
                    font=dict(color="#cbd5e1"),
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                st.plotly_chart(fig_hist, use_container_width=True)
else:
    st.error("No se localizó el archivo 'datos_procesados.csv'.")

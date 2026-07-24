import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="Win Predictor", page_icon="⚽")

st.title("⚽ Win Predictor - Liga Argentina")
st.write("Predicciones de Inteligencia Artificial basadas en rendimiento y rachas recientes.")

@st.cache_data
def preparar_datos_y_modelo():
    try:
        df = pd.read_csv("datos/datos_procesados.csv")
    except FileNotFoundError:
        df = pd.read_csv("datos_procesados.csv")
    
    # Limpieza básica
    df = df.dropna(subset=["Local", "Visitante", "Resultado"])
    
    le = LabelEncoder()
    equipos = pd.concat([df["Local"], df["Visitante"]]).unique()
    le.fit(equipos)
    
    df["Local_Num"] = le.transform(df["Local"])
    df["Visita_Num"] = le.transform(df["Visitante"])
    
    X = df[["Local_Num", "Visita_Num", "Racha_Local", "Racha_Visita"]]
    y = df["Resultado"]
    
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X, y)
    
    return df, modelo, le, equipos

def racha_equipo(df, equipo):
    partidos = df[(df['Local'] == equipo) | (df['Visitante'] == equipo)].tail(5)
    pts = 0
    for _, f in partidos.iterrows():
        if f['Local'] == equipo and f['Resultado'] == 'L': pts += 3
        elif f['Visitante'] == equipo and f['Resultado'] == 'V': pts += 3
        elif f['Resultado'] == 'E': pts += 1
    return pts

try:
    df, modelo, le, equipos = preparar_datos_y_modelo()
    
    # --- PREDICCIÓN ---
    col1, col2 = st.columns(2)
    with col1:
        local = st.selectbox("🏠 Local", sorted(equipos))
    with col2:
        visitante = st.selectbox("✈️ Visitante", sorted(equipos), index=1)
        
    if st.button("🔮 Predecir Partido"):
        if local == visitante:
            st.error("Seleccioná dos equipos diferentes.")
        else:
            r_l = racha_equipo(df, local)
            r_v = racha_equipo(df, visitante)
            
            st.info(f"📊 **Puntos últimos 5 partidos:** {local} ({r_l} pts) | {visitante} ({r_v} pts)")
            
            l_num = le.transform([local])[0]
            v_num = le.transform([visitante])[0]
            
            pred = modelo.predict([[l_num, v_num, r_l, r_v]])[0]
            probs = modelo.predict_proba([[l_num, v_num, r_l, r_v]])[0]
            clases = list(modelo.classes_)
            
            p_L = probs[clases.index('L')] * 100
            p_E = probs[clases.index('E')] * 100
            p_V = probs[clases.index('V')] * 100
            
            if pred == "L":
                st.success(f"🏆 Pronóstico: Gana **{local}**")
            elif pred == "V":
                st.success(f"🏆 Pronóstico: Gana **{visitante}**")
            else:
                st.warning("🤝 Pronóstico: **Empate**")
                
            st.write(f"Probabilidades: **{local}** {p_L:.1f}% | **Empate** {p_E:.1f}% | **{visitante}** {p_V:.1f}%")

    # --- TABLA DE POSICIONES CALCULADA Y EXACTA ---
    st.divider()
    st.subheader("🏆 Tabla de Posiciones Torneo")
    
    stats = {}
    for _, f in df.iterrows():
        l, v, res = f["Local"], f["Visitante"], f["Resultado"]
        
        if l not in stats: stats[l] = {"PJ": 0, "G": 0, "E": 0, "P": 0, "Pts": 0}
        if v not in stats: stats[v] = {"PJ": 0, "G": 0, "E": 0, "P": 0, "Pts": 0}
        
        stats[l]["PJ"] += 1
        stats[v]["PJ"] += 1
        
        if res == "L":
            stats[l]["G"] += 1
            stats[l]["Pts"] += 3
            stats[v]["P"] += 1
        elif res == "V":
            stats[v]["G"] += 1
            stats[v]["Pts"] += 3
            stats[l]["P"] += 1
        else:
            stats[l]["E"] += 1
            stats[v]["E"] += 1
            stats[l]["Pts"] += 1
            stats[v]["Pts"] += 1
            
    df_tabla = pd.DataFrame.from_dict(stats, orient="index").sort_values(by=["Pts", "PJ"], ascending=[False, True]).reset_index()
    df_tabla = df_tabla.rename(columns={"index": "Equipo"})
    df_tabla.index = df_tabla.index + 1
    
    st.dataframe(df_tabla, use_container_width=True)

except Exception as e:
    st.error(f"❌ Cargando datos... (Si persiste, corré el robot en Actions). Detalle: {e}")

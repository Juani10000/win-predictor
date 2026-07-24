import pandas as pd
import os

def calcular_rachas(df, n_partidos=5):
    if df.empty or "Local" not in df.columns:
        print("⚠️ El archivo de datos está vacío o incompleto.")
        return df

    df['Racha_Local'] = 0
    df['Racha_Visita'] = 0

    historial_puntos = {}

    for i, fila in df.iterrows():
        local = fila['Local']
        visita = fila['Visitante']
        res = fila.get('Resultado', 'E')

        if local not in historial_puntos: historial_puntos[local] = []
        if visita not in historial_puntos: historial_puntos[visita] = []

        df.at[i, 'Racha_Local'] = sum(historial_puntos[local][-n_partidos:]) if historial_puntos[local] else 0
        df.at[i, 'Racha_Visita'] = sum(historial_puntos[visita][-n_partidos:]) if historial_puntos[visita] else 0

        if res == 'L':
            historial_puntos[local].append(3)
            historial_puntos[visita].append(0)
        elif res == 'V':
            historial_puntos[local].append(0)
            historial_puntos[visita].append(3)
        else:
            historial_puntos[local].append(1)
            historial_puntos[visita].append(1)

    return df

if __name__ == "__main__":
    ruta_input = "datos/liga_argentina.csv"
    
    if os.path.exists(ruta_input) and os.path.getsize(ruta_input) > 10:
        df = pd.read_csv(ruta_input)
        print("⚡ Calculando rachas...")
        df_proc = calcular_rachas(df)
        df_proc.to_csv("datos/datos_procesados.csv", index=False)
        print("✅ 'datos_procesados.csv' creado correctamente.")
    else:
        print("❌ Error: 'liga_argentina.csv' no existe o está vacío.")

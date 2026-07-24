import pandas as pd
import numpy as np

def calcular_rachas(df, n_partidos=5):
    """
    Calcula los puntos obtenidos por cada equipo en sus últimos N partidos.
    """
    df['Fecha_Partido'] = pd.to_datetime(df['Fecha_Partido']) if 'Fecha_Partido' in df.columns else df.index
    df = df.sort_values(by='Fecha_Partido').reset_index(drop=True)

    # Creamos columnas vacías para las rachas
    df['Racha_Local'] = 0
    df['Racha_Visita'] = 0

    # Historial de resultados por equipo: list de puntos [3, 1, 0, ...]
    historial_puntos = {}

    for i, fila in df.iterrows():
        local = fila['Local']
        visita = fila['Visitante']
        res = fila['Resultado']

        # Inicializar historial si no existe
        if local not in historial_puntos: historial_puntos[local] = []
        if visita not in historial_puntos: historial_puntos[visita] = []

        # 1. Calcular la racha PREVIA a este partido (últimos N encuentros)
        df.at[i, 'Racha_Local'] = sum(historial_puntos[local][-n_partidos:]) if historial_puntos[local] else 0
        df.at[i, 'Racha_Visita'] = sum(historial_puntos[visita][-n_partidos:]) if historial_puntos[visita] else 0

        # 2. Guardar el resultado de HOY para los próximos partidos
        if res == 'L':
            historial_puntos[local].append(3)
            historial_puntos[visita].append(0)
        elif res == 'V':
            historial_puntos[local].append(0)
            historial_puntos[visita].append(3)
        else: # Empate 'E'
            historial_puntos[local].append(1)
            historial_puntos[visita].append(1)

    return df

if __name__ == "__main__":
    print("🔄 Cargando datos originales...")
    df = pd.read_csv("datos/liga_argentina.csv")
    
    print("⚡ Calculando rachas recientes...")
    df_procesado = calcular_rachas(df, n_partidos=5)
    
    # Guardar el archivo procesado con las nuevas variables
    df_procesado.to_csv("datos/datos_procesados.csv", index=False)
    print("✅ ¡'datos_procesados.csv' generado con éxito con las rachas!")

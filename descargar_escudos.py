import os
import urllib.request

# Crea la carpeta si no existe
if not os.path.exists('escudos'):
    os.makedirs('escudos')

print("Descargando escudos, por favor espera...")

ESCUDOS_WIKIPEDIA = {
    "lpf_logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg/200px-Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg.png",
    "argentinos": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/AAAJ_logo.svg/100px-AAAJ_logo.svg.png",
    "atletico_tucuman": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg/100px-Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg.png",
    "banfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Banfield.svg.png",
    "barracas": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_de_Barracas_Central.svg/100px-Escudo_de_Barracas_Central.svg.png",
    "belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg/100px-Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg.png",
    "boca": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg.png",
    "central_cordoba": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg/100px-Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg.png",
    "defensa": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg/100px-Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg.png",
    "riestra": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Deportivo_Riestra_logo.svg/100px-Deportivo_Riestra_logo.svg.png",
    "estudiantes_lp": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Escudo_de_Estudiantes_de_La_Plata.svg/100px-Escudo_de_Estudiantes_de_La_Plata.svg.png",
    "gimnasia_lp": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Gimnasia_y_Esgrima_de_La_Plata_logo.svg/100px-Gimnasia_y_Esgrima_de_La_Plata_logo.svg.png",
    "godoy_cruz": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg/100px-Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg.png",
    "huracan": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg.png",
    "independiente_rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg/100px-Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg.png",
    "independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Escudo_del_Club_Atl%C3%A9tico_Independiente.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Independiente.svg.png",
    "instituto": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Escudo_de_Instituto_ACC.svg/100px-Escudo_de_Instituto_ACC.svg.png",
    "lanus": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg.png",
    "newell": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg.png",
    "platense": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Escudo_del_Club_Atl%C3%A9tico_Platense.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Platense.svg.png",
    "racing": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Escudo_de_Racing_Club.svg/100px-Escudo_de_Racing_Club.svg.png",
    "river": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/100px-Escudo_del_C_A_River_Plate.svg.png",
    "rosario_central": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg.png",
    "san_lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
    "sarmiento": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg.png",
    "talleres": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg.png",
    "tigre": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Tigre.svg.png",
    "union": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg.png",
    "velez": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
    "aldosivi": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg.png",
    "san_martin_sj": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg.png"
}

for equipo, url in ESCUDOS_WIKIPEDIA.items():
    ruta = f"escudos/{equipo}.png"
    try:
        urllib.request.urlretrieve(url, ruta)
        print(f"✅ Descargado: {equipo}.png")
    except Exception as e:
        print(f"❌ Error descargando {equipo}: {e}")

print("¡Listo! Ya tenés todos los escudos en tu computadora.")

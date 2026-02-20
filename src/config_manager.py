import os
import json
import pandas as pd

# --- CONFIGURACIÓN DE ARCHIVOS ---
ARCHIVO_AJUSTES = "data/ajustes_produccion.json"


def cargar_ajustes():
    if os.path.exists(ARCHIVO_AJUSTES):
        with open(ARCHIVO_AJUSTES, "r") as f:
            df = pd.DataFrame(json.load(f))
            # Limpiar espacios en "Masa Base" para evitar errores de sincronización
            if "Masa Base" in df.columns:
                df["Masa Base"] = df["Masa Base"].astype(str).str.strip()
            return df
    else:
        df_defecto = pd.DataFrame(
            {
                "Masa Base": [
                    "SALVADO GRANDE",
                    "BLANCO GRANDE",
                    "INTEGRAL SEMILLADO",
                    "BLANCO LARGO",
                    "SALVADO LARGO",
                    "BLANCO CHICO",
                    "SEMILLADO CHICO",
                    "OCHO CEREALES",
                    "SEMILLADO MEDIANO",
                    "SEMILLADO SIN SAL",
                    "CAMPO MEDIANO",
                    "BAGEL BCO SEMILLADO GDE",
                    "BAGEL BCO GDE",
                    "BAGEL INTEGRAL GDE",
                ],
                "Tope 1 (Crítico)": [
                    600,
                    400,
                    200,
                    150,
                    150,
                    300,
                    300,
                    150,
                    100,
                    100,
                    80,
                    50,
                    50,
                    50,
                ],
                "Producir 1": [
                    370,
                    260,
                    155,
                    130,
                    135,
                    200,
                    200,
                    200,
                    140,
                    140,
                    140,
                    130,
                    130,
                    130,
                ],
                "Tope 2 (Medio)": [
                    900,
                    600,
                    350,
                    250,
                    250,
                    500,
                    500,
                    250,
                    200,
                    200,
                    150,
                    100,
                    100,
                    100,
                ],
                "Producir 2": [
                    260,
                    130,
                    80,
                    65,
                    65,
                    100,
                    100,
                    100,
                    70,
                    70,
                    70,
                    65,
                    65,
                    65,
                ],
                "Tope 3 (Alto)": [
                    1200,
                    800,
                    500,
                    400,
                    400,
                    700,
                    700,
                    400,
                    300,
                    300,
                    200,
                    150,
                    150,
                    150,
                ],
                "Producir 3": [135, 65, 40, 30, 30, 50, 50, 50, 35, 35, 35, 30, 30, 30],
            }
        )
        guardar_ajustes(df_defecto)
        return df_defecto


def guardar_ajustes(df):
    ruta = "data/ajustes_produccion.json"
    # Convertimos el DataFrame a diccionario y luego a JSON
    dict_ajustes = df.to_dict(orient="records")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(dict_ajustes, f, indent=4, ensure_ascii=False)

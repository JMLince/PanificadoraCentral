import math
import pandas as pd
import os
from datetime import datetime


def aplicar_redondeo(n):
    """Mantiene la lógica de redondeo específica de la panificadora."""
    if n == 0:
        return 0.0
    parte_entera = math.floor(n)
    decimal = round(n - parte_entera, 2)
    if decimal <= 0.06:
        return float(parte_entera)
    elif 0.07 <= decimal <= 0.55:
        return parte_entera + 0.50
    else:
        return float(parte_entera + 1)


def guardar_en_historial(df, turno, usuario, comentario=None):
    ruta_historial = "data/historial_produccion.csv"
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    hora_registro = datetime.now().strftime("%H:%M:%S")

    # 1. Preparar el DataFrame de la sesión actual
    df_actual = df.copy()

    if os.path.exists(ruta_historial):
        try:
            historial_completo = pd.read_csv(ruta_historial)
            # Calculamos cuánto hay registrado actualmente para este día y turno (Suma neta)
            ya_registrado = (
                historial_completo[
                    (historial_completo["Fecha"] == fecha_hoy)
                    & (historial_completo["Turno"] == turno)
                ]
                .groupby("TIPO DE PAN")["MASAS"]
                .sum()
                .reset_index()
            )

            if not ya_registrado.empty:
                if not comentario:
                    return False, "Ya existe un registro. Use 'Corregir' con motivo."

                # --- LÓGICA DE DIFERENCIA NETA (MÁXIMA EFICIENCIA) ---
                ajustes = []
                for _, fila_nueva in df_actual.iterrows():
                    pan = fila_nueva["TIPO DE PAN"]
                    valor_nuevo = fila_nueva["MASAS"]

                    # Buscamos cuánto sumaba ese pan en el historial
                    valor_anterior = ya_registrado.loc[
                        ya_registrado["TIPO DE PAN"] == pan, "MASAS"
                    ].values
                    valor_anterior = valor_anterior[0] if len(valor_anterior) > 0 else 0

                    diferencia = valor_nuevo - valor_anterior

                    if diferencia != 0:
                        # Solo guardamos el movimiento que ajusta el saldo
                        nueva_fila = fila_nueva.copy()
                        nueva_fila["MASAS"] = diferencia
                        nueva_fila["Fecha"] = fecha_hoy
                        nueva_fila["Hora"] = hora_registro
                        nueva_fila["Turno"] = turno
                        nueva_fila["Usuario"] = usuario
                        nueva_fila["Comentario"] = f"AJUSTE: {comentario}"
                        ajustes.append(nueva_fila)

                if ajustes:
                    df_final_ajustes = pd.DataFrame(ajustes)
                    nuevo_historial = pd.concat(
                        [historial_completo, df_final_ajustes], ignore_index=True
                    )
                else:
                    return True, "No hubo cambios en los valores."
            else:
                # Es la primera carga del turno
                df_actual["Fecha"] = fecha_hoy
                df_actual["Hora"] = hora_registro
                df_actual["Turno"] = turno
                df_actual["Usuario"] = usuario
                df_actual["Comentario"] = ""
                nuevo_historial = pd.concat(
                    [historial_completo, df_actual], ignore_index=True
                )

        except Exception as e:
            return False, f"Error: {e}"
    else:
        # El archivo no existe, primera carga total
        df_actual["Fecha"] = fecha_hoy
        df_actual["Hora"] = hora_registro
        df_actual["Turno"] = turno
        df_actual["Usuario"] = usuario
        df_actual["Comentario"] = "Carga Inicial"
        nuevo_historial = df_actual

    nuevo_historial.to_csv(ruta_historial, index=False)
    return True, "Ajuste de saldo guardado."


def guardar_historial_stock(df_rpd, df_pa, usuario, comentario=""):
    """
    Guarda una captura del stock inicial y demanda cargada por el usuario.
    CORRECCIÓN: Mantiene identidad de productos PA y evita duplicados.
    """
    archivo = "data/historial_stock.csv"
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    hora_actual = datetime.now().strftime("%H:%M:%S")

    if not os.path.exists("data"):
        os.makedirs("data")

    # 1. Procesar Stock RPD
    # (Usamos 'Masa Base' como Producto porque en RPD son 1 a 1)
    df_rpd_log = df_rpd[["Masa Base", "Stock Actual"]].copy()
    df_rpd_log.columns = ["Producto", "Cantidad"]
    df_rpd_log["Demanda"] = 0
    df_rpd_log["Origen"] = "RPD"

    # 2. Procesar Pedidos PA
    # CORRECCIÓN: NO agrupar por Masa Base. Usar el nombre del 'Producto' individual.
    df_pa_log = df_pa[["Producto", "Stock Inicial", "Demanda"]].copy()
    df_pa_log.columns = ["Producto", "Cantidad", "Demanda"]
    df_pa_log["Origen"] = "PA"

    # 3. Combinar ambos
    df_nuevo = pd.concat([df_rpd_log, df_pa_log], ignore_index=True)
    df_nuevo["Fecha"] = fecha_hoy
    df_nuevo["Hora"] = hora_actual
    df_nuevo["Usuario"] = usuario
    df_nuevo["Comentario"] = comentario

    # 4. Evitar duplicados en el mismo día (Lógica de sobreescritura)
    if os.path.exists(archivo):
        try:
            historial_viejo = pd.read_csv(archivo)
            # Filtramos para ELIMINAR lo que sea de hoy antes de guardar lo nuevo
            historial_limpio = historial_viejo[historial_viejo["Fecha"] != fecha_hoy]
            df_final = pd.concat([historial_limpio, df_nuevo], ignore_index=True)
        except:
            df_final = df_nuevo
    else:
        df_final = df_nuevo

    # 5. Guardar archivo final
    try:
        df_final.to_csv(archivo, index=False, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error crítico al guardar stock: {e}")
        return False

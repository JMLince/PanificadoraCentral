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

    # 1. Limpieza de datos entrantes
    df_actual = df.copy()
    df_actual["MASAS"] = pd.to_numeric(df_actual["MASAS"], errors="coerce").fillna(0)

    if os.path.exists(ruta_historial):
        try:
            historial_completo = pd.read_csv(ruta_historial)

            # 2. Obtener el SALDO ACTUAL real del historial para este día y turno
            # Esto es vital: sumamos todo lo que hay (cargas + ajustes previos)
            mask_hoy = (historial_completo["Fecha"].astype(str) == fecha_hoy) & (
                historial_completo["Turno"] == turno
            )

            ya_registrado = historial_completo[mask_hoy]

            if not ya_registrado.empty:
                if not comentario:
                    return False, "Ya existe un registro confirmado."

                # Agrupamos para saber el total neto actual por producto
                saldos_actuales = (
                    ya_registrado.groupby("TIPO DE PAN")["MASAS"].sum().to_dict()
                )

                ajustes_reales = []
                for _, fila_nueva in df_actual.iterrows():
                    pan = fila_nueva["TIPO DE PAN"]
                    valor_final_deseado = float(fila_nueva["MASAS"])
                    valor_en_historial = float(saldos_actuales.get(pan, 0))

                    # CÁLCULO DE LA DIFERENCIA EXACTA
                    diferencia = round(valor_final_deseado - valor_en_historial, 2)

                    # SOLO SI HAY DIFERENCIA, CREAMOS UNA FILA
                    if abs(diferencia) > 0.001:
                        nueva_fila = {
                            "TIPO DE PAN": pan,
                            "MASAS": diferencia,
                            "Fecha": fecha_hoy,
                            "Hora": hora_registro,
                            "Turno": turno,
                            "Usuario": usuario,
                            "Comentario": f"AJUSTE: {comentario}",
                        }
                        # Mantener columnas adicionales (Corte, Tapa) si existen
                        for col in ["CORTE", "TAPA"]:
                            if col in fila_nueva:
                                nueva_fila[col] = fila_nueva[col]

                        ajustes_reales.append(nueva_fila)

                if ajustes_reales:
                    df_final_ajustes = pd.DataFrame(ajustes_reales)
                    nuevo_historial = pd.concat(
                        [historial_completo, df_final_ajustes], ignore_index=True
                    )
                else:
                    return True, "No se detectaron cambios que requieran ajuste."
            else:
                # Primera carga del día (aquí sí van las 14 filas originales)
                df_actual["Fecha"] = fecha_hoy
                df_actual["Hora"] = hora_registro
                df_actual["Turno"] = turno
                df_actual["Usuario"] = usuario
                df_actual["Comentario"] = "Carga Inicial"
                nuevo_historial = pd.concat(
                    [historial_completo, df_actual], ignore_index=True
                )

        except Exception as e:
            return False, f"Error: {str(e)}"
    else:
        # Si el archivo no existe
        df_actual["Fecha"] = fecha_hoy
        df_actual["Hora"] = hora_registro
        df_actual["Turno"] = turno
        df_actual["Usuario"] = usuario
        df_actual["Comentario"] = "Carga Inicial"
        nuevo_historial = df_actual

    nuevo_historial.to_csv(ruta_historial, index=False)
    return True, "Registro actualizado."


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

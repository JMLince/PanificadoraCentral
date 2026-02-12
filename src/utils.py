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

    # 1. Preparar el nuevo registro
    df_nuevo = df.copy()
    df_nuevo["Fecha"] = fecha_hoy
    df_nuevo["Hora"] = hora_registro
    df_nuevo["Turno"] = turno
    df_nuevo["Usuario"] = usuario
    df_nuevo["Comentario"] = comentario if comentario else ""

    if os.path.exists(ruta_historial):
        try:
            historial = pd.read_csv(ruta_historial)
            ya_existe = historial[
                (historial["Fecha"] == fecha_hoy) & (historial["Turno"] == turno)
            ]

            if not ya_existe.empty:
                if not comentario:
                    return False, "Ya existe un registro confirmado."

                # --- LÓGICA DE AJUSTE QUIRÚRGICO ---
                movimientos_ajuste = []

                # Unimos el registro viejo con el nuevo para comparar
                # Asumimos que "TIPO DE PAN" es la clave única
                comparativa = pd.merge(
                    ya_existe[["TIPO DE PAN", "MASAS"]],
                    df_nuevo[["TIPO DE PAN", "MASAS"]],
                    on="TIPO DE PAN",
                    suffixes=("_viejo", "_nuevo"),
                )

                for _, fila in comparativa.iterrows():
                    val_v = fila["MASAS_viejo"]
                    val_n = fila["MASAS_nuevo"]

                    if val_v != val_n:
                        # 1. Anulación parcial (Solo de lo que cambió)
                        anulacion = df_nuevo[
                            df_nuevo["TIPO DE PAN"] == fila["TIPO DE PAN"]
                        ].copy()
                        anulacion["MASAS"] = -val_v
                        anulacion["Comentario"] = f"ANULACIÓN PARCIAL: {comentario}"

                        # 2. Nuevo valor (Solo del que cambió)
                        correccion = df_nuevo[
                            df_nuevo["TIPO DE PAN"] == fila["TIPO DE PAN"]
                        ].copy()
                        correccion["MASAS"] = val_n
                        correccion["Comentario"] = comentario

                        movimientos_ajuste.extend([anulacion, correccion])

                if movimientos_ajuste:
                    df_ajustes = pd.concat(movimientos_ajuste, ignore_index=True)
                    nuevo_historial = pd.concat(
                        [historial, df_ajustes], ignore_index=True
                    )
                else:
                    return True, "No se detectaron cambios en los valores."
            else:
                nuevo_historial = pd.concat([historial, df_nuevo], ignore_index=True)

        except Exception as e:
            return False, f"Error al procesar: {e}"
    else:
        nuevo_historial = df_nuevo

    try:
        nuevo_historial.to_csv(ruta_historial, index=False)
        return True, "Ajuste parcial guardado con éxito."
    except Exception as e:
        return False, f"Error al guardar: {e}"


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

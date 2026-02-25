from fpdf import FPDF
from datetime import datetime
import os
import pandas as pd


def generar_pdf_produccion(df, turno):
    pdf = FPDF()
    pdf.add_page()

    # --- INSERTAR LOGO ---
    ruta_logo = "assets/logo_nb.png"
    if os.path.exists(ruta_logo):
        # x=10 (izq), y=8 (arriba), w=30 (ancho en mm)
        pdf.image(ruta_logo, x=10, y=8, w=30)

    # --- TÍTULO Y FECHA (Desplazados a la derecha del logo) ---
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40)  # Espacio para que el texto no tape el logo
    pdf.cell(0, 10, f"PLAN DE PRODUCCION", ln=True, align="L")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(40)
    pdf.cell(0, 10, f"TURNO: {turno.upper()}", ln=True, align="L")

    pdf.set_font("Arial", "I", 9)
    pdf.cell(
        0,
        5,
        f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ln=True,
        align="R",
    )

    pdf.ln(15)  # Espacio antes de la tabla

    # --- ENCABEZADOS DE TABLA ---
    pdf.set_fill_color(240, 240, 240)  # Gris muy claro
    pdf.set_font("Arial", "B", 10)
    pdf.cell(85, 10, " TIPO DE PAN", 1, 0, "L", True)
    pdf.cell(25, 10, " MASAS", 1, 0, "C", True)
    pdf.cell(40, 10, " CORTE (gr)", 1, 0, "C", True)
    pdf.cell(30, 10, " TAPA", 1, 1, "C", True)

    # --- CONTENIDO ---
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        # Alternar color de fondo suave para filas
        pdf.cell(85, 8, f" {row['TIPO DE PAN']}", 1)
        pdf.cell(25, 8, str(row["MASAS"]), 1, 0, "C")
        pdf.cell(40, 8, str(row["CORTE"]), 1, 0, "C")
        pdf.cell(30, 8, row["TAPA"], 1, 1, "C")

    # --- TOTAL FINAL ---
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(
        0, 10, f"Total Masas del Turno: {df['MASAS'].sum():.1f}", ln=True, align="R"
    )

    return bytes(pdf.output())


def exportar_pedido_pdf(pedido_id, detalle_productos, info_cliente):
    """
    Genera un PDF profesional con el detalle de un pedido.

    Args:
        pedido_id (str): ID del pedido
        detalle_productos (pd.DataFrame): DataFrame con columnas ["Producto", "Unidades"] (sin Obs)
        info_cliente (pd.Series): Serie con información: Cliente, Fecha_Entrega, Fecha_Registro, Estado, Obs

    Returns:
        bytes: Contenido del PDF en memoria
    """
    pdf = FPDF()
    pdf.add_page()

    # --- ENCABEZADO: NOMBRE DE LA EMPRESA ---
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, "PANIFICADORA CENTRAL", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 5, "Pedido de Productos", ln=True, align="C")
    pdf.ln(5)

    # --- INFORMACIÓN DEL PEDIDO (Izq-Der) ---
    pdf.set_font("Arial", "B", 11)
    pdf.cell(50, 8, "Nro. Pedido:", 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, str(pedido_id), 0, 1)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(50, 8, "Cliente:", 0, 0)
    pdf.set_font("Arial", "", 11)
    cliente = (
        info_cliente.get("Cliente", "N/A")
        if hasattr(info_cliente, "get")
        else info_cliente["Cliente"]
    )
    pdf.cell(0, 8, str(cliente), 0, 1)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(50, 8, "Fecha de Registro:", 0, 0)
    pdf.set_font("Arial", "", 11)
    fecha_registro = (
        info_cliente.get("Fecha_Registro", "N/A")
        if hasattr(info_cliente, "get")
        else info_cliente["Fecha_Registro"]
    )
    pdf.cell(0, 8, str(fecha_registro), 0, 1)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(50, 8, "Fecha de Entrega:", 0, 0)
    pdf.set_font("Arial", "", 11)
    fecha_entrega = (
        info_cliente.get("Fecha_Entrega", "N/A")
        if hasattr(info_cliente, "get")
        else info_cliente["Fecha_Entrega"]
    )
    pdf.cell(0, 8, str(fecha_entrega), 0, 1)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(50, 8, "Estado:", 0, 0)
    pdf.set_font("Arial", "", 11)
    estado = (
        info_cliente.get("Estado", "N/A")
        if hasattr(info_cliente, "get")
        else info_cliente["Estado"]
    )
    pdf.cell(0, 8, str(estado), 0, 1)

    pdf.ln(8)

    # --- TABLA DE PRODUCTOS (sin columna de Observaciones) ---
    pdf.set_fill_color(41, 84, 209)  # Azul profesional
    pdf.set_text_color(255, 255, 255)  # Blanco
    pdf.set_font("Arial", "B", 11)

    # Ancho de columnas: Producto (120mm), Unidades (70mm)
    pdf.cell(120, 10, "PRODUCTO", 1, 0, "L", True)
    pdf.cell(0, 10, "UNIDADES", 1, 1, "C", True)

    # --- CONTENIDO DE LA TABLA ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 10)

    row_height = 8

    # Iterar sobre los productos (solo Producto y Unidades)
    for _, row in detalle_productos.iterrows():
        producto = str(row.get("Producto", "")).strip()
        unidades = str(row.get("Unidades", "")).strip()

        # Limitar longitud del producto para que se vea bien
        if len(producto) > 45:
            producto = producto[:42] + "..."

        pdf.cell(120, row_height, producto, 1, 0, "L")
        pdf.cell(0, row_height, unidades, 1, 1, "C")

    # --- TOTAL DE UNIDADES ---
    pdf.ln(5)
    total_unidades = detalle_productos["Unidades"].astype(int).sum()
    pdf.set_font("Arial", "B", 11)
    pdf.cell(120, 10, "TOTAL UNIDADES:", 0, 0, "R")
    pdf.cell(0, 10, str(total_unidades), 0, 1, "C")

    # --- OBSERVACIONES GENERALES (al final, una sola vez) ---
    obs_general = (
        info_cliente.get("Obs", "")
        if hasattr(info_cliente, "get")
        else info_cliente.get("Obs", "")
    )

    pdf.ln(8)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "OBSERVACIONES GENERALES:", 0, 1)
    pdf.set_font("Arial", "", 9)

    if obs_general and str(obs_general).strip() and not pd.isna(obs_general):
        pdf.multi_cell(0, 5, str(obs_general).strip())
    else:
        pdf.multi_cell(0, 5, "Sin observaciones")

    # --- PIE DE PÁGINA ---
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(
        0,
        10,
        f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        0,
        1,
        "R",
    )

    return bytes(pdf.output())

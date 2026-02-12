from fpdf import FPDF
from datetime import datetime
import os


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

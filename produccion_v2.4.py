import streamlit as st
import pandas as pd
import os
import signal
import time
from datetime import datetime, timedelta


# IMPORTACIONES MODULARES DESDE TU CARPETA SRC
from src.utils import aplicar_redondeo, guardar_en_historial
from src.config_manager import cargar_ajustes, guardar_ajustes
from src.auth import generar_login
from src.report_generator import generar_pdf_produccion

# --- CONFIGURACIÓN DE PÁGINA ---
# Debe ser lo primero que se ejecute
st.set_page_config(page_title="Panificadora Central v2.4", layout="wide")

# --- 1. SISTEMA DE LOGIN ---
# Esta función detiene la ejecución si el usuario no está autenticado
generar_login()

# --- ESTILOS CSS ---
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display: none;}
    footer {visibility: hidden;}
    
    .report-table {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        color: inherit;
    }
    .report-table th {
        background-color: rgba(128, 128, 128, 0.1);
        color: inherit;
        text-align: center !important;
        padding: 10px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.3);
    }
    .report-table td {
        text-align: center !important;
        padding: 8px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- CARGA DE DATOS ---
if "df_ajustes" not in st.session_state:
    st.session_state.df_ajustes = cargar_ajustes()

datos_tecnicos = {
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
        "SEMILLADO GRANDE",
        "CAMPO GRANDE",
        "BLANCO GDE SESAMO",
        "SALVADO CHICO",
        "MINIBAGEL INTEGRAL",
        "CAÑON BLANCO",
        "CAÑON SEMILLADO",
        "PANINO AMAPOLA",
        "SALVADO GDE C/TAPA",
        "SEMILLADO FRESH",
        "SALVADO FRESH",
    ],
    "Cant_Batch": [
        135,
        130,
        155,
        150,
        150,
        200,
        200,
        155,
        155,
        155,
        150,
        85,
        85,
        85,
        135,
        125,
        125,
        200,
        13,
        80,
        80,
        75,
        135,
        155,
        155,
    ],
    "Peso Corte": [
        650,
        650,
        650,
        580,
        580,
        420,
        420,
        570,
        570,
        570,
        570,
        110,
        110,
        110,
        650,
        650,
        650,
        420,
        85,
        950,
        950,
        1100,
        700,
        570,
        570,
    ],
    "Tapa": [
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "NO",
        "SI",
        "SI",
        "SI",
        "SI",
        "NO",
        "NO",
    ],
}
df_base = pd.DataFrame(datos_tecnicos)

st.title(f"🍞 Gestión de Producción v2.4")

# --- 2. PANEL DE CONTROL (SIDEBAR) ---
with st.sidebar:
    st.write(f"👤 **Perfil:** {st.session_state.perfil.upper()}")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    st.divider()
    p_inc = st.number_input("Factor Incremento RPD (%)", value=17)
    dias_esp = st.multiselect(
        "Días de incremento",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        default=["Tuesday"],
    )
    p_manana = st.slider("Porcentaje Turno Mañana", 0, 100, 60)

    st.divider()
    if st.button("🔴 Salir del Sistema", use_container_width=True):
        st.components.v1.html(
            """
            <script>
                const div = window.parent.document.createElement('div');
                div.style.position = 'fixed';
                div.style.top = '0'; div.style.left = '0';
                div.style.width = '100vw'; div.style.height = '100vh';
                div.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
                div.style.zIndex = '999999';
                div.style.display = 'flex';
                div.style.justifyContent = 'center'; div.style.alignItems = 'center';
                div.style.fontFamily = 'sans-serif';
                div.innerHTML = `
                    <div style="background-color: white; color: #333; padding: 30px; border-radius: 12px; text-align: center; width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border-top: 5px solid #ff4b4b;">
                        <h2 style="margin: 0; color: #ff4b4b; font-size: 1.5rem;">Sesión Finalizada</h2>
                        <p style="font-size: 1.1rem; margin: 15px 0; color: #555;">El sistema <b>v2.4</b> se ha detenido.</p>
                        <div style="height: 1px; background: #eee; margin: 15px 0;"></div>
                        <p style="font-size: 0.9rem; color: #888;">Ya puede cerrar esta pestaña con seguridad.</p>
                    </div>`;
                window.parent.document.body.appendChild(div);
            </script>
            """,
            height=0,
        )
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)

# --- 3. PESTAÑAS ---
titulos_tabs = ["📥 Carga de Stocks", "📋 Lista Agrupada", "🌅 Mañana", "🌇 Tarde"]
if st.session_state.perfil == "admin":
    titulos_tabs.append("⚙️ Ajustes Maestros")
tabs = st.tabs(titulos_tabs)

with tabs[0]:
    col_rpd, col_pa = st.columns(2)
    with col_rpd:
        st.subheader("Stock RPD")
        df_rpd_in = st.session_state.df_ajustes[["Masa Base"]].copy()
        df_rpd_in["Stock Actual"] = 0
        edit_rpd = st.data_editor(
            df_rpd_in,
            key="editor_rpd",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Masa Base": st.column_config.TextColumn(
                    "Masa Base", width="medium", disabled=True
                ),
                "Stock Actual": st.column_config.NumberColumn(
                    "Stock Actual", format="%d", required=True
                ),
            },
        )

    with col_pa:
        st.subheader("Pedidos PA")
        prod_pa = [
            ("SALVADO GRANDE", "LC SALVADO 590"),
            ("SALVADO GRANDE", "DW SALVADO 590"),
            ("BLANCO GRANDE", "LC BLANCO 590"),
            ("BLANCO GRANDE", "DW BLANCO 590"),
            ("INTEGRAL SEMILLADO", "DW INTEGRAL 590"),
            ("SEMILLADO GRANDE", "DW SEMILLADO 590DW"),
            ("CAMPO GRANDE", "CAMPO 590DW"),
            ("BLANCO GDE SESAMO", "BLANCO SESAMO 590"),
            ("BLANCO CHICO", "LC BLANCO 350DW"),
            ("BLANCO CHICO", "BLANCO 350LC"),
            ("SEMILLADO CHICO", "SEMILLADO 350DW"),
            ("SEMILLADO CHICO", "SEMILLADO 350"),
            ("SALVADO CHICO", "LC SALVADO 350"),
            ("SALVADO CHICO", "DW SALVADO 350"),
            ("CAMPO MEDIANO", "FRESH CAMPO 500"),
            ("MINIBAGEL INTEGRAL", "CAJA x40 u. MINIBAGEL"),
            ("CAÑON BLANCO", "BCO C/TAPA 800 - RICAPAN"),
            ("CAÑON BLANCO", "BCO C/TAPA 800 - CAÑON"),
            ("CAÑON SEMILLADO", "MULTIC C/T 800 - RICAPAN"),
            ("CAÑON SEMILLADO", "MULTIC C/T 800 - CAÑON"),
            ("PANINO AMAPOLA", "BCO AMAPOLA 950 - PANINO"),
            ("SALVADO GDE C/TAPA", "SALVADO GDE C/TAPA - CAÑON"),
            ("SEMILLADO FRESH", "MULTIC. FETEADO FRESH"),
            ("SEMILLADO FRESH", "MULTIC. ENTERO FRESH"),
            ("SALVADO FRESH", "SALVADO FETEADO FRESH"),
        ]
        df_pa_in = pd.DataFrame(prod_pa, columns=["Masa Base", "Producto"])
        df_pa_in["Stock Inicial"] = 0
        df_pa_in["Demanda"] = 0
        edit_pa = st.data_editor(
            df_pa_in,
            key="editor_pa",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Masa Base": st.column_config.TextColumn("Masa Base", disabled=True),
                "Producto": st.column_config.TextColumn("Producto", disabled=True),
                "Stock Inicial": st.column_config.NumberColumn(
                    "Stock Inicial", format="%d"
                ),
                "Demanda": st.column_config.NumberColumn("Demanda", format="%d"),
            },
        )

# --- MOTOR DE CÁLCULO ---
factor = (1 + (p_inc / 100)) if datetime.now().strftime("%A") in dias_esp else 1.0
df_rpd_calc = pd.merge(edit_rpd, st.session_state.df_ajustes, on="Masa Base")


def logica_t(row):
    s = row["Stock Actual"]
    if s <= row["Tope 1 (Crítico)"]:
        return row["Producir 1"]
    if s <= row["Tope 2 (Medio)"]:
        return row["Producir 2"]
    if s <= row["Tope 3 (Alto)"]:
        return row["Producir 3"]
    return 0


df_rpd_calc["Unidades"] = df_rpd_calc.apply(logica_t, axis=1)
df_rpd_calc = pd.merge(
    df_rpd_calc, df_base[["Masa Base", "Cant_Batch"]], on="Masa Base"
)
df_rpd_calc["Batches_RPD"] = (
    df_rpd_calc["Unidades"] / df_rpd_calc["Cant_Batch"]
) * factor

edit_pa["Neto"] = (edit_pa["Demanda"] - edit_pa["Stock Inicial"]).clip(lower=0)
pa_agrupado = edit_pa.groupby("Masa Base").agg({"Neto": "sum"}).reset_index()
pa_agrupado = pd.merge(
    pa_agrupado, df_base[["Masa Base", "Cant_Batch"]], on="Masa Base", how="left"
)
pa_agrupado["Batches_PA"] = pa_agrupado["Neto"] / pa_agrupado["Cant_Batch"].fillna(1)

df_final = df_base[["Masa Base", "Peso Corte", "Tapa"]].copy()
df_final = pd.merge(
    df_final, df_rpd_calc[["Masa Base", "Batches_RPD"]], on="Masa Base", how="left"
)
df_final = pd.merge(
    df_final, pa_agrupado[["Masa Base", "Batches_PA"]], on="Masa Base", how="left"
).fillna(0)
df_final["TOTAL"] = (df_final["Batches_RPD"] + df_final["Batches_PA"]).apply(
    aplicar_redondeo
)


def renderizar(df, col, titulo):
    st.markdown(f"### {titulo}")
    lista = df[df[col] > 0][["Masa Base", col, "Peso Corte", "Tapa"]].copy()
    lista.columns = ["TIPO DE PAN", "MASAS", "CORTE", "TAPA"]
    html_tabla = lista.to_html(index=False, justify="center", classes="report-table")
    st.markdown(html_tabla, unsafe_allow_html=True)
    st.metric(f"Total {titulo}", f"{lista['MASAS'].sum():.1f}")


with tabs[1]:
    renderizar(df_final, "TOTAL", "Plan Total")

    # Preparamos los datos filtrados para el PDF Total
    df_total = df_final[df_final["TOTAL"] > 0][
        ["Masa Base", "TOTAL", "Peso Corte", "Tapa"]
    ]

    if not df_total.empty:
        df_total.columns = ["TIPO DE PAN", "MASAS", "CORTE", "TAPA"]

        # Generamos el PDF del plan completo
        pdf_bytes_total = generar_pdf_produccion(df_total, "Total del Día")

        st.download_button(
            label="📥 Descargar Plan Total (PDF)",
            data=pdf_bytes_total,
            file_name=f"plan_total_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_descarga_total",
        )

with tabs[2]:  # Turno Mañana
    # --- DEBUG: Actívalo quitando los 3 # para ver qué pasa ---

    # st.write(
    # f"DEBUG: Rol actual: '{st.session_state.get('rol')}' | Confirmado: {st.session_state.get('confirmado_m')}"
    # )

    # ------------------------------------------------------
    # --- NUEVA LÓGICA DE PERSISTENCIA ---
    import os
    import pandas as pd

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists("data/historial_produccion.csv"):
        hist = pd.read_csv("data/historial_produccion.csv")
        # Si ya existe registro de hoy para la mañana, marcamos como confirmado
        if not hist[(hist["Fecha"] == fecha_hoy) & (hist["Turno"] == "Mañana")].empty:
            st.session_state["confirmado_m"] = True

    df_final["M"] = (df_final["TOTAL"] * (p_manana / 100)).apply(aplicar_redondeo)
    renderizar(df_final, "M", "Turno Mañana")

    # Preparamos los datos para el registro y el PDF
    df_m = df_final[df_final["M"] > 0][["Masa Base", "M", "Peso Corte", "Tapa"]]

    if not df_m.empty:
        df_m.columns = ["TIPO DE PAN", "MASAS", "CORTE", "TAPA"]

        st.markdown("---")
        col_conf, col_pdf = st.columns(2)

        # Usamos 'perfil' que es la variable que sí tiene datos en tu sesión
        # Lo pasamos a minúsculas para que 'ADMIN' o 'admin' funcionen igual
        perfil_actual = str(st.session_state.get("perfil", "")).lower().strip()
        esta_confirmado = st.session_state.get("confirmado_m", False)

        with col_conf:
            if esta_confirmado and perfil_actual == "admin":
                with st.expander(
                    "⚠️ Corregir / Ajustar Producción Mañana", expanded=True
                ):
                    st.write(
                        "Modifique las cantidades directamente en la tabla de abajo:"
                    )

                    # --- EL EDITOR DE DATOS ---
                    # Creamos una versión editable de df_m
                    df_editable_m = st.data_editor(
                        df_m,
                        column_config={
                            "TIPO DE PAN": st.column_config.TextColumn(disabled=True),
                            "CORTE": st.column_config.NumberColumn(disabled=True),
                            "TAPA": st.column_config.TextColumn(disabled=True),
                            "MASAS": st.column_config.NumberColumn(
                                min_value=0, step=0.5
                            ),
                        },
                        hide_index=True,
                        key="editor_m",
                    )

                    st.markdown("---")
                    motivo = st.text_input(
                        "Motivo del cambio:", max_chars=60, key="txt_motivo_m"
                    )

                    if st.button(
                        "Confirmar Ajuste Autorizado",
                        type="primary",
                        use_container_width=True,
                        key="btn_ajuste_m",
                    ):
                        if len(motivo) >= 5:
                            # IMPORTANTE: Guardamos 'df_editable_m', que tiene los nuevos valores
                            exito, mensaje = guardar_en_historial(
                                df_editable_m,
                                "Mañana",
                                st.session_state.get("usuario", "Admin"),
                                motivo,
                            )
                            if exito:
                                st.success(
                                    "¡Ajuste realizado! Los nuevos valores se han guardado."
                                )
                                # Limpiamos caché para que el PDF se genere con los nuevos datos
                                st.rerun()
                        else:
                            st.warning("Escriba un motivo de al menos 5 caracteres.")

            # 2. Si NO está confirmado, botón normal
            elif not esta_confirmado:
                if st.button(
                    "✅ Confirmar Producción Mañana",
                    use_container_width=True,
                    key="btn_conf_m",
                ):
                    exito, mensaje = guardar_en_historial(
                        df_m, "Mañana", st.session_state.get("usuario", "Admin")
                    )
                    if exito:
                        st.success(mensaje)
                        st.session_state["confirmado_m"] = True
                        st.rerun()
                    else:
                        st.error(mensaje)
                        if "ya existe" in mensaje.lower():
                            st.session_state["confirmado_m"] = True
                            st.rerun()

            # 3. Confirmado por usuario común
            else:
                st.info("✅ Producción cerrada.")

        with col_pdf:
            if esta_confirmado:
                pdf_bytes = generar_pdf_produccion(df_m, "Mañana")
                st.download_button(
                    label="📥 Descargar PDF Mañana",
                    data=pdf_bytes,
                    file_name=f"plan_manana_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_pdf_m",
                )

            else:
                st.info("⚠️ Confirmar para descargar PDF.")

    else:
        st.warning("No hay producción programada para el turno mañana.")

with tabs[3]:  # Turno Tarde
    # --- PERSISTENCIA TURNO TARDE ---
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists("data/historial_produccion.csv"):
        hist = pd.read_csv("data/historial_produccion.csv")
        if not hist[(hist["Fecha"] == fecha_hoy) & (hist["Turno"] == "Tarde")].empty:
            st.session_state["confirmado_t"] = True
    # --------------------------------

    df_final["T"] = (df_final["TOTAL"] - df_final.get("M", 0)).apply(aplicar_redondeo)
    renderizar(df_final, "T", "Turno Tarde")

    df_t = df_final[df_final["T"] > 0][["Masa Base", "T", "Peso Corte", "Tapa"]]

    if not df_t.empty:
        df_t.columns = ["TIPO DE PAN", "MASAS", "CORTE", "TAPA"]

        st.markdown("---")
        col_conf_t, col_pdf_t = st.columns(2)

        perfil_actual = str(st.session_state.get("perfil", "")).lower().strip()
        esta_confirmado_t = st.session_state.get("confirmado_t", False)

        with col_conf_t:
            # 1. Ajuste para ADMIN cuando ya está confirmado
            if esta_confirmado_t and perfil_actual == "admin":
                with st.expander(
                    "⚠️ Corregir / Ajustar Producción Tarde", expanded=True
                ):
                    st.write("Modifique las cantidades de la tarde aquí:")

                    # --- EL EDITOR DE DATOS (Faltaba este bloque) ---
                    df_editable_t = st.data_editor(
                        df_t,
                        column_config={
                            "TIPO DE PAN": st.column_config.TextColumn(disabled=True),
                            "CORTE": st.column_config.NumberColumn(disabled=True),
                            "TAPA": st.column_config.TextColumn(disabled=True),
                            "MASAS": st.column_config.NumberColumn(
                                min_value=0, step=0.5
                            ),
                        },
                        hide_index=True,
                        key="editor_t",
                    )

                    st.markdown("---")
                    motivo_t = st.text_input(
                        "Motivo del cambio (Tarde):", max_chars=60, key="txt_motivo_t"
                    )

                    if st.button(
                        "Confirmar Ajuste Autorizado Tarde",
                        type="primary",
                        use_container_width=True,
                        key="btn_ajuste_t",
                    ):
                        if len(motivo_t) >= 5:
                            # Guardamos los datos del EDITOR (df_editable_t)
                            exito, mensaje = guardar_en_historial(
                                df_editable_t,
                                "Tarde",
                                st.session_state.get("usuario", "Admin"),
                                motivo_t,
                            )
                            if exito:
                                st.success("Ajuste de tarde registrado correctamente.")
                                st.rerun()
                        else:
                            st.warning("Escriba un motivo de al menos 5 caracteres.")

            # 2. Confirmación normal (Primera vez)
            elif not esta_confirmado_t:
                if st.button(
                    "✅ Confirmar Producción Tarde",
                    use_container_width=True,
                    key="btn_conf_t",
                ):
                    exito, mensaje = guardar_en_historial(
                        df_t, "Tarde", st.session_state.get("usuario", "Admin")
                    )
                    if exito:
                        st.success(mensaje)
                        st.session_state["confirmado_t"] = True
                        st.rerun()
                    else:
                        st.error(mensaje)

            # 3. Vista para usuario no-admin
            else:
                st.info("✅ Producción de la tarde cerrada.")

        with col_pdf_t:
            if esta_confirmado_t:
                pdf_bytes_t = generar_pdf_produccion(df_t, "Tarde")
                st.download_button(
                    label="📥 Descargar PDF Tarde",
                    data=pdf_bytes_t,
                    file_name=f"plan_tarde_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_pdf_t",
                )
            else:
                st.info("⚠️ Confirmar para descargar PDF.")
    else:
        st.warning("No hay producción programada para el turno tarde.")

if st.session_state.perfil == "admin":
    with tabs[4]:  # Pestaña de Estadísticas y Ajustes
        st.header("📊 Panel de Control y Estadísticas")

        # --- SECCIÓN 1: MÉTRICAS Y GRÁFICOS ---
        if os.path.exists("data/historial_produccion.csv"):
            df_hist = pd.read_csv("data/historial_produccion.csv")

            # Convertimos la columna Fecha a objeto datetime para poder filtrar correctamente
            df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"]).dt.date

            # --- FILTROS INTERACTIVOS ---
            col_f1, col_f2, col_f3 = st.columns([1, 1, 2])

            with col_f1:
                opcion_turno = st.selectbox(
                    "Filtrar por Turno:",
                    ["Total Día", "Mañana", "Tarde"],
                    key="filtro_turno_stats",
                )

            with col_f2:
                productos = ["Todos"] + sorted(df_hist["TIPO DE PAN"].unique().tolist())
                opcion_prod = st.selectbox(
                    "Filtrar por Producto:", productos, key="filtro_prod_stats"
                )

            with col_f3:
                # Selectores individuales para evitar "presets" en inglés
                hoy = datetime.now().date()
                hace_una_semana = hoy - timedelta(days=7)

                c_ini, c_fin = st.columns(2)
                with c_ini:
                    f_inicio = st.date_input(
                        "Desde:",
                        hace_una_semana,
                        max_value=hoy,
                        format="DD/MM/YYYY",
                        key="f_ini_manual",
                    )
                with c_fin:
                    f_fin = st.date_input(
                        "Hasta:",
                        hoy,
                        max_value=hoy,
                        format="DD/MM/YYYY",
                        key="f_fin_manual",
                    )

            # --- PROCESAMIENTO DE DATOS ---
            df_filtrado = df_hist.copy()

            # 1. Filtro de Fechas (Usando las variables de los selectores individuales)
            df_filtrado = df_filtrado[
                (df_filtrado["Fecha"] >= f_inicio) & (df_filtrado["Fecha"] <= f_fin)
            ]

            # 2. Filtro de Turno
            if opcion_turno != "Total Día":
                df_filtrado = df_filtrado[df_filtrado["Turno"] == opcion_turno]

            # 3. Filtro de Producto
            if opcion_prod != "Todos":
                df_filtrado = df_filtrado[df_filtrado["TIPO DE PAN"] == opcion_prod]

            # --- MÉTRICAS Y VISUALIZACIÓN ---
            if not df_filtrado.empty:
                # Agrupación para métricas
                df_resumen_diario = (
                    df_filtrado.groupby("Fecha")["MASAS"].sum().reset_index()
                )

                m1, m2, m3 = st.columns(3)
                total_masas = df_filtrado["MASAS"].sum()
                promedio = (
                    df_resumen_diario["MASAS"].mean()
                    if not df_resumen_diario.empty
                    else 0
                )

                m1.metric("Producción Total", f"{total_masas:.1f} Masas")
                m2.metric("Promedio Diario", f"{promedio:.1f}")
                m3.metric("Días en el Rango", len(df_resumen_diario))

                st.subheader(f"Evolución de Producción: {opcion_turno}")

                # Gráfico de Barras Apiladas
                df_grafico = (
                    df_filtrado.groupby(["Fecha", "TIPO DE PAN"])["MASAS"]
                    .sum()
                    .reset_index()
                )

                st.bar_chart(
                    data=df_grafico,
                    x="Fecha",
                    y="MASAS",
                    color="TIPO DE PAN",
                    use_container_width=True,
                )

                # --- RANKING ---
                st.subheader("🏆 Ranking de Elaboración (Período Seleccionado)")
                df_ranking = (
                    df_filtrado.groupby("TIPO DE PAN")["MASAS"]
                    .sum()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                st.dataframe(df_ranking, use_container_width=True, hide_index=True)

                # --- AUDITORÍA PARA ADMIN ---
                perfil_actual = (
                    str(st.session_state.get("perfil", st.session_state.get("rol", "")))
                    .lower()
                    .strip()
                )
                if perfil_actual in ["admin", "none", ""]:
                    with st.expander("📝 Ver Auditoría (Ajustes y Comentarios)"):
                        st.dataframe(
                            df_filtrado[
                                [
                                    "Fecha",
                                    "Turno",
                                    "TIPO DE PAN",
                                    "MASAS",
                                    "Usuario",
                                    "Comentario",
                                ]
                            ].sort_values(by=["Fecha", "Turno"], ascending=False),
                            use_container_width=True,
                            hide_index=True,
                        )
            else:
                st.info(
                    "No hay datos para los filtros o el rango de fechas seleccionados."
                )
        else:
            st.info("Aún no hay datos históricos para mostrar estadísticas.")

        st.markdown("---")

        # --- SECCIÓN 2: AJUSTES MAESTROS ---
        with st.expander("⚙️ Configuración de Ajustes Maestros"):
            st.write("Modifique los umbrales críticos, medios y altos aquí:")
            edit_maestro = st.data_editor(
                st.session_state.df_ajustes,
                key="editor_maestro",
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Tope 1 (Crítico)": st.column_config.NumberColumn(format="%d"),
                    "Producir 1": st.column_config.NumberColumn(format="%d"),
                    "Tope 2 (Medio)": st.column_config.NumberColumn(format="%d"),
                    "Producir 2": st.column_config.NumberColumn(format="%d"),
                    "Tope 3 (Alto)": st.column_config.NumberColumn(format="%d"),
                    "Producir 3": st.column_config.NumberColumn(format="%d"),
                },
            )
            if st.button("💾 Guardar Ajustes Maestros", use_container_width=True):
                guardar_ajustes(edit_maestro)
                st.success("Ajustes maestros actualizados correctamente.")

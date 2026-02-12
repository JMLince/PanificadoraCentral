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
st.set_page_config(page_title="Panificadora Central v2.5", layout="wide")

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

st.title(f"🍞 Gestión de Producción y Stock v2.5 PRO")

# --- 2. PANEL DE CONTROL (SIDEBAR) ---
with st.sidebar:
    st.write(f"👤 **Perfil:** {st.session_state.perfil.upper()}")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    st.divider()

    # --- LÓGICA DE BLOQUEO POR PERFIL ---
    perfil_actual = st.session_state.perfil
    # Bloqueamos para Encargado (por auditoría) y para Panadero (por jerarquía)
    bloquear_controles = perfil_actual in ["encargado", "panadero"]

    if perfil_actual == "encargado":
        st.info("📋 Modo Lectura: Parámetros fijos para supervisión.")
    elif perfil_actual == "panadero":
        st.warning("🔒 Parámetros de producción definidos por administración.")

    # --- CONTROLES DE PARÁMETROS ---
    p_inc = st.number_input(
        "Factor Incremento RPD (%)", value=17, disabled=bloquear_controles
    )

    dias_esp = st.multiselect(
        "Días de incremento",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        default=["Tuesday"],
        disabled=bloquear_controles,
    )

    p_manana = st.slider(
        "Porcentaje Turno Mañana", 0, 100, 60, disabled=bloquear_controles
    )

    st.divider()

    # Solo mostramos el botón de detener sistema al Administrador
    if perfil_actual == "admin":
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
                            <p style="font-size: 1.1rem; margin: 15px 0; color: #555;">El sistema <b>v2.5</b> se ha detenido.</p>
                            <div style="height: 1px; background: #eee; margin: 15px 0;"></div>
                            <p style="font-size: 0.9rem; color: #888;">Ya puede cerrar esta pestaña con seguridad.</p>
                        </div>`;
                    window.parent.document.body.appendChild(div);
                </script>
                """,
                height=0,
            )
            import time, os, signal

            time.sleep(1)
            os.kill(os.getpid(), signal.SIGTERM)

# ========================================================
# --- DEFINICIÓN DINÁMICA DE PESTAÑAS ---
# ========================================================
perfil = st.session_state.get("perfil", "panadero")

if perfil == "admin":
    titulos_tabs = [
        "📦 Stock/Pedidos",
        "📋 Plan Total",
        "🌅 Mañana",
        "🌇 Tarde",
        "📊 Estadísticas",
        "⚙️ Ajustes",
    ]
elif perfil == "encargado":
    titulos_tabs = [
        "📦 Stock/Pedidos",
        "📋 Plan Total",
        "🌅 Mañana",
        "🌇 Tarde",
        "📊 Estadísticas",
    ]
else:
    # Panadero/Operario
    titulos_tabs = ["📦 Stock/Pedidos", "📋 Plan Total", "🌅 Mañana", "🌇 Tarde"]

tabs = st.tabs(titulos_tabs)

# ========================================================
# PESTAÑA 0: STOCK Y PEDIDOS (Todos)
# ========================================================
with tabs[0]:
    # --- 1. LÓGICA DE PERSISTENCIA Y BLOQUEO ---
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_hist_stock = "data/historial_stock.csv"

    ya_cargado = False
    df_valores_previos = None

    if os.path.exists(archivo_hist_stock):
        h_stock = pd.read_csv(archivo_hist_stock)
        hoy_data = h_stock[h_stock["Fecha"].astype(str) == fecha_hoy]
        if not hoy_data.empty:
            ya_cargado = True
            ultima_hora = hoy_data["Hora"].max()
            df_valores_previos = hoy_data[hoy_data["Hora"] == ultima_hora]

    perfil_actual = st.session_state.get("perfil", "panadero")
    es_admin = perfil_actual == "admin"
    es_encargado = perfil_actual == "encargado"

    bloquear_stock = ya_cargado and not es_admin
    bloquear_todo_encargado = es_encargado

    if ya_cargado:
        st.success(f"📌 Stock inicial registrado para hoy: {fecha_hoy}")
        if es_admin:
            st.warning(
                "🔓 Modo Administrador: Puedes corregir el stock y volver a guardar."
            )
        elif es_encargado:
            st.info(
                "📋 Perfil Encargado: Visualización de stock y pedidos habilitada para supervisión."
            )

    # --- 2. TABLAS DE DATOS (RPD y PA) ---
    col_rpd, col_pa = st.columns(2)

    with col_rpd:
        st.subheader("Stock RPD")
        df_rpd_in = st.session_state.df_ajustes[["Masa Base"]].copy()

        if ya_cargado and df_valores_previos is not None:
            rpd_saved = df_valores_previos[df_valores_previos["Origen"] == "RPD"]
            df_rpd_in = df_rpd_in.merge(
                rpd_saved[["Producto", "Cantidad"]],
                left_on="Masa Base",
                right_on="Producto",
                how="left",
            )
            df_rpd_in["Stock Actual"] = df_rpd_in["Cantidad"].fillna(0).astype(int)
            df_rpd_in = df_rpd_in.drop(
                columns=[c for c in ["Producto", "Cantidad"] if c in df_rpd_in.columns]
            )
        else:
            df_rpd_in["Stock Actual"] = 0

        es_panadero = st.session_state.perfil == "panadero"

        edit_rpd = st.data_editor(
            df_rpd_in,
            key="editor_rpd",
            hide_index=True,
            use_container_width=True,
            disabled=bloquear_stock or bloquear_todo_encargado or es_panadero,
            column_config={
                "Masa Base": st.column_config.TextColumn("Masa Base", disabled=True),
                "Stock Actual": st.column_config.NumberColumn(
                    "Stock Actual",
                    format="%d",
                    min_value=0,
                    disabled=bloquear_stock or bloquear_todo_encargado or es_panadero,
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

        # --- LÓGICA DE CARGA BLINDADA (STOCK + DEMANDA) ---
        if ya_cargado and df_valores_previos is not None:
            # 1. Filtramos solo los registros de PA del historial
            pa_saved = df_valores_previos[df_valores_previos["Origen"] == "PA"].copy()

            # 2. Unimos por Producto trayendo Cantidad (Stock) y Demanda
            # Nota: Usamos los nombres de columna tal cual están en tu CSV de historial
            df_pa_in = df_pa_in.merge(
                pa_saved[["Producto", "Cantidad", "Demanda"]], on="Producto", how="left"
            )

            # 3. Asignamos valores y limpiamos columna temporal 'Cantidad'
            df_pa_in["Stock Inicial"] = df_pa_in["Cantidad"].fillna(0).astype(int)
            df_pa_in["Demanda"] = df_pa_in["Demanda"].fillna(0).astype(int)
            df_pa_in = df_pa_in.drop(columns=["Cantidad"])
        else:
            # Si es la primera carga del día, todo inicia en 0
            df_pa_in["Stock Inicial"] = 0
            df_pa_in["Demanda"] = 0

        # --- EDITOR DE DATOS ---
        edit_pa = st.data_editor(
            df_pa_in,
            key="editor_pa",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Masa Base": st.column_config.TextColumn("Masa Base", disabled=True),
                "Producto": st.column_config.TextColumn("Producto", disabled=True),
                "Stock Inicial": st.column_config.NumberColumn(
                    "Stock Inicial",
                    format="%d",
                    min_value=0,
                    disabled=bloquear_stock or bloquear_todo_encargado or es_panadero,
                ),
                "Demanda": st.column_config.NumberColumn(
                    "Demanda",
                    format="%d",
                    min_value=0,
                    disabled=bloquear_stock or bloquear_todo_encargado or es_panadero,
                ),
            },
        )

    st.divider()
    # --- MODIFICADO: Solo Admin o Encargado (si no está cargado) pueden ver esto ---
    # El panadero queda excluido de la condición
    if (not ya_cargado or es_admin) and not es_encargado and not es_panadero:
        col_btn, col_txt = st.columns([1, 2])
        with col_txt:
            comentario_stock = ""
            if es_admin and ya_cargado:
                comentario_stock = st.text_input(
                    "📝 Motivo del ajuste de stock:",
                    placeholder="Ej: Conteo manual corregido...",
                    key="audit_comment",
                )

        with col_btn:
            label_boton = (
                "💾 Guardar Stock Inicial"
                if not ya_cargado
                else "🔄 Actualizar Stock (Admin)"
            )
            if st.button(label_boton, use_container_width=True, type="primary"):
                if es_admin and ya_cargado and len(comentario_stock) < 5:
                    st.error(
                        "⚠️ Ingrese un motivo válido para el ajuste (mín. 5 caracteres)."
                    )
                else:
                    from src.utils import guardar_historial_stock

                    exito = guardar_historial_stock(
                        edit_rpd,
                        edit_pa,
                        st.session_state.get("usuario", "Usuario"),
                        comentario_stock,
                    )
                    if exito:
                        st.success("✅ Stock registrado exitosamente.")
                        st.rerun()

    # Mensaje informativo para el Panadero
    elif es_panadero:
        st.info("💡 Los datos de Stock y Pedidos son de solo lectura para su perfil.")

# ========================================================
# MOTOR DE CÁLCULO (Se ejecuta siempre antes de las pestañas de producción)
# ========================================================
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


# ========================================================
# PESTAÑA 1: PLAN TOTAL
# ========================================================
with tabs[1]:
    renderizar(df_final, "TOTAL", "Plan Total")
    df_total = df_final[df_final["TOTAL"] > 0][
        ["Masa Base", "TOTAL", "Peso Corte", "Tapa"]
    ]
    if not df_total.empty:
        df_total.columns = ["TIPO DE PAN", "MASAS", "CORTE", "TAPA"]
        pdf_bytes_total = generar_pdf_produccion(df_total, "Total del Día")
        st.download_button(
            label="📥 Descargar Plan Total (PDF)",
            data=pdf_bytes_total,
            file_name=f"plan_total_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ========================================================
# PESTAÑA 2: MAÑANA
# ========================================================
with tabs[2]:
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists("data/historial_produccion.csv"):
        hist = pd.read_csv("data/historial_produccion.csv")
        if not hist[(hist["Fecha"] == fecha_hoy) & (hist["Turno"] == "Mañana")].empty:
            st.session_state["confirmado_m"] = True

    df_final["M"] = (df_final["TOTAL"] * (p_manana / 100)).apply(aplicar_redondeo)
    renderizar(df_final, "M", "Turno Mañana")
    df_m = df_final[df_final["M"] > 0][["Masa Base", "M", "Peso Corte", "Tapa"]]

    if not df_m.empty:
        df_m.columns = ["TIPO DE PAN", "MASAS", "CORTE", "TAPA"]
        st.markdown("---")
        col_conf, col_pdf = st.columns(2)
        perfil_actual = str(st.session_state.get("perfil", "")).lower().strip()
        esta_confirmado = st.session_state.get("confirmado_m", False)

        with col_conf:
            if esta_confirmado and perfil_actual == "admin":
                with st.expander("⚠️ Corregir Producción Mañana", expanded=True):
                    df_editable_m = st.data_editor(
                        df_m,
                        hide_index=True,
                        key="editor_m",
                        column_config={
                            "TIPO DE PAN": st.column_config.TextColumn(disabled=True),
                            "MASAS": st.column_config.NumberColumn(
                                min_value=0, step=0.5
                            ),
                        },
                    )
                    motivo = st.text_input("Motivo del cambio:", key="txt_motivo_m")
                    if st.button(
                        "Confirmar Ajuste Autorizado",
                        type="primary",
                        use_container_width=True,
                    ):
                        if len(motivo) >= 5:
                            exito, _ = guardar_en_historial(
                                df_editable_m,
                                "Mañana",
                                st.session_state.get("usuario", "Admin"),
                                motivo,
                            )
                            if exito:
                                st.rerun()

            elif not esta_confirmado:
                # --- CAMBIO AQUÍ: Solo Admin y Encargado ven el botón ---
                if st.session_state.perfil in ["admin", "encargado"]:
                    if st.button(
                        "✅ Confirmar Producción Mañana",
                        use_container_width=True,
                        key="btn_conf_m",
                    ):
                        exito, mensaje = guardar_en_historial(
                            df_m, "Mañana", st.session_state.get("usuario", "Admin")
                        )
                        if exito:
                            st.session_state["confirmado_m"] = True
                            st.rerun()
                else:
                    # Mensaje para el Panadero
                    st.warning(
                        "⏳ Esperando confirmación de un supervisor para cerrar este turno."
                    )

            else:
                st.info("✅ Producción cerrada.")

        with col_pdf:
            if esta_confirmado:
                pdf_bytes = generar_pdf_produccion(df_m, "Mañana")
                st.download_button(
                    label="📥 Descargar PDF Mañana",
                    data=pdf_bytes,
                    file_name=f"plan_m.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

# ========================================================
# PESTAÑA 3: TARDE
# ========================================================
with tabs[3]:
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists("data/historial_produccion.csv"):
        hist = pd.read_csv("data/historial_produccion.csv")
        if not hist[(hist["Fecha"] == fecha_hoy) & (hist["Turno"] == "Tarde")].empty:
            st.session_state["confirmado_t"] = True

    df_final["T"] = (df_final["TOTAL"] - df_final.get("M", 0)).apply(aplicar_redondeo)
    renderizar(df_final, "T", "Turno Tarde")
    df_t = df_final[df_final["T"] > 0][["Masa Base", "T", "Peso Corte", "Tapa"]]

    if not df_t.empty:
        df_t.columns = ["TIPO DE PAN", "MASAS", "CORTE", "TAPA"]
        st.markdown("---")
        col_conf_t, col_pdf_t = st.columns(2)
        esta_confirmado_t = st.session_state.get("confirmado_t", False)

        with col_conf_t:
            if esta_confirmado_t and perfil_actual == "admin":
                with st.expander("⚠️ Corregir Producción Tarde", expanded=True):
                    df_editable_t = st.data_editor(
                        df_t,
                        hide_index=True,
                        key="editor_t",
                        column_config={
                            "TIPO DE PAN": st.column_config.TextColumn(disabled=True),
                            "MASAS": st.column_config.NumberColumn(
                                min_value=0, step=0.5
                            ),
                        },
                    )
                    motivo = st.text_input("Motivo del cambio:", key="txt_motivo_t")
                    if st.button(
                        "Confirmar Ajuste Autorizado",
                        type="primary",
                        use_container_width=True,
                    ):
                        if len(motivo) >= 5:
                            exito, _ = guardar_en_historial(
                                df_editable_t,
                                "Tarde",
                                st.session_state.get("usuario", "Admin"),
                                motivo,
                            )
                            if exito:
                                st.rerun()

            elif not esta_confirmado:
                # --- CAMBIO AQUÍ: Solo Admin y Encargado ven el botón ---
                if st.session_state.perfil in ["admin", "encargado"]:
                    if st.button(
                        "✅ Confirmar Producción Tarde",
                        use_container_width=True,
                        key="btn_conf_t",
                    ):
                        exito, mensaje = guardar_en_historial(
                            df_t, "Tarde", st.session_state.get("usuario", "Admin")
                        )
                        if exito:
                            st.session_state["confirmado_t"] = True
                            st.rerun()
                else:
                    # Mensaje para el Panadero
                    st.warning(
                        "⏳ Esperando confirmación de un supervisor para cerrar este turno."
                    )

            else:
                st.info("✅ Producción cerrada.")

        with col_pdf_t:
            if esta_confirmado_t:
                pdf_t = generar_pdf_produccion(df_t, "Tarde")
                st.download_button(
                    label="📥 Descargar PDF Tarde",
                    data=pdf_t,
                    file_name=f"plan_t.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

# ========================================================
# PESTAÑA 4: ESTADÍSTICAS (Admin y Encargado)
# ========================================================
if perfil in ["admin", "encargado"]:
    with tabs[4]:
        st.header("📊 Panel de Control y Auditoría")

        # --- SECCIÓN 1: PRODUCCIÓN (Masas) ---
        if os.path.exists("data/historial_produccion.csv"):
            st.subheader("📈 Histórico de Producción")
            df_hist = pd.read_csv("data/historial_produccion.csv")
            df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"]).dt.date

            # Filtros de Producción
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                op_turno = st.selectbox(
                    "Turno:", ["Total Día", "Mañana", "Tarde"], key="f_t"
                )
            with c2:
                op_prod = st.selectbox(
                    "Producto:",
                    ["Todos"] + sorted(df_hist["TIPO DE PAN"].unique().tolist()),
                    key="f_p",
                )
            with c3:
                f_ini = st.date_input(
                    "Desde:",
                    datetime.now().date() - timedelta(days=7),
                    key="f_i",
                    max_value=datetime.now().date(),
                )
                f_fin = st.date_input(
                    "Hasta:",
                    datetime.now().date(),
                    key="f_f",
                    max_value=datetime.now().date(),
                )

            df_filtro = df_hist[
                (df_hist["Fecha"] >= f_ini) & (df_hist["Fecha"] <= f_fin)
            ].copy()

            if op_turno != "Total Día":
                df_filtro = df_filtro[df_filtro["Turno"] == op_turno]
            if op_prod != "Todos":
                df_filtro = df_filtro[df_filtro["TIPO DE PAN"] == op_prod]

            # MEJORA: Validación de datos existentes tras el filtrado
            if not df_filtro.empty:
                st.metric("Total Masas Producidas", f"{df_filtro['MASAS'].sum():.1f}")

                cols_prod = [
                    c
                    for c in [
                        "Fecha",
                        "Hora",
                        "Turno",
                        "TIPO DE PAN",
                        "MASAS",
                        "Usuario",
                        "Comentario",
                    ]
                    if c in df_filtro.columns
                ]
                st.dataframe(
                    df_filtro[cols_prod].sort_values(
                        by=["Fecha", "Hora"], ascending=False
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "No existen datos para mostrar según fechas seleccionadas."
                )  # <--- Mensaje solicitado

        st.divider()

        # --- SECCIÓN 2: AUDITORÍA DE STOCK INICIAL ---
        st.subheader("📋 Auditoría de Stock y Pedidos (PA/RPD)")
        if os.path.exists("data/historial_stock.csv"):
            df_s = pd.read_csv("data/historial_stock.csv")
            df_s["Fecha"] = pd.to_datetime(df_s["Fecha"]).dt.date

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                f_stock_ini = st.date_input(
                    "Stock desde:",
                    datetime.now().date() - timedelta(days=3),
                    key="s_ini",
                    max_value=datetime.now().date(),
                )
            with col_s2:
                f_stock_fin = st.date_input(
                    "Stock hasta:",
                    datetime.now().date(),
                    key="s_fin",
                    max_value=datetime.now().date(),
                )

            df_s_filtrado = df_s[
                (df_s["Fecha"] >= f_stock_ini) & (df_s["Fecha"] <= f_stock_fin)
            ].copy()

            if not df_s_filtrado.empty:
                st.dataframe(
                    df_s_filtrado.sort_values(by=["Fecha", "Hora"], ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "No existen datos de stock para mostrar según fechas seleccionadas."
                )

# ========================================================
# PESTAÑA 5: AJUSTES MAESTROS (Solo Admin)
# ========================================================
if perfil == "admin":
    with tabs[5]:
        st.header("⚙️ Configuración Maestra")
        st.warning("⚠️ Solo personal autorizado.")
        edit_m = st.data_editor(
            st.session_state.df_ajustes,
            key="ed_maestro",
            hide_index=True,
            use_container_width=True,
        )
        if st.button(
            "💾 Guardar Cambios Maestros", type="primary", use_container_width=True
        ):
            from src.utils import guardar_ajustes

            guardar_ajustes(edit_m)
            st.success("Ajustes actualizados.")

import streamlit as st
import pandas as pd
import os
import signal
import time
from datetime import datetime, timedelta, date

# st.cache_data.clear() -- comentada para prueba con carga aj. maestros

# IMPORTACIONES MODULARES DESDE TU CARPETA SRC
from src.utils import (
    aplicar_redondeo,
    guardar_en_historial,
    reservar_pedido,
    anular_pedido,
)
from src.config_manager import cargar_ajustes, guardar_ajustes
from src.auth import generar_login
from src.report_generator import generar_pdf_produccion, exportar_pedido_pdf

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

    /* Forzar visibilidad de checkboxes y radio buttons en cualquier tabla o editor */
    [data-testid="stDataFrameDataLayer"] [role="gridcell"] button,
    [data-testid="stDataFrameDataLayer"] [role="gridcell"] input,
    div[data-baseweb="checkbox"] {
        opacity: 1 !important;
        visibility: visible !important;
    }
    /* Asegurar que la primera columna (donde suele estar el selector) sea siempre opaca */
    [data-testid="stDataFrameDataLayer"] [aria-colindex="1"] {
        opacity: 1 !important;
    }
    /* Forzar visibilidad del botón "+" de añadir fila */
    [data-testid="stDataFrameDynamicControls"] button {
        opacity: 1 !important;
        visibility: visible !important;
        background-color: rgba(255, 255, 255, 0.1) !important; /* Un fondo suave para que resalte */
    }
    /* Forzar visibilidad de la papelera en las filas */
    [data-testid="stDataFrameDataLayer"] button[title="Delete row"],
    [data-testid="stDataFrameDataLayer"] button[aria-label="Delete row"] {
        opacity: 1 !important;
        visibility: visible !important;
        color: #ff4b4b !important; /* Rojo para identificar borrado */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- CARGA DE DATOS ---
if "df_ajustes" not in st.session_state:
    st.session_state.df_ajustes = cargar_ajustes()
    # Asegurar limpieza de espacios en "Masa Base" al cargar
    if "Masa Base" in st.session_state.df_ajustes.columns:
        st.session_state.df_ajustes["Masa Base"] = (
            st.session_state.df_ajustes["Masa Base"].astype(str).str.strip()
        )

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
# Limpiar espacios en "Masa Base" desde el inicio para evitar errores de sincronización
df_base["Masa Base"] = df_base["Masa Base"].astype(str).str.strip()

st.title(f"🍞 Gestión de Producción y Stock v2.5 PRO")

# --- 2. PANEL DE CONTROL (SIDEBAR) ---
with st.sidebar:
    st.write(
        f"👤 **Perfil:** {st.session_state.authenticator.get_user_profile().upper()}"
    )
    st.divider()

    # --- LÓGICA DE BLOQUEO POR PERFIL ---
    perfil_actual = st.session_state.authenticator.get_user_profile()
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
        "👥 Clientes",
        "📝 Carga Pedidos",  # <--- Nueva pestaña (Índice 7)
    ]
elif perfil == "encargado":
    titulos_tabs = [
        "📦 Stock/Pedidos",
        "📋 Plan Total",
        "🌅 Mañana",
        "🌇 Tarde",
        "📊 Estadísticas",
        "👥 Clientes",  # <--- También para el encargado si quieres que cargue pedidos
    ]
else:
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
        # Limpiar espacios en "Masa Base" para evitar errores de sincronización
        df_rpd_in["Masa Base"] = df_rpd_in["Masa Base"].astype(str).str.strip()

        if ya_cargado and df_valores_previos is not None:
            rpd_saved = df_valores_previos[df_valores_previos["Origen"] == "RPD"].copy()
            # Limpiar espacios en "Producto" antes del merge
            rpd_saved["Producto"] = rpd_saved["Producto"].astype(str).str.strip()
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

        es_panadero = st.session_state.authenticator.get_user_profile() == "panadero"

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
        # Limpiar espacios en "Masa Base" y "Producto" para evitar errores de sincronización
        df_pa_in["Masa Base"] = df_pa_in["Masa Base"].astype(str).str.strip()
        df_pa_in["Producto"] = df_pa_in["Producto"].astype(str).str.strip()

        # --- LÓGICA DE CARGA BLINDADA (STOCK + DEMANDA) ---
        if ya_cargado and df_valores_previos is not None:
            # 1. Filtramos solo los registros de PA del historial
            pa_saved = df_valores_previos[df_valores_previos["Origen"] == "PA"].copy()
            # Limpiar espacios en "Producto" antes del merge
            pa_saved["Producto"] = pa_saved["Producto"].astype(str).str.strip()

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

# --- LIMPIEZA Y SINCRONIZACIÓN DE DATOS ---
# Aplicar strip() a "Masa Base" para evitar errores con espacios (ej: 'BLANCO LARGO')
edit_rpd_clean = edit_rpd.copy()
edit_rpd_clean["Masa Base"] = edit_rpd_clean["Masa Base"].astype(str).str.strip()

df_ajustes_clean = st.session_state.df_ajustes.copy()
df_ajustes_clean["Masa Base"] = df_ajustes_clean["Masa Base"].astype(str).str.strip()

# Merge evitando duplicación de columnas: solo traemos las columnas necesarias de df_ajustes
# excluyendo "Masa Base" que ya está en edit_rpd_clean
columnas_ajustes = [col for col in df_ajustes_clean.columns if col != "Masa Base"]
df_rpd_calc = pd.merge(
    edit_rpd_clean[["Masa Base", "Stock Actual"]],
    df_ajustes_clean[["Masa Base"] + columnas_ajustes],
    on="Masa Base",
    how="inner",
)


def logica_t(row):
    s = row.get("Stock Actual", 0)

    # Usamos .get() para evitar el KeyError si la columna falta o cambia de nombre
    t1 = row.get("Tope 1 (critico)", 0)
    t2 = row.get("Tope 2 (Medio)", 0)
    t3 = row.get("Tope 3 (Alto)", 0)

    p1 = row.get("Producir 1", 0)
    p2 = row.get("Producir 2", 0)
    p3 = row.get("Producir 3", 0)

    if s <= t1:
        return p1
    if s <= t2:
        return p2
    if s <= t3:
        return p3
    return 0


df_rpd_calc["Unidades"] = df_rpd_calc.apply(logica_t, axis=1)

# Limpiar espacios en df_base antes del merge
df_base_clean = df_base.copy()
df_base_clean["Masa Base"] = df_base_clean["Masa Base"].astype(str).str.strip()
df_rpd_calc = pd.merge(
    df_rpd_calc, df_base_clean[["Masa Base", "Cant_Batch"]], on="Masa Base", how="left"
)
df_rpd_calc["Batches_RPD"] = (
    df_rpd_calc["Unidades"] / df_rpd_calc["Cant_Batch"]
) * factor

edit_pa["Neto"] = (edit_pa["Demanda"] - edit_pa["Stock Inicial"]).clip(lower=0)
# Limpiar espacios en "Masa Base" antes de agrupar
edit_pa_clean = edit_pa.copy()
edit_pa_clean["Masa Base"] = edit_pa_clean["Masa Base"].astype(str).str.strip()
pa_agrupado = edit_pa_clean.groupby("Masa Base").agg({"Neto": "sum"}).reset_index()
pa_agrupado = pd.merge(
    pa_agrupado, df_base_clean[["Masa Base", "Cant_Batch"]], on="Masa Base", how="left"
)
pa_agrupado["Batches_PA"] = pa_agrupado["Neto"] / pa_agrupado["Cant_Batch"].fillna(1)

df_final = df_base_clean[["Masa Base", "Peso Corte", "Tapa"]].copy()
# Asegurar que df_rpd_calc y pa_agrupado también tienen "Masa Base" limpio
df_rpd_calc["Masa Base"] = df_rpd_calc["Masa Base"].astype(str).str.strip()
pa_agrupado["Masa Base"] = pa_agrupado["Masa Base"].astype(str).str.strip()
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
                if st.session_state.authenticator.get_user_profile() in [
                    "admin",
                    "encargado",
                ]:
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
                        key="btn_ajuste_tarde",
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

            elif not esta_confirmado_t:
                # --- CAMBIO AQUÍ: Solo Admin y Encargado ven el botón ---
                if st.session_state.authenticator.get_user_profile() in [
                    "admin",
                    "encargado",
                ]:
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

                # --- LÓGICA DE MAQUILLAJE VISUAL ---
                def estilado_auditoria(row):
                    estilo = [""] * len(row)
                    val = row["MASAS"]
                    coment = str(row["Comentario"])

                    # 1. Ajuste Negativo (Descuento): Rojo + Negrita
                    if val < 0:
                        estilo = ["color: #FF4B4B; font-weight: bold;"] * len(row)
                    # 2. Ajuste Positivo (Incremento): Verde + Negrita
                    elif "AJUSTE" in coment and val > 0:
                        estilo = ["color: #09AB3B; font-weight: bold;"] * len(row)

                    return estilo

                # Preparamos el DataFrame ordenado
                df_mostrar = df_filtro[cols_prod].sort_values(
                    by=["Fecha", "Hora"], ascending=False
                )

                # Aplicamos el estilo
                df_estilado = df_mostrar.style.apply(estilado_auditoria, axis=1).format(
                    subset=["MASAS"], formatter="{:.1f}"
                )

                st.write("**Detalle de Auditoría de Movimientos:**")
                st.dataframe(
                    df_estilado,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No existen datos para mostrar según fechas seleccionadas.")

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

        st.divider()

        # --- SECCIÓN 3: HISTORIAL DE PEDIDOS ANULADOS ---
        st.subheader("🗑️ Historial de Pedidos Anulados")

        ruta_pedidos = "data/pedidos.csv"
        if os.path.exists(ruta_pedidos):
            df_pedidos = pd.read_csv(ruta_pedidos)

            # Filtrar solo pedidos anulados
            df_anulados = df_pedidos[df_pedidos["Estado"] == "Anulado"].copy()

            if not df_anulados.empty:
                # Preparar columnas para visualización
                df_anulados["Fecha_Registro"] = pd.to_datetime(
                    df_anulados["Fecha_Registro"], errors="coerce"
                ).dt.strftime("%Y-%m-%d %H:%M")

                # Seleccionar columnas de cabecera sin detalles de productos
                df_auditoria_anulados = df_anulados[
                    ["ID_Pedido", "Cliente", "Fecha_Registro", "Estado"]
                ].copy()

                # Eliminar duplicados por ID_Pedido para que solo aparezca una fila por pedido
                df_auditoria_anulados = df_auditoria_anulados.drop_duplicates(
                    subset=["ID_Pedido"], keep="first"
                )

                df_auditoria_anulados.columns = [
                    "ID Pedido",
                    "Cliente",
                    "Fecha",
                    "Estado",
                ]

                # Ordenar por fecha descendente
                df_auditoria_anulados = df_auditoria_anulados.sort_values(
                    by="Fecha", ascending=False
                ).reset_index(drop=True)

                # Mostrar en expander con estilos históricos
                with st.expander(
                    "📋 Ver Registro Histórico de Anulaciones", expanded=False
                ):
                    st.markdown(
                        """
                    <style>
                    .historial-anulados {
                        background-color: rgba(200, 200, 200, 0.1);
                        border-left: 4px solid #FF6B6B;
                        padding: 10px;
                        border-radius: 5px;
                        font-size: 0.9em;
                    }
                    </style>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.info(
                        "📌 Este registro contiene todos los pedidos anulados. "
                        "Los datos se mantienen para auditoría y no afectan operaciones activas."
                    )

                    # Métrica de pedidos anulados (contar solo pedidos únicos)
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric(
                            "Pedidos Anulados (Únicos)", len(df_auditoria_anulados)
                        )
                    with col_m2:
                        st.metric("Total de Ítems Anulados", len(df_anulados))

                    # Tabla compacta con estilos históricos
                    st.dataframe(
                        df_auditoria_anulados,
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Opción de descarga
                    csv_anulados = df_auditoria_anulados.to_csv(
                        index=False, encoding="utf-8"
                    )
                    st.download_button(
                        label="⬇️ Descargar Historial (CSV)",
                        data=csv_anulados,
                        file_name=f"pedidos_anulados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            else:
                st.info("✅ No hay pedidos anulados registrados en el sistema.")
        else:
            st.warning("⚠️ El archivo de pedidos no se encontró.")

# ========================================================
# PESTAÑA 5: AJUSTES MAESTROS (Solo Admin)
# ========================================================

if perfil == "admin":
    with tabs[5]:
        st.header("⚙️ Configuración Maestra")
        st.warning("⚠️ Solo personal autorizado.")
        # reordenar columnas para que "Tope 1 (critico)" sea la segunda
        df_display = st.session_state.df_ajustes.copy()
        if not df_display.empty:
            desired_order = ["Masa Base", "Tope 1 (critico)", "Producir 1"]
            cols = [c for c in desired_order if c in df_display.columns]
            cols += [c for c in df_display.columns if c not in cols]
            df_display = df_display[cols]
        edit_m = st.data_editor(
            df_display,
            key="ed_maestro",
            hide_index=True,
            use_container_width=True,
        )
        if st.button(
            "💾 Guardar Cambios Maestros", type="primary", use_container_width=True
        ):
            from src.config_manager import guardar_ajustes

            # Guardar en archivo permanente
            guardar_ajustes(edit_m)

            # Actualizar session_state para mantener sincronización con otras pestañas
            # Asegurar limpieza de espacios en "Masa Base"
            edit_m_clean = edit_m.copy()
            if "Masa Base" in edit_m_clean.columns:
                edit_m_clean["Masa Base"] = (
                    edit_m_clean["Masa Base"].astype(str).str.strip()
                )
            st.session_state.df_ajustes = edit_m_clean

            st.success("Ajustes actualizados.")

        st.divider()

        # --- IMPORTAR AJUSTES DESDE CSV ---
        with st.expander("📂 Importar Ajustes desde CSV", expanded=False):
            st.info(
                "Sube un archivo CSV con los ajustes para actualizar la configuración maestra."
            )
            archivo_subido = st.file_uploader(
                "Sube el archivo .csv que descargaste", type="csv"
            )

            if archivo_subido is not None:
                if st.button("🚀 Aplicar datos del CSV a Ajustes Maestros"):
                    # leer con utf-8 para enseñar avisos pronto si hay otro encoding
                    df_subido = pd.read_csv(archivo_subido, encoding="utf-8")
                    # normalizar posibles encabezados rotos/acentuados
                    df_subido.rename(
                        columns={
                            "Tope 1 (CrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­tico)": "Tope 1 (critico)",
                            "Tope 1 (Crítico)": "Tope 1 (critico)",
                            "Tope 1 (Critico)": "Tope 1 (critico)",
                        },
                        inplace=True,
                    )
                    # Limpiar espacios en "Masa Base" para evitar errores de sincronización
                    if "Masa Base" in df_subido.columns:
                        df_subido["Masa Base"] = (
                            df_subido["Masa Base"].astype(str).str.strip()
                        )

                    # Guardamos lo que subiste en la memoria del sistema
                    st.session_state.df_ajustes = df_subido

                    # También lo guardamos en el archivo permanente para que no se borre
                    st.session_state.df_ajustes.to_json(
                        "data/ajustes_produccion.json", orient="records", indent=4
                    )

                    st.success("✅ Ajustes actualizados desde el CSV.")
                    st.rerun()

# ========================================================
# PESTAÑA 6: GESTIÓN DE CLIENTES (Bloque Corregido)
# ========================================================
if perfil in ["admin", "encargado"]:
    try:
        idx_clientes = titulos_tabs.index("👥 Clientes")
        with tabs[idx_clientes]:
            st.header("👥 Directorio de Clientes")

            ruta_clientes = "data/clientes.csv"

            # --- Formulario de Alta Totalmente Automático ---
            with st.expander("➕ Registrar Nuevo Cliente", expanded=False):
                with st.form("form_nuevo_cliente"):
                    st.info("El ID de cliente se generará automáticamente al guardar.")

                    nombre_cliente = st.text_input(
                        "Nombre / Razón Social (Ej: Hotel Central):"
                    )

                    c1, c2 = st.columns(2)
                    with c1:
                        contacto = st.text_input("Teléfono / Contacto:")
                    with c2:
                        zona = st.selectbox(
                            "Zona de Entrega:",
                            [
                                "Norte",
                                "Sur",
                                "Este",
                                "Oeste",
                                "Centro",
                                "Retira en Planta",
                            ],
                        )

                    btn_guardar = st.form_submit_button(
                        "Guardar Cliente", use_container_width=True
                    )

                    if btn_guardar:
                        if nombre_cliente:
                            # --- Lógica de ID Automático (Interna) ---
                            if os.path.exists(ruta_clientes):
                                df_c = pd.read_csv(ruta_clientes)
                                if not df_c.empty:
                                    # Aseguramos que el ID sea tratado como entero para sumar
                                    nuevo_id = int(df_c["ID"].max()) + 1
                                else:
                                    nuevo_id = 1001
                            else:
                                df_c = pd.DataFrame(
                                    columns=[
                                        "ID",
                                        "Nombre",
                                        "Contacto",
                                        "Zona",
                                        "Fecha_Alta",
                                    ]
                                )
                                nuevo_id = 1001

                            # Crear el registro
                            nuevo_c = pd.DataFrame(
                                [
                                    {
                                        "ID": nuevo_id,
                                        "Nombre": nombre_cliente,
                                        "Contacto": contacto,
                                        "Zona": zona,
                                        "Fecha_Alta": datetime.now().strftime(
                                            "%Y-%m-%d"
                                        ),
                                    }
                                ]
                            )

                            df_c = pd.concat([df_c, nuevo_c], ignore_index=True)
                            df_c.to_csv(ruta_clientes, index=False)
                            st.success(
                                f"✅ Cliente registrado con éxito. ID Asignado: {nuevo_id}"
                            )
                            st.rerun()
                        else:
                            st.warning("⚠️ El nombre del cliente es obligatorio.")

            # --- Visualización y Edición ---
            if os.path.exists(ruta_clientes):
                df_c = pd.read_csv(ruta_clientes)
                st.subheader("Lista de Clientes Activos")

                # Aquí el ID está bloqueado para edición (disabled)
                df_c_edit = st.data_editor(
                    df_c,
                    num_rows="dynamic",
                    key="editor_clientes_vFinal",
                    use_container_width=True,
                    hide_index=True,
                    disabled=["ID", "Fecha_Alta"],
                )

                if st.button("💾 Guardar Cambios en la Lista"):
                    df_c_edit.to_csv(ruta_clientes, index=False)
                    st.success("Cambios guardados.")
                    st.rerun()
            else:
                st.info("Aún no hay clientes registrados.")
    except ValueError:
        pass
# ========================================================
# PESTAÑA 7: CARGA DE PEDIDOS (Formulario Dinámico por Unidades)
# ========================================================
if perfil in ["admin", "encargado"]:
    try:
        idx_pedidos = titulos_tabs.index("📝 Carga Pedidos")
        with tabs[idx_pedidos]:
            # si estamos en modo edición de un pedido, ajustar encabezado
            if "pedido_en_edicion" in st.session_state:
                st.header("✏️ Modificar Pedido")
            else:
                st.header("📝 Registro de Pedidos (Unidades)")

            ruta_pedidos = "data/pedidos.csv"
            ruta_clientes = "data/clientes.csv"

            # 1. Cargar base de datos de Clientes
            lista_clientes = []
            if os.path.exists(ruta_clientes):
                df_c = pd.read_csv(ruta_clientes)
                lista_clientes = [
                    f"{row['ID']} - {row['Nombre']}" for _, row in df_c.iterrows()
                ]

            # 2. Cargar base de datos de Productos (Priorizando Session State)
            if "df_ajustes" in st.session_state:
                lista_productos = (
                    st.session_state.df_ajustes["Masa Base"].unique().tolist()
                )
            elif os.path.exists("data/ajustes_produccion.json"):
                df_temp = pd.read_json("data/ajustes_produccion.json")
                lista_productos = df_temp["Masa Base"].unique().tolist()
            else:
                lista_productos = df_base["Masa Base"].unique().tolist()

            if not lista_clientes:
                st.warning("⚠️ Registra clientes antes de cargar pedidos.")
            elif not lista_productos:
                st.error(
                    "⚠️ No se encontró la tabla de Ajustes Maestros para referenciar productos."
                )
            else:
                # --- FORMULARIO PRÁCTICO ---
                # CSS para mostrar checkboxes sin hover
                st.markdown(
                    """
                <style>
                [data-testid="stTable"] th:first-child, [data-testid="stTable"] td:first-child {
                    opacity: 1 !important;
                }
                /* Forzar visibilidad en data_editor moderno */
                div[data-testid="stDataFrameDataLayer"] button {
                    opacity: 1 !important;
                }
                </style>
                """,
                    unsafe_allow_html=True,
                )
                # detectamos si estamos modificando un pedido previamente seleccionado
                editing = "pedido_en_edicion" in st.session_state
                exp_label = (
                    "🔧 Modificar Pedido" if editing else "🆕 Generar Nuevo Pedido"
                )
                with st.expander(exp_label, expanded=True):
                    # Contenedor local para forzar CSS en este editor
                    with st.container():
                        st.markdown(
                            """
                            <style>
                            button {
                                opacity: 1 !important;
                            }
                            /* Selector específico para checkboxes de data_editor */
                            div[data-testid="stDataFrameDataLayer"] button[role="checkbox"],
                            div[data-testid="stDataFrameDataLayer"] button[aria-checked] {
                                opacity: 1 !important;
                                visibility: visible !important;
                            }
                            </style>
                        """,
                            unsafe_allow_html=True,
                        )

                    # Encabezado fijo del pedido
                    c1, c2 = st.columns(2)
                    with c1:
                        if editing and "cliente_en_edicion" in st.session_state:
                            default_cli = st.session_state.cliente_en_edicion
                            default_idx = (
                                lista_clientes.index(default_cli)
                                if default_cli in lista_clientes
                                else 0
                            )
                            cliente_sel = st.selectbox(
                                "Seleccionar Cliente:",
                                lista_clientes,
                                index=default_idx,
                                disabled=True,
                            )
                        else:
                            cliente_sel = st.selectbox(
                                "Seleccionar Cliente:", lista_clientes
                            )
                    with c2:
                        if editing and "fecha_entrega_en_edicion" in st.session_state:
                            fecha_entrega = st.date_input(
                                "Fecha de Entrega:",
                                value=st.session_state.fecha_entrega_en_edicion,
                                min_value=date.today(),
                                help="Só se pueden seleccionar fechas de hoy en adelante.",
                            )
                        else:
                            fecha_entrega = st.date_input(
                                "Fecha de Entrega:",
                                value=date.today() + timedelta(days=1),
                                min_value=date.today(),
                                help="Só se pueden seleccionar fechas de hoy en adelante. Por defecto, mañana para programación anticipated.",
                            )

                    if editing and "obs_en_edicion" in st.session_state:
                        obs_general = st.text_input(
                            "Observaciones generales del pedido:",
                            value=st.session_state.obs_en_edicion,
                        )
                    else:
                        obs_general = st.text_input(
                            "Observaciones generales del pedido:"
                        )

                    st.write("### Detalle de Productos")
                    st.info(
                        "Usa el botón + abajo a la derecha para sumar productos. Toca el tacho de basura rojo para quitar un ítem."
                    )

                    # manejar lista de productos en session_state
                    if not editing:
                        if "items_nuevo_pedido" not in st.session_state:
                            st.session_state.items_nuevo_pedido = [
                                {
                                    "Seleccionar": False,
                                    "Producto": lista_productos[0],
                                    "Unidades": 1,
                                }
                            ]
                    else:
                        # si se perdió la lista por alguna recarga, intentar reconstruirla
                        if "items_nuevo_pedido" not in st.session_state:
                            if os.path.exists(ruta_pedidos):
                                df_tmp = pd.read_csv(ruta_pedidos)
                                df_this = df_tmp[
                                    df_tmp["ID_Pedido"].astype(str)
                                    == str(st.session_state.pedido_en_edicion)
                                ]
                                if not df_this.empty:
                                    items = []
                                    for _, r in df_this.iterrows():
                                        items.append(
                                            {
                                                "Seleccionar": False,
                                                "Producto": r["Producto"],
                                                "Unidades": r["Unidades"],
                                            }
                                        )
                                    st.session_state.items_nuevo_pedido = items
                                else:
                                    st.session_state.items_nuevo_pedido = [
                                        {
                                            "Seleccionar": False,
                                            "Producto": lista_productos[0],
                                            "Unidades": 1,
                                        }
                                    ]
                            else:
                                st.session_state.items_nuevo_pedido = [
                                    {
                                        "Seleccionar": False,
                                        "Producto": lista_productos[0],
                                        "Unidades": 1,
                                    }
                                ]

                    # convertir lista a DataFrame para editar, asegurando columna Seleccionar primero
                    df_temp = pd.DataFrame(st.session_state.items_nuevo_pedido)
                    if "Seleccionar" not in df_temp.columns:
                        df_temp.insert(0, "Seleccionar", False)
                    else:
                        # mover Seleccionar a la primera posición
                        cols = list(df_temp.columns)
                        cols.insert(0, cols.pop(cols.index("Seleccionar")))
                        df_temp = df_temp[cols]

                    # configurar columnas editables
                    col_cfg = {}
                    col_cfg["Seleccionar"] = st.column_config.CheckboxColumn(
                        "Seleccionar",
                        help="Marcar fila para operaciones",
                    )
                    col_cfg["Producto"] = st.column_config.SelectboxColumn(
                        "Producto",
                        options=lista_productos,
                        required=True,
                        width="large",
                    )
                    col_cfg["Unidades"] = st.column_config.NumberColumn(
                        "Unidades",
                        min_value=1,
                        step=1,
                        format="%d",
                        required=True,
                    )

                    df_editor = st.data_editor(
                        df_temp,
                        column_config=col_cfg,
                        num_rows="fixed",
                        disabled=False,
                        use_container_width=True,
                        hide_index=True,
                        key="editor_nuevo_pedido",
                    )

                    # helper para aplicar ediciones pendientes del widget
                    def apply_widget_edits():
                        widget = st.session_state.get("editor_nuevo_pedido", {})
                        edits = []
                        if hasattr(widget, "get"):
                            edits = widget.get("edited_rows", [])
                        elif isinstance(widget, list):
                            edits = widget
                        for change in edits:
                            # support integer entries
                            if isinstance(change, int):
                                idx = change
                                continue  # nothing else to apply
                            if isinstance(change, dict):
                                idx = change.get("index")
                            else:
                                continue
                            if idx is None or idx >= len(
                                st.session_state.items_nuevo_pedido
                            ):
                                continue
                            if isinstance(change, dict):
                                for k, v in change.items():
                                    if k == "index":
                                        continue
                                    st.session_state.items_nuevo_pedido[idx][k] = v

                    # botones de control fuera de la tabla (3 columnas para distribución equitativa)
                    btn1, btn2, btn3 = st.columns([1, 1, 1])
                    with btn1:
                        if st.button(
                            "➕ Agregar Producto",
                            use_container_width=True,
                            type="primary",
                        ):
                            # guardar todos los cambios actuales de la tabla
                            if df_editor is not None:
                                try:
                                    st.session_state.items_nuevo_pedido = (
                                        df_editor.to_dict(orient="records")
                                    )
                                except Exception:
                                    pass
                            apply_widget_edits()
                            # añadir fila nueva con valores por defecto al final
                            st.session_state.items_nuevo_pedido.append(
                                {
                                    "Seleccionar": False,
                                    "Producto": lista_productos[0],
                                    "Unidades": 1,
                                }
                            )
                            # simplemente rerun para que la tabla se redibuje automáticamente
                            st.rerun()
                    with btn2:
                        if st.button(
                            "🗑️ Borrar seleccionados", use_container_width=True
                        ):
                            # capturar estado actual antes de filtrar
                            if df_editor is not None:
                                try:
                                    st.session_state.items_nuevo_pedido = (
                                        df_editor.to_dict(orient="records")
                                    )
                                except Exception:
                                    pass
                            apply_widget_edits()
                            df_now = pd.DataFrame(st.session_state.items_nuevo_pedido)
                            if "Seleccionar" in df_now.columns:
                                df_now = df_now[~df_now["Seleccionar"]]
                            if df_now.empty:
                                df_now = pd.DataFrame(
                                    [
                                        {
                                            "Seleccionar": False,
                                            "Producto": lista_productos[0],
                                            "Unidades": 1,
                                        }
                                    ]
                                )
                            st.session_state.items_nuevo_pedido = df_now.to_dict(
                                orient="records"
                            )
                            if "editor_nuevo_pedido" in st.session_state:
                                del st.session_state["editor_nuevo_pedido"]
                            st.rerun()
                            st.session_state.items_nuevo_pedido = df_now.to_dict(
                                orient="records"
                            )
                            st.rerun()
                    # columna 3 intencionalmente vacía para espaciado

                    # permitir cancelar edición si estamos modificando
                    if editing and st.button(
                        "❌ Cancelar edición",
                        use_container_width=True,
                        type="secondary",
                    ):
                        for key in [
                            "pedido_en_edicion",
                            "estado_en_edicion",
                            "cliente_en_edicion",
                            "fecha_entrega_en_edicion",
                            "obs_en_edicion",
                            "items_nuevo_pedido",
                            "editor_nuevo_pedido",
                        ]:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

                    save_label = (
                        "💾 Guardar Cambios"
                        if editing
                        else "🚀 Confirmar y Guardar Pedido Completo"
                    )
                    if st.button(
                        save_label,
                        use_container_width=True,
                        type="primary",
                    ):
                        # Validación de seguridad: la fecha no puede ser anterior a hoy
                        if fecha_entrega < date.today():
                            st.error(
                                "❌ Error: La fecha de entrega no puede ser anterior a hoy. Por favor, selecciona una fecha válida."
                            )
                        else:
                            # determinar si estábamos editando un pedido existente
                            editing = "pedido_en_edicion" in st.session_state
                            # conservar el mismo ID en caso de edición, o generar nuevo
                            if editing:
                                id_grupo = st.session_state.pedido_en_edicion
                                estado_para_guardar = st.session_state.get(
                                    "estado_en_edicion", "Pendiente"
                                )
                            else:
                                id_grupo = int(datetime.now().timestamp())
                                estado_para_guardar = "Pendiente"
                            id_cli = cliente_sel.split(" - ")[0]
                            nom_cli = cliente_sel.split(" - ")[1]
                            fecha_reg = datetime.now().strftime("%Y-%m-%d %H:%M")

                            # Convertimos las filas del editor en el formato del CSV
                            nuevos_registros = []
                            for _, fila in df_editor.iterrows():
                                producto = fila.get("Producto")
                                unidades = fila.get("Unidades")
                                # ignorar filas vacías o no seleccionadas
                                if pd.isna(producto) or str(producto).strip() == "":
                                    continue
                                try:
                                    unidades_val = int(unidades)
                                except Exception:
                                    unidades_val = 0
                                if unidades_val <= 0:
                                    continue
                                nuevos_registros.append(
                                    {
                                        "ID_Pedido": id_grupo,
                                        "ID_Cliente": id_cli,
                                        "Cliente": nom_cli,
                                        "Producto": producto,
                                        "Unidades": unidades_val,
                                        "Fecha_Entrega": fecha_entrega.strftime(
                                            "%Y-%m-%d"
                                        ),
                                        "Estado": estado_para_guardar,
                                        "Fecha_Registro": fecha_reg,
                                        "Obs": obs_general,
                                    }
                                )

                            df_nuevos = pd.DataFrame(nuevos_registros)

                            # Persistencia en CSV
                            if os.path.exists(ruta_pedidos):
                                df_hist = pd.read_csv(ruta_pedidos)
                                if editing:
                                    # eliminamos las líneas antiguas del pedido para evitar duplicados
                                    df_hist = df_hist[
                                        df_hist["ID_Pedido"].astype(str)
                                        != str(id_grupo)
                                    ]
                                df_final = pd.concat(
                                    [df_hist, df_nuevos], ignore_index=True
                                )
                            else:
                                df_final = df_nuevos

                            df_final.to_csv(ruta_pedidos, index=False)

                            # Limpiamos sesión y refrescamos; también quitar bandera de edición si existía
                            if editing:
                                for key in [
                                    "pedido_en_edicion",
                                    "estado_en_edicion",
                                    "cliente_en_edicion",
                                    "fecha_entrega_en_edicion",
                                    "obs_en_edicion",
                                ]:
                                    if key in st.session_state:
                                        del st.session_state[key]

                            if "df_pedido_temp" in st.session_state:
                                del st.session_state.df_pedido_temp

                            if "editor_nuevo_pedido" in st.session_state:
                                del st.session_state["editor_nuevo_pedido"]
                            if "items_nuevo_pedido" in st.session_state:
                                del st.session_state["items_nuevo_pedido"]

                            if editing:
                                st.success(
                                    f"✅ Pedido {id_grupo} modificado con {len(nuevos_registros)} ítems para {nom_cli}."
                                )
                            else:
                                st.success(
                                    f"✅ Pedido de {len(nuevos_registros)} ítems guardado para {nom_cli}."
                                )
                            time.sleep(1)
                            st.rerun()
                if os.path.exists(ruta_pedidos):
                    st.divider()
                    st.subheader("📋 Pedidos Programados")
                    df_p = pd.read_csv(ruta_pedidos)

                    # Asegurar que la columna 'Estado' existe, si no asignar 'Pendiente' por defecto
                    if "Estado" not in df_p.columns:
                        df_p["Estado"] = "Pendiente"

                    # Filtramos por pendientes Y reservados
                    df_pendientes = df_p[
                        df_p["Estado"].isin(["Pendiente", "Reservado"])
                    ].copy()

                    # Ordenar: Reservados primero, luego Pendientes
                    estado_order = {"Reservado": 0, "Pendiente": 1}
                    df_pendientes["estado_sort"] = df_pendientes["Estado"].map(
                        estado_order
                    )
                    df_pendientes = df_pendientes.sort_values(by="estado_sort").drop(
                        "estado_sort", axis=1
                    )

                    if not df_pendientes.empty:
                        # Agrupar por ID_Pedido y crear vista resumida
                        df_resumen = (
                            df_pendientes.groupby("ID_Pedido")
                            .agg(
                                {
                                    "Cliente": "first",  # Tomar el primer valor encontrado
                                    "Fecha_Entrega": "first",
                                    "Fecha_Registro": "first",
                                    "Estado": "first",
                                }
                            )
                            .reset_index()
                        )

                        # Renombrar columnas según requerimientos
                        df_resumen = df_resumen.rename(
                            columns={
                                "ID_Pedido": "Nro. Pedido",
                                "Fecha_Registro": "Fecha ingreso",
                                "Fecha_Entrega": "Fecha entrega",
                            }
                        )

                        # Agregar columna 'Despacho' vacía
                        df_resumen["Despacho"] = ""

                        # Reordenar columnas según especificación
                        df_resumen = df_resumen[
                            [
                                "Nro. Pedido",
                                "Fecha ingreso",
                                "Cliente",
                                "Fecha entrega",
                                "Despacho",
                                "Estado",
                            ]
                        ]

                        # Ordenar por fecha de entrega y número de pedido
                        df_resumen = df_resumen.sort_values(
                            by=["Fecha entrega", "Nro. Pedido"], ascending=[True, False]
                        )

                        # Mostrar tabla resumida usando data_editor para checkbox persistente
                        df_resumen = df_resumen.copy()
                        # insertar columna de selección al principio
                        if "Seleccionar" not in df_resumen.columns:
                            df_resumen.insert(0, "Seleccionar", False)

                        col_cfg = {
                            "Seleccionar": st.column_config.CheckboxColumn(
                                "Seleccionar",
                                help="Marca para elegir este pedido",
                            )
                        }
                        # ordenar columnas para asegurar que 'Seleccionar' quede la primera
                        column_order = list(df_resumen.columns)

                        df_edit = st.data_editor(
                            df_resumen,
                            use_container_width=True,
                            hide_index=True,
                            column_config=col_cfg,
                            column_order=column_order,
                            key="tabla_pedidos_resumen",
                        )

                        # Obtener el pedido seleccionado a partir del checkbox
                        pedido_seleccionado = None
                        num_seleccionadas = 0
                        if not df_edit.empty and "Seleccionar" in df_edit.columns:
                            seleccionadas = df_edit[df_edit["Seleccionar"]]
                            num_seleccionadas = len(seleccionadas)
                            if num_seleccionadas == 1:
                                pedido_seleccionado = seleccionadas.iloc[0][
                                    "Nro. Pedido"
                                ]
                            elif num_seleccionadas > 1:
                                st.warning(
                                    "⚠️ Selecciona únicamente un pedido para modificar o ver detalle."
                                )

                        # Sección para ver detalles de pedidos específicos
                        st.subheader("🔍 Ver Detalle de Pedidos")

                        # Inicializar estado de visualización si no existe
                        if "mostrar_detalle_pedido" not in st.session_state:
                            st.session_state.mostrar_detalle_pedido = False
                            st.session_state.pedido_detalle_activo = None

                        # Si cambió la selección, resetear el estado del detalle
                        if (
                            pedido_seleccionado is not None
                            and st.session_state.get("pedido_detalle_activo")
                            is not None
                            and str(st.session_state.get("pedido_detalle_activo"))
                            != str(pedido_seleccionado)
                        ):
                            st.session_state.mostrar_detalle_pedido = False
                            st.session_state.pedido_detalle_activo = None

                        # Mostrar botones o mensaje según la selección
                        if pedido_seleccionado is not None:
                            # Convertir a string para comparación uniforme
                            pedido_id = str(pedido_seleccionado)

                            # Obtener estado actual del pedido
                            estado_actual = (
                                df_pendientes[
                                    df_pendientes["ID_Pedido"].astype(str) == pedido_id
                                ]["Estado"].iloc[0]
                                if not df_pendientes[
                                    df_pendientes["ID_Pedido"].astype(str) == pedido_id
                                ].empty
                                else "Desconocido"
                            )

                            # Obtener perfil del usuario actual
                            perfil_usuario = (
                                st.session_state.authenticator.get_user_profile()
                            )
                            es_admin = perfil_usuario == "admin"

                            # --- BOTONES DE ACCIÓN (aparecen siempre, habilitados solo para admin) ---
                            st.write("**Acciones disponibles:**")

                            # Crear 5 columnas para los botones de acción
                            col_mod, col_ver, col_anu, col_res, col_des = st.columns(5)

                            # Botón 1: Modificar
                            with col_mod:
                                if st.button(
                                    "✏️ Modificar",
                                    use_container_width=True,
                                    disabled=not es_admin or num_seleccionadas != 1,
                                    key=f"btn_modificar_{pedido_id}",
                                ):
                                    if es_admin:
                                        # preparar el modo edición
                                        st.session_state.pedido_en_edicion = pedido_id
                                        st.session_state.estado_en_edicion = (
                                            estado_actual
                                        )

                                        # extraer detalles del pedido para precargar el formulario
                                        df_this = df_pendientes[
                                            df_pendientes["ID_Pedido"].astype(str)
                                            == str(pedido_id)
                                        ]
                                        if not df_this.empty:
                                            first = df_this.iloc[0]
                                            st.session_state.cliente_en_edicion = f"{first['ID_Cliente']} - {first['Cliente']}"
                                            try:
                                                st.session_state.fecha_entrega_en_edicion = datetime.strptime(
                                                    first["Fecha_Entrega"], "%Y-%m-%d"
                                                ).date()
                                            except Exception:
                                                st.session_state.fecha_entrega_en_edicion = (
                                                    date.today()
                                                )
                                            st.session_state.obs_en_edicion = first.get(
                                                "Obs", ""
                                            )

                                            items = []
                                            for _, r in df_this.iterrows():
                                                items.append(
                                                    {
                                                        "Seleccionar": False,
                                                        "Producto": r["Producto"],
                                                        "Unidades": r["Unidades"],
                                                    }
                                                )
                                            st.session_state.items_nuevo_pedido = items

                                        # resetear cualquier detalle abierto y la tabla para evitar confusiones
                                        st.session_state.mostrar_detalle_pedido = False
                                        st.session_state.pedido_detalle_activo = None
                                        if "tabla_pedidos_resumen" in st.session_state:
                                            del st.session_state[
                                                "tabla_pedidos_resumen"
                                            ]
                                        st.rerun()

                            # Botón 2: Ver detalle (toggle expander) - ÚNICO CONTROL DEL EXPANDER
                            with col_ver:
                                if st.button(
                                    "👁️ Ver detalle",
                                    use_container_width=True,
                                    disabled=not es_admin,
                                    key=f"btn_ver_det_{pedido_id}",
                                ):
                                    if es_admin:
                                        # Establecer el pedido activo y hacer toggle
                                        st.session_state.pedido_detalle_activo = (
                                            pedido_id
                                        )
                                        st.session_state.mostrar_detalle_pedido = (
                                            not st.session_state.get(
                                                "mostrar_detalle_pedido", False
                                            )
                                        )
                                        st.rerun()

                            # Botón 3: Anular
                            with col_anu:
                                # Verificar si hay cancelación pendiente
                                es_anulacion_pendiente = (
                                    st.session_state.get("pedido_anular_confirmacion")
                                    == pedido_id
                                )

                                if st.button(
                                    "❌ Anular",
                                    use_container_width=True,
                                    disabled=not es_admin or estado_actual == "Anulado",
                                    key=f"btn_anular_{pedido_id}",
                                ):
                                    if es_admin:
                                        # Establecer el pedido que aguarda confirmación
                                        st.session_state.pedido_anular_confirmacion = (
                                            pedido_id
                                        )
                                        st.rerun()

                                # Mostrar prompt de confirmación si está pendiente
                                if es_anulacion_pendiente:
                                    st.warning(
                                        f"⚠️ **Confirmar anulación del pedido #{pedido_id}**\n\n"
                                        "Esta acción NO se puede deshacer. El pedido se marcará "
                                        "como 'Anulado' pero se mantendrá en el archivo para historial.",
                                        icon="⚠️",
                                    )

                                    col_conf_si, col_conf_no = st.columns(2)

                                    with col_conf_si:
                                        if st.button(
                                            "✅ Confirmar Anulación",
                                            use_container_width=True,
                                            key=f"btn_confirmar_anular_{pedido_id}",
                                            type="primary",
                                        ):
                                            # Ejecutar la anulación
                                            exito, mensaje = anular_pedido(pedido_id)

                                            if exito:
                                                st.success(f"✅ {mensaje}")
                                                # Limpiar la confirmación pendiente
                                                st.session_state.pedido_anular_confirmacion = (
                                                    None
                                                )
                                                st.rerun()
                                            else:
                                                st.error(f"❌ {mensaje}")
                                                st.session_state.pedido_anular_confirmacion = (
                                                    None
                                                )

                                    with col_conf_no:
                                        if st.button(
                                            "❌ Cancelar",
                                            use_container_width=True,
                                            key=f"btn_cancelar_anular_{pedido_id}",
                                        ):
                                            # Cancelar la confirmación
                                            st.session_state.pedido_anular_confirmacion = (
                                                None
                                            )
                                            st.rerun()

                            # Botón 4: Reservar
                            with col_res:
                                # Determinar etiqueta y estado del botón basado en estado actual
                                es_ya_reservado = estado_actual == "Reservado"
                                etiqueta_btn = (
                                    "✓ Reservado" if es_ya_reservado else "🔒 Reservar"
                                )
                                btn_deshabilitado = not es_admin or es_ya_reservado

                                if st.button(
                                    etiqueta_btn,
                                    use_container_width=True,
                                    disabled=btn_deshabilitado,
                                    key=f"btn_reservar_{pedido_id}",
                                ):
                                    if es_admin and not es_ya_reservado:
                                        # Ejecutar la lógica de reserva
                                        exito, mensaje = reservar_pedido(pedido_id)

                                        if exito:
                                            st.success(f"✅ {mensaje}")
                                            st.session_state["pedido_reservado"] = True
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {mensaje}")

                            # Botón 5: Descargar
                            with col_des:
                                if st.button(
                                    "⬇️ Descargar",
                                    use_container_width=True,
                                    disabled=not es_admin,
                                    key=f"btn_descargar_{pedido_id}",
                                ):
                                    if es_admin:
                                        # Obtener datos del pedido desde df_pendientes
                                        detalle_pedido_data = df_pendientes[
                                            df_pendientes["ID_Pedido"].astype(str)
                                            == pedido_id
                                        ][["Producto", "Unidades"]].copy()

                                        info_pedido_data = df_pendientes[
                                            df_pendientes["ID_Pedido"].astype(str)
                                            == pedido_id
                                        ].iloc[0]

                                        # Generar PDF en memoria
                                        pdf_bytes = exportar_pedido_pdf(
                                            pedido_id=pedido_id,
                                            detalle_productos=detalle_pedido_data,
                                            info_cliente=info_pedido_data,
                                        )

                                        # Botón de descarga
                                        st.download_button(
                                            label="📥 Descargar PDF",
                                            data=pdf_bytes,
                                            file_name=f"Pedido_{pedido_id}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.pdf",
                                            mime="application/pdf",
                                            key=f"download_pdf_{pedido_id}",
                                        )

                            st.divider()

                            # Mostrar el detalle SOLO si está activado por el botón "Ver detalle"
                            if (
                                st.session_state.get("mostrar_detalle_pedido", False)
                                and str(
                                    st.session_state.get("pedido_detalle_activo", "")
                                )
                                == pedido_id
                            ):
                                # Extraer datos del pedido
                                info_pedido = df_pendientes[
                                    df_pendientes["ID_Pedido"].astype(str) == pedido_id
                                ].iloc[0]

                                # Obtener observaciones una sola vez
                                obs_general = (
                                    str(info_pedido.get("Obs", "")).strip()
                                    if pd.notna(info_pedido.get("Obs"))
                                    else ""
                                )

                                # DataFrame solo con Producto y Unidades (sin Obs)
                                detalle_pedido = df_pendientes[
                                    df_pendientes["ID_Pedido"].astype(str) == pedido_id
                                ][["Producto", "Unidades"]].copy()

                                if not detalle_pedido.empty:
                                    with st.expander(
                                        f"📦 Detalle del Pedido #{pedido_id}",
                                        expanded=True,
                                    ):
                                        # Mostrar tabla de productos (sin observaciones)
                                        st.dataframe(
                                            detalle_pedido,
                                            use_container_width=True,
                                            hide_index=True,
                                        )

                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write(
                                                f"**Cliente:** {info_pedido['Cliente']}"
                                            )
                                            st.write(
                                                f"**Fecha de Entrega:** {info_pedido['Fecha_Entrega']}"
                                            )
                                        with col2:
                                            st.write(
                                                f"**Fecha de Registro:** {info_pedido['Fecha_Registro']}"
                                            )
                                            st.write(
                                                f"**Estado:** {info_pedido['Estado']}"
                                            )

                                        # Mostrar observaciones generales una sola vez
                                        if obs_general:
                                            st.info(
                                                f"📝 **Observaciones Generales:** {obs_general}"
                                            )
                        else:
                            # Mensaje informativo cuando no hay selección
                            st.info(
                                "Seleccione un pedido de la tabla para ver su detalle."
                            )
                    else:
                        st.info("No hay pedidos pendientes programados.")

    except ValueError:
        pass

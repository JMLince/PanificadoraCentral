import streamlit as st


def generar_login():
    # Inicialización de variables de estado
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.perfil = None
        st.session_state.usuario = None

    # Si NO está autenticado, mostramos el formulario
    if not st.session_state.autenticado:
        st.markdown(
            "<h1 style='text-align: center;'>🔐 Acceso al Sistema</h1>",
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.form("login"):
                usuario = st.text_input("Usuario")
                clave = st.text_input("Contraseña", type="password")

                if st.form_submit_button("Ingresar", use_container_width=True):
                    # --- PERFIL: ADMINISTRADOR ---
                    if usuario == "admin" and clave == "1234":
                        st.session_state.autenticado = True
                        st.session_state.perfil = "admin"
                        st.session_state.usuario = "Administrador"
                        st.rerun()

                    # --- PERFIL: PANADERO (Producción) ---
                    elif usuario == "panadero" and clave == "5678":
                        st.session_state.autenticado = True
                        st.session_state.perfil = (
                            "panadero"  # Cambiado de 'operario' a 'panadero'
                        )
                        st.session_state.usuario = "Panadero"
                        st.rerun()

                    # --- PERFIL: ENCARGADO (NUEVO) ---
                    elif usuario == "encargado" and clave == "2468":
                        st.session_state.autenticado = True
                        st.session_state.perfil = "encargado"
                        st.session_state.usuario = "Jefe de Planta"
                        st.rerun()

                    else:
                        st.error("Credenciales incorrectas")

        # El st.stop() aquí es vital para que no se ejecute el main si no hay login
        st.stop()

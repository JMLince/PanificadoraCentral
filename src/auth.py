"""
Módulo de autenticación y manejo de sesiones.

Define la clase Authenticator que maneja el flujo de login y la gestión
del estado de autenticación en Streamlit, utilizando estrategias configurables.
"""

import streamlit as st
from typing import Optional
from src.auth_strategies import AuthStrategy


class Authenticator:
    """
    Gestor de autenticación que coordina el flujo de login con Streamlit.

    - Mantiene el estado de autenticación en st.session_state
    - Renderiza el formulario de login en la sidebar
    - Delega la validación de credenciales a una estrategia configurable
    """

    # Claves de sesión
    SESSION_AUTH_KEY = "autenticado"
    SESSION_PERFIL_KEY = "perfil"
    SESSION_USUARIO_KEY = "usuario"

    def __init__(self, strategy: AuthStrategy):
        """
        Inicializa el Authenticator con una estrategia de autenticación.

        Args:
            strategy (AuthStrategy): Estrategia a usar para validar credenciales
        """
        self.strategy = strategy
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """
        Inicializa las claves necesarias en st.session_state.
        Solo se ejecuta si aún no existen.
        """
        if self.SESSION_AUTH_KEY not in st.session_state:
            st.session_state[self.SESSION_AUTH_KEY] = False
            st.session_state[self.SESSION_PERFIL_KEY] = None
            st.session_state[self.SESSION_USUARIO_KEY] = None

    def is_authenticated(self) -> bool:
        """
        Verifica si el usuario está autenticado.

        Returns:
            bool: True si está autenticado, False en caso contrario
        """
        return st.session_state.get(self.SESSION_AUTH_KEY, False)

    def get_user_profile(self) -> Optional[str]:
        """
        Obtiene el perfil del usuario autenticado.

        Returns:
            Optional[str]: Perfil del usuario (admin, panadero, etc.) o None
        """
        return st.session_state.get(self.SESSION_PERFIL_KEY)

    def get_username(self) -> Optional[str]:
        """
        Obtiene el nombre del usuario autenticado.

        Returns:
            Optional[str]: Nombre completo del usuario o None
        """
        return st.session_state.get(self.SESSION_USUARIO_KEY)

    def logout(self) -> None:
        """
        Cierra la sesión del usuario y limpia el estado.
        """
        st.session_state[self.SESSION_AUTH_KEY] = False
        st.session_state[self.SESSION_PERFIL_KEY] = None
        st.session_state[self.SESSION_USUARIO_KEY] = None

    def render_login_form(self) -> None:
        """
        Renderiza el formulario de login en la interfaz.

        Si el usuario no está autenticado, muestra el formulario centrado.
        Si está autenticado, muestra información de perfil en la sidebar.
        """
        if not self.is_authenticated():
            self._render_login_page()
        else:
            self._render_sidebar_info()

    def _render_login_page(self) -> None:
        """
        Renderiza la página de login completa (para usuarios no autenticados).
        Detiene la ejecución del resto de la app con st.stop().
        """
        st.markdown(
            "<h1 style='text-align: center;'>🔐 Acceso al Sistema</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: gray;'>Panificadora Central v2.5</p>",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 1.2, 1])

        with col2:
            st.markdown("---")
            with st.form("login_form", border=True):
                username = st.text_input(
                    "👤 Usuario", placeholder="Ingresa tu usuario", key="login_username"
                )
                password = st.text_input(
                    "🔑 Contraseña",
                    type="password",
                    placeholder="Ingresa tu contraseña",
                    key="login_password",
                )

                submitted = st.form_submit_button(
                    "Ingresar al Sistema", use_container_width=True, type="primary"
                )

                if submitted:
                    self._process_login(username, password)

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; font-size: 12px; color: gray;'>"
            "Contacta al administrador si olvidaste tus credenciales."
            "</p>",
            unsafe_allow_html=True,
        )

        # Detener ejecución si no está autenticado
        st.stop()

    def _process_login(self, username: str, password: str) -> None:
        """
        Procesa las credenciales enviadas usando la estrategia configurada.

        Args:
            username (str): Nombre de usuario ingresado
            password (str): Contraseña ingresada
        """
        # Validar que los campos no estén vacíos
        if not username or not password:
            st.error("❌ Usuario y contraseña son requeridos")
            return

        # Delegar validación a la estrategia
        result = self.strategy.authenticate(username, password)

        if result["autenticado"]:
            # Guardar estado de sesión
            st.session_state[self.SESSION_AUTH_KEY] = True
            st.session_state[self.SESSION_PERFIL_KEY] = result["perfil"]
            st.session_state[self.SESSION_USUARIO_KEY] = result["usuario"]
            st.success(f"✅ ¡Bienvenido, {result['usuario']}!")
            st.rerun()
        else:
            st.error(f"❌ {result.get('error', 'Error de autenticación')}")

    def _render_sidebar_info(self) -> None:
        """
        Renderiza información del usuario en la sidebar (cuando ya está autenticado).
        """
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**👤 Usuario:** {self.get_username()}")
            st.markdown(f"**🎯 Perfil:** {self.get_user_profile()}")
            st.markdown("---")

            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                self.logout()
                st.rerun()


# --- FUNCIÓN COMPATIBLE CON EL CÓDIGO EXISTENTE ---
def generar_login():
    """
    Función de compatibilidad que mantiene la interfaz anterior.

    Crea un Authenticator con la estrategia por defecto
    y renderiza el formulario de login.

    NOTA: Esta función es un wrapper para mantener retrocompatibilidad.
    El nuevo código debe usar directamente la clase Authenticator.
    """
    from src.auth_strategies import HardcodedAuthStrategy

    # Usar estrategia por defecto si no existe en session_state
    if "authenticator" not in st.session_state:
        strategy = HardcodedAuthStrategy()
        st.session_state.authenticator = Authenticator(strategy)

    authenticator = st.session_state.authenticator
    authenticator.render_login_form()

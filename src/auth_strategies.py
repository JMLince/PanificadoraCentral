"""
Módulo de estrategias de autenticación.

Implementa el patrón Strategy para permitir diferentes mecanismos
de validación de credenciales de forma flexible y escalable.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd


class AuthStrategy(ABC):
    """
    Clase base abstracta que define la interfaz para estrategias de autenticación.

    Todas las estrategias concretas deben implementar el método authenticate()
    para validar las credenciales del usuario.
    """

    @abstractmethod
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Autentica un usuario con sus credenciales.

        Args:
            username (str): Nombre de usuario
            password (str): Contraseña

        Returns:
            Dict[str, Any]: Diccionario con los siguientes campos:
                - 'autenticado' (bool): True si las credenciales son válidas
                - 'perfil' (str): Rol del usuario (admin, panadero, encargado, etc.)
                - 'usuario' (str): Nombre completo o representación del usuario
                - 'error' (str, opcional): Mensaje de error si la autenticación falla
        """
        pass


class PandasAuthStrategy(AuthStrategy):
    """
    Estrategia de autenticación basada en un DataFrame de Pandas.

    Valida credenciales comparándolas contra registros en un DataFrame
    que contiene columnas: username, password, perfil, nombre_completo.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa la estrategia con un DataFrame de usuarios.

        Args:
            df (pd.DataFrame): DataFrame con columnas requeridas:
                - 'username': nombre de usuario
                - 'password': contraseña (idealmente hash, pero se valida plain)
                - 'perfil': rol del usuario
                - 'nombre_completo': nombre para mostrar en la interfaz
        """
        self.df = df
        self._validate_dataframe()

    def _validate_dataframe(self) -> None:
        """
        Valida que el DataFrame tenga las columnas necesarias.

        Raises:
            ValueError: Si falta alguna columna requerida
        """
        required_cols = {"username", "password", "perfil", "nombre_completo"}
        missing_cols = required_cols - set(self.df.columns)

        if missing_cols:
            raise ValueError(
                f"DataFrame debe contener las columnas: {required_cols}. "
                f"Faltan: {missing_cols}"
            )

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Valida credenciales contra el DataFrame de usuarios.

        Args:
            username (str): Nombre de usuario
            password (str): Contraseña

        Returns:
            Dict[str, Any]: Resultado de la autenticación con campos:
                - 'autenticado' (bool)
                - 'perfil' (str): Rol del usuario
                - 'usuario' (str): Nombre completo
                - 'error' (str, opcional): Mensaje de error
        """
        # Búsqueda en el DataFrame
        usuario_row = self.df[
            (self.df["username"].str.strip() == username.strip())
            & (self.df["password"].str.strip() == password.strip())
        ]

        if not usuario_row.empty:
            # Credenciales válidas
            return {
                "autenticado": True,
                "perfil": usuario_row.iloc[0]["perfil"],
                "usuario": usuario_row.iloc[0]["nombre_completo"],
            }
        else:
            # Credenciales inválidas
            return {
                "autenticado": False,
                "perfil": None,
                "usuario": None,
                "error": "Credenciales incorrectas",
            }


class HardcodedAuthStrategy(AuthStrategy):
    """
    Estrategia de autenticación con credenciales hard-coded en memoria.

    Útil para testing, desarrollo o cuando el conjunto de usuarios es muy pequeño.
    Los datos se definen en el constructor como un diccionario.
    """

    def __init__(self, users: Optional[Dict[str, Dict[str, str]]] = None):
        """
        Inicializa la estrategia con usuarios hard-coded.

        Args:
            users (Dict[str, Dict[str, str]]): Diccionario con estructura:
                {
                    'username': {
                        'password': 'clave',
                        'perfil': 'rol',
                        'nombre_completo': 'Nombre'
                    }
                }
        """
        self.users = users or self._default_users()

    @staticmethod
    def _default_users() -> Dict[str, Dict[str, str]]:
        """Retorna usuarios por defecto para testing."""
        return {
            "admin": {
                "password": "1234",
                "perfil": "admin",
                "nombre_completo": "Administrador",
            },
            "panadero": {
                "password": "5678",
                "perfil": "panadero",
                "nombre_completo": "Panadero",
            },
            "encargado": {
                "password": "2468",
                "perfil": "encargado",
                "nombre_completo": "Jefe de Planta",
            },
        }

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Valida credenciales contra los usuarios hard-coded.

        Args:
            username (str): Nombre de usuario
            password (str): Contraseña

        Returns:
            Dict[str, Any]: Resultado de la autenticación
        """
        user = self.users.get(username)

        if user and user.get("password") == password:
            return {
                "autenticado": True,
                "perfil": user["perfil"],
                "usuario": user["nombre_completo"],
            }
        else:
            return {
                "autenticado": False,
                "perfil": None,
                "usuario": None,
                "error": "Credenciales incorrectas",
            }

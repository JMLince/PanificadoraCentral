# Arquitectura de Autenticación - Patrón Strategy

## 📋 Descripción General

Se implementó el **patrón Strategy** para el sistema de login, permitiendo múltiples formas de autenticación de manera escalable y profesional.

### Archivos Creados/Modificados

1. **`src/auth_strategies.py`** (NUEVO)
   - Clase base abstracta `AuthStrategy`
   - Implementación `PandasAuthStrategy` (validación contra DataFrame)
   - Implementación `HardcodedAuthStrategy` (usuarios en memoria)

2. **`src/auth.py`** (REFACTORIZADO)
   - Clase `Authenticator` que coordina el flujo de login
   - Función `generar_login()` para retrocompatibilidad

3. **`produccion_v2.5.py`** (ACTUALIZADO)
   - Integración con la nueva clase `Authenticator`
   - Reemplazo de referencias antiguas con métodos de la clase

---

## 🏗️ Arquitectura

### Patrón Strategy

```
┌─────────────────────┐
│    AuthStrategy     │  (Clase base abstracta)
│   (ABC)             │
├─────────────────────┤
│ + authenticate()    │
└──────────┬──────────┘
           │
      ┌────┴────┬──────────────────┐
      │          │                  │
┌─────▼────────┐ │ ┌──────────────────┐
│  Pandas      │ │ │  Hardcoded       │
│  AuthStrategy│ │ │  AuthStrategy    │
│              │ │ │  (Testing)       │
│ (DataFrame)  │ │ │                  │
└──────────────┘ │ └──────────────────┘
                 │
             [Futura]
          OAuthStrategy,
          LDAPStrategy, etc.
```

### Flujo de Autenticación

```
Usuario
   │
   ├──> generar_login()
   │       │
   │       ├──> Authenticator.render_login_form()
   │       │       │
   │       │       ├──> Validar campos
   │       │       │
   │       │       └──> Authenticator._process_login()
   │       │               │
   │       └────────────────┤
   │                        │
   │                   Estrategia
   │                   .authenticate()
   │                        │
   │       ┌────────────────┴────────────────┐
   │       │                                 │
   │   ✅ Válido                          ❌ Inválido
   │       │                                 │
   │   Guardar en                       Error
   │   st.session_state                 (mensaje)
   │       │
   │   st.rerun()
   │
   └──> Acceso al Sistema
```

---

## 💡 Ejemplo de Uso

### 1. Uso Actual (Retrocompatible)

```python
from src.auth import generar_login

# En tu app.py o produccion_v2.5.py
generar_login()  # Maneja todo automáticamente
```

### 2. Uso Avanzado con Pandas

Si quieres cambiar a validación con Pandas:

```python
import pandas as pd
from src.auth import Authenticator
from src.auth_strategies import PandasAuthStrategy

# Crear DataFrame con usuarios
df_usuarios = pd.DataFrame({
    'username': ['admin', 'panadero', 'encargado'],
    'password': ['1234', '5678', '2468'],
    'perfil': ['admin', 'panadero', 'encargado'],
    'nombre_completo': ['Administrador', 'Panadero', 'Jefe de Planta']
})

# Crear estrategia y autenticador
strategy = PandasAuthStrategy(df_usuarios)
authenticator = Authenticator(strategy)

# Renderizar formulario
authenticator.render_login_form()

# Usar en la app
if authenticator.is_authenticated():
    perfil = authenticator.get_user_profile()
    usuario = authenticator.get_username()
    # ... resto de la lógica
```

### 3. Uso Avanzado con Hardcoded

```python
from src.auth import Authenticator
from src.auth_strategies import HardcodedAuthStrategy

custom_users = {
    'admin': {
        'password': 'super_secret_123',
        'perfil': 'admin',
        'nombre_completo': 'Admin del Sistema'
    },
    'panadero': {
        'password': 'panadero_123',
        'perfil': 'panadero',
        'nombre_completo': 'Mi Panadero'
    }
}

strategy = HardcodedAuthStrategy(users=custom_users)
authenticator = Authenticator(strategy)
authenticator.render_login_form()
```

---

## 🔑 API de la Clase `Authenticator`

### Métodos Públicos

```python
Authenticator(strategy: AuthStrategy)
    # Constructor: requiere una estrategia

.is_authenticated() -> bool
    # Retorna True si el usuario está autenticado

.get_user_profile() -> Optional[str]
    # Retorna el perfil del usuario (admin, panadero, etc.)

.get_username() -> Optional[str]
    # Retorna el nombre completo del usuario

.logout() -> None
    # Cierra la sesión y limpia st.session_state

.render_login_form() -> None
    # Renderiza el formulario (maneja autenticados y no autenticados)
```

---

## 🎯 Ventajas de Esta Arquitectura

| Aspecto | Beneficio |
|--------|-----------|
| **Escalabilidad** | Agrega nuevas formas de auth sin tocar el código existente |
| **Testabilidad** | Cada estrategia se prueba aislada |
| **Desacoplamiento** | El frontend (Streamlit) no conoce detalles de validación |
| **Reutilización** | Las estrategias pueden usarse en diferentes apps |
| **Mantenibilidad** | Código limpio, bien comentado y organizado |
| **Flexibilidad** | Cambiar de estrategia es trivial (solo una línea) |

---

## 🚀 Próximas Mejoras Posibles

1. **OAuthStrategy**: Integración con Google, GitHub, Azure AD
2. **DatabaseAuthStrategy**: Validación contra BD (SQLAlchemy)
3. **LDAPStrategy**: Autenticación contra directorio LDAP
4. **EncryptionMixin**: Encriptación de contraseñas (bcrypt, argon2)
5. **2FAStrategy**: Autenticación de dos factores
6. **SessionManager**: Manejo avanzado de sesiones y tiempos de expiración
7. **AuditLogger**: Logging de intentos de login (exitosos y fallidos)

---

## 📝 Notas Importantes

- **Retrocompatibilidad**: La función `generar_login()` sigue funcionando como antes
- **Estados de Sesión**: Las claves antiguas (`st.session_state.perfil`, etc.) están reemplazadas por métodos de `Authenticator`
- **Sin Emails**: El sistema usa solo `username` y `password` como se solicitó
- **Sin Hashing**: Por ahora se valida plain-text (considera agregar hashing en producción)

---

## 🔐 Recomendaciones de Seguridad (Futuro)

Para producción, se recomienda:

1. Usar hashing de contraseñas (bcrypt, argon2)
2. Almacenar contraseñas en variables de entorno o secretarios
3. Implementar rate limiting en intentos de login
4. Agregar logging de auditoría
5. Considerar HTTPS + sesiones seguras
6. Implementar expiración de sesiones
7. Usar CRSF tokens si es una web tradicional


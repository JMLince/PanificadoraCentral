# RESUMEN TÉCNICO ULTRA-COMPACTO: produccion_v2.5.py

## 📦 LIBRERÍAS CRÍTICAS IMPORTADAS

```python
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from fpdf import FPDF  # → fpdf2 en requirements.txt

# Módulos internos
from src.utils import aplicar_redondeo, guardar_en_historial, reservar_pedido, anular_pedido
from src.config_manager import cargar_ajustes, guardar_ajustes
from src.auth import generar_login
from src.report_generator import generar_pdf_produccion, exportar_pedido_pdf
```

---

## 💾 ESTRUCTURA DE `st.session_state`

### Inicialización Global (líneas ~155-175)

| Variable | Tipo | Descripción |
|---|---|---|
| `df_ajustes` | DataFrame | Maestro de ajustes (Masa Base, productos técnicos) |
| `items_nuevo_pedido` | **DataFrame** | Tabla editable con cols: `['Seleccionar', 'Producto', 'Unidades']` |
| `editor_version` | int | **Contador de versión para Key Versioning** (destruye/recrea widget) |

### En Modo Edición (líneas ~1695-1710)

| Variable | Tipo | Propósito |
|---|---|--|
| `pedido_en_edicion` | str/int | ID del pedido siendo editado |
| `estado_en_edicion` | str | Estado previo (Pendiente/Reservado) |
| `cliente_en_edicion` | str | "ID - Nombre" |
| `fecha_entrega_en_edicion` | date | Fecha destino |
| `obs_en_edicion` | str | Observaciones |

### Scroll & Detalle (líneas ~1905-1910)

| Variable | Tipo | Uso |
|---|---|---|
| `editor_nuevo_pedido_{editor_version}` | dict | Key dinámica del widget `st.data_editor` |
| `mostrar_detalle_pedido` | bool | Toggle para expandir detalle|
| `pedido_detalle_activo` | str/int | ID del pedido con detalle abierto |

---

## 🗂️ ESTRUCTURA CSV: `pedidos.csv`

**Ruta**: `data/pedidos.csv`

**Columnas**:
```
ID_Pedido | ID_Cliente | Cliente | Producto | Unidades | Fecha_Entrega | Estado | Fecha_Registro | Obs
```

**Estados válidos**: `"Pendiente"`, `"Reservado"`, `"Entregado"`, `"Anulado"`

**Nota**: El nuevo `productos_venta.csv` se propone para futura integración (no creado aún).

---

## ⚙️ FUNCIONES PERSONALIZADAS CLAVE

### 1️⃣ `apply_widget_edits()` (líneas ~1556-1610)

**Propósito**: Sincronización manual de cambios del `st.data_editor` al DataFrame capturado en session_state.

**Lógica**:
```python
def apply_widget_edits():
    current_key = f"editor_nuevo_pedido_{st.session_state.editor_version}"
    widget = st.session_state.get(current_key, {})
    edited_rows = widget.get("edited_rows", {})
    
    for idx_str, values in edited_rows.items():
        idx = int(idx_str)
        for col, val in values.items():
            st.session_state.items_nuevo_pedido.at[idx, col] = val
```

**Patrón**: Se llama ANTES de cualquier filtrado/borrado para asegurar sincronización.

---

### 2️⃣ `generar_pdf_remito(id_pedido, cliente, productos_items)` (líneas ~31-89)

**Propósito**: Genera PDF de remito en bytes (sin archivo temporal en disco).

**Inputs**:
- `id_pedido`: str/int
- `cliente`: str (nombre)
- `productos_items`: list de dicts `[{"Producto": str, "Unidades": int}, ...]`

**Output**: `bytes(pdf.output())` → compatible con `st.download_button`

**Estructura PDF**: Encabezado + ID + Cliente + Fecha + Tabla productos

---

## 🔄 LÓGICA DE BORRADO (Botón "🗑️ Borrar seleccionados")

**Orden atómico** (líneas ~1662-1683):

1. **Sincronización**: `apply_widget_edits()` captura cambios actuales
2. **Filtrado**: `df[df['Seleccionar'] == False].copy().reset_index(drop=True)`
3. **Asignación**: `st.session_state.items_nuevo_pedido = df_filtrado`
4. **Destrucción widget**: `st.session_state.editor_version += 1`
5. **Hard reload**: `st.rerun()`

**Debug**: Print en consola VS Code: `[DEBUG] Antes del filtrado: X filas`

---

## 🔐 KEY VERSIONING PATTERN

**Problema original**: Asignación directa a `st.session_state["editor_nuevo_pedido"]` → StreamlitAPIException

**Solución**: Use key dinámica que cambiar fuerza destrucción/reconstrucción

```python
key=f"editor_nuevo_pedido_{st.session_state.editor_version}"

# Al agregar/borrar/cancelar:
st.session_state.editor_version += 1
st.rerun()
```

---

## 📋 ESTADOS DE PEDIDO Y ACCIONES

| Estado | Botón "Modificar" | Botón "Remito" | Botón "Reservar" |
|---|---|---|---|
| **Pendiente** | ✅ Activo | ❌ Deshabilitado | ✅ Activo |
| **Reservado** | ✅ Activo | ✅ **Activo** | ❌ Gris (ya reservado) |
| **Entregado** | ❌ No aparece | ❌ No aparece | ❌ No aparece |

**Al Modificar**: Estado se preserva (`estado_en_edicion` → `estado_para_guardar`)

---

## 📍 TABLAS HTML Y SCROLL

- **Ancla**: `<div id="scroll-to-editor"></div>` (línea ~1255)
- **Script JS**: setTimeout(500ms) para cambio de tab + scroll suave (línea ~2005-2015)
- **Disparador**: Botón "✏️ Modificar" en Pedidos Programados

---

## 🚀 PRÓXIMAS INTEGRACIONES

- **productos_venta.csv**: Campos propuestos = `[ID, Nombre, PrecioUnitario, Stock, ...]`
- **Integración Remito**: Agregar PrecioUnitario × Unidades en tabla PDF
- **Estados avanzados**: Workflow Pendiente → Reservado → Entregado

---

## 📊 MÉTRICAS UBICACIÓN CLAVE

| Concepto | Línea Approx |
|---|---|
| Inicialización session_state | 155-175 |
| generar_pdf_remito() | 31-89 |
| apply_widget_edits() | 1556-1610 |
| Botón Borrar lógica | 1662-1683 |
| Botón Remito condicional | 2187-2220 |
| Estilos CSS | ~85-140 |

---

**Versión**: 2.5 | **Fecha**: 27 Feb 2026 | **Contexto**: Ultra-compacto para limit tokens

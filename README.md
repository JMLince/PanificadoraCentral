# PanificadoraCentral

**Sistema de Gestión de Producción y Pedidos para Panificación Industrial**

Herramienta operacional completa desarrollada en Python y Streamlit, diseñada para reemplazar el proceso manual y propenso a errores de planificación de producción en una empresa de panificación industrial. Actualmente en uso operativo diario.

---

## El problema

La empresa no contaba con ninguna herramienta dinámica para gestionar los objetivos de producción diarios entre múltiples productos. El sistema existente era estático, no generaba análisis ni ofrecía soporte de planificación — lo que derivaba en faltantes de mercadería recurrentes, entregas incumplidas y cálculos manuales que requerían controlar múltiples variables al mismo tiempo.

El flujo de pedidos no se respetaba y nadie podía acordar un horario de corte. En lugar de esperar una solución externa, construí el sistema.

---

## La solución

Un modelo de producción por umbrales que persigue la demanda, con parámetros configurables por producto, combinado con gestión de pedidos externos firmes — todo unificado en una salida consolidada que le indica al área de producción exactamente qué fabricar y en qué cantidad.

**Decisiones de diseño clave:**

- **Modelo de umbrales**: cada producto tiene parámetros configurables de mínimo, medio y máximo de producción. El sistema persigue la demanda dinámicamente sin necesidad de una lista de pedidos cerrada.
- **Doble manejo de pedidos**: la demanda interna (por umbrales) y los pedidos externos firmes (cantidades exactas) se calculan por separado y se fusionan en un único plan de producción.
- **Consolidación de ingredientes**: los productos están definidos como subconjuntos de masas base, por lo que la salida es una lista unificada de requerimientos de masas e ingredientes — no solo un conteo de productos.

---

## Funcionalidades

- **Planificación de producción** — objetivos diarios dinámicos por producto basados en umbrales
- **Gestión de pedidos** — ciclo de vida completo: Pendiente → Reservado → Entregado → Anulado
- **Edición en tiempo real** — modificación de pedidos mediante `st.data_editor` con patrón Key Versioning
- **Generación de PDF** — exportación automática de remitos vía fpdf2
- **Autenticación de usuarios** — sistema de login mediante `src/auth`
- **Gestión de configuración** — ajustes persistentes mediante `src/config_manager`
- **Historial de auditoría** — seguimiento de pedidos y registros históricos

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend / UI | Streamlit |
| Procesamiento de datos | Python · Pandas |
| Generación de PDF | fpdf2 |
| Almacenamiento | CSV (pipelines con Pandas) |
| Control de versiones | Git · GitHub |

---

## Estructura del proyecto

```
PanificadoraCentral/
├── produccion_v2.5.py      # Punto de entrada principal
├── requirements.txt
├── src/
│   ├── auth.py             # Autenticación de usuarios
│   ├── config_manager.py   # Persistencia de configuración
│   ├── report_generator.py # Generación de PDF y remitos
│   └── utils.py            # Utilidades compartidas
├── data/                   # Archivos CSV
├── assets/                 # Recursos estáticos
└── .streamlit/             # Configuración de Streamlit
```

---

## Instalación y ejecución local

```bash
# Clonar el repositorio
git clone https://github.com/JMLince/PanificadoraCentral.git
cd PanificadoraCentral

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run produccion_v2.5.py
```

---

## Estado del proyecto

**Activo — v2.5**
En uso operativo diario. El desarrollo continuo incluye integración de catálogo de productos en CSV, precios unitarios en remitos y flujos de estado de pedidos ampliados.

---

---

# PanificadoraCentral

**Production & Order Management System for Food Manufacturing**

A full-stack operational tool built with Python and Streamlit, designed to replace manual, error-prone production planning processes at a food manufacturing company. Currently in active daily use.

---

## The Problem

The company had no dynamic tool to manage daily production targets across multiple SKUs. The existing system was static, provided no analysis, and generated no planning support — leading to recurring stockouts, missed delivery windows, and time-consuming manual calculations across multiple variables simultaneously.

Nobody could agree on a cutoff time for orders. The workflow wasn't being followed. So I built a system that didn't need it to be.

---

## The Solution

A demand-following production planning model with configurable thresholds per product, combined with firm external order management — unified into a single consolidated output that tells the production floor exactly what to make and how much.

**Key design decisions:**

- **Threshold model**: each product has configurable min/mid/max production targets. The system chases demand dynamically rather than waiting for a closed order list.
- **Dual order handling**: internal demand (threshold-based) + external firm orders (exact quantities) are calculated separately and merged into a single production plan.
- **Ingredient rollup**: products are defined as sub-components of base doughs/masses, so the output is a unified ingredient/dough requirements list — not just a product count.

---

## Features

- **Production planning** — dynamic threshold-based daily targets per SKU
- **Order management** — full lifecycle: Pending → Reserved → Delivered → Cancelled
- **Inline editing** — real-time order editing via `st.data_editor` with Key Versioning pattern
- **PDF generation** — automated remito (delivery note) export via fpdf2
- **User authentication** — login system via `src/auth`
- **Configuration management** — persistent settings via `src/config_manager`
- **Audit history** — order tracking and historical records

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Data processing | Python · Pandas |
| PDF generation | fpdf2 |
| Data storage | CSV (Pandas pipelines) |
| Version control | Git · GitHub |

---

## Project Structure

```
PanificadoraCentral/
├── produccion_v2.5.py      # Main application entry point
├── requirements.txt
├── src/
│   ├── auth.py             # User authentication
│   ├── config_manager.py   # Settings persistence
│   ├── report_generator.py # PDF report & remito generation
│   └── utils.py            # Shared utilities
├── data/                   # CSV data files
├── assets/                 # Static assets
└── .streamlit/             # Streamlit configuration
```

---

## Running Locally

```bash
git clone https://github.com/JMLince/PanificadoraCentral.git
cd PanificadoraCentral
pip install -r requirements.txt
streamlit run produccion_v2.5.py
```

---

## Status

**Active — v2.5**
In daily operational use. Ongoing development includes product catalog CSV integration, unit pricing in remitos, and extended order state workflows.

---

## About

Built by Jorge Martin Lince — operations and procurement professional with 14 years in food manufacturing, self-taught Python developer.

[GitHub](https://github.com/JMLince) · Open to remote opportunities in data analysis, AI data operations, and QA.

# BienestarEnCasa

Sistema web de servicios de estética y bienestar a domicilio desarrollado con **Django**, **Django REST Framework**, **SimpleJWT** y **MySQL** (con respaldo automático en SQLite para desarrollo local).

---

## Estructura del Proyecto

```text
BienestarEnCasa/
├── README.md
├── .gitignore
├── docs/                                         # Documentación técnica y reportes del proyecto
│   ├── Informe_Tecnico_BienestarEnCasa_Sprint3.pdf
│   ├── DOCUMENTACION_SPRINT3_Y_CORRECCIONES.md
│   └── reporte_paginas_urls.txt
├── Backend/
│   ├── .env.example                              # Plantilla de conexión a MySQL
│   ├── manage.py
│   ├── requirements.txt
│   ├── BienestarEnCasa/                          # Configuración global (settings, urls, paginas_urls)
│   ├── usuarios/                                 # Autenticación JWT, perfiles, direcciones, zonas y disponibilidad
│   │   ├── migrations/
│   │   ├── urls/
│   │   └── tests/
│   │       ├── test_autenticacion.py             # HU-01, HU-02, HU-03
│   │       ├── test_perfil_cliente.py            # HU-04
│   │       └── test_perfil_proveedor.py          # HU-05
│   ├── catalogo/                                 # Categorías, servicios, multimedia y elementos
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── test_catalogo_api.py              # HU-06 a HU-10
│   │       └── test_paginas_y_regresion.py       # Páginas HTML, seed de categorías y disponibilidad
│   └── solicitudes/                              # Creación, límites, negociación, cancelación y cierre
│       ├── migrations/
│       └── tests/
│           ├── test_creacion_y_limites.py        # HU-12, HU-13, HU-14, HU-19
│           └── test_sprint3_negociacion_cierre.py # HU-15, HU-16, HU-17, HU-18 y E2E Sprint 3
└── frontend/
    ├── static/                                   # estilos.css y logo.png
    └── templates/                                # Vistas HTML organizadas por módulo (users, catalogo, solicitudes)
```

---

## Instalación y Ejecución

### 1. Crear entorno virtual e instalar dependencias

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r Backend\requirements.txt
```

### 2. Configurar la base de datos

- **Con MySQL (equipo / presentación):** copia `Backend/.env.example` a `Backend/.env` y completa `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`.
- **Con SQLite (local sin MySQL):** si no existe `Backend/.env` (o defines `USE_SQLITE=true`), Django usará `Backend/db.sqlite3` automáticamente.

### 3. Aplicar migraciones y arrancar el servidor

```powershell
python Backend\manage.py migrate
python Backend\manage.py runserver
```

> Las migraciones incluyen el sembrado automático de categorías iniciales (`catalogo.0005_seed_categorias_iniciales`) y los campos del Sprint 3 (`solicitudes.0005_sprint3_negociacion_cierre`) sin afectar datos previos en MySQL.

---

## Funcionalidades por Sprint

- **Sprint 1 (HU-01 a HU-10):** registro por rol, inicio/cierre de sesión JWT en cookies `HttpOnly` con sesión única y CSRF, recuperación de contraseña, perfil/direcciones de cliente, perfil profesional/zonas de proveedor, catálogo de servicios con multimedia e insumos, búsqueda y perfiles públicos.
- **Sprint 2 (HU-11 a HU-14 y HU-19):** disponibilidad semanal y periodos no disponibles del proveedor, creación de solicitudes con validación de horarios y límites por cliente (sin traslapes y máximo 3 activas/día), consulta de solicitudes y agenda del proveedor.
- **Sprint 3 (HU-15 a HU-18):**
  - **HU-15:** aceptar, rechazar (con motivo obligatorio) o contraproponer fecha/hora desde el panel del proveedor (`POST /api/solicitudes/{id}/aceptar|rechazar|contraproponer/`).
  - **HU-16:** aceptar o rechazar contrapropuestas desde la vista del cliente (`POST /api/solicitudes/{id}/aceptar-contrapropuesta|rechazar-contrapropuesta/`).
  - **HU-17:** cancelación con motivo obligatorio por cliente o proveedor y liberación automática del horario (`POST /api/solicitudes/{id}/cancelar/`).
  - **HU-18:** finalización del servicio por el proveedor con observaciones opcionales e inmutabilidad posterior (`POST /api/solicitudes/{id}/finalizar/`).

---

## Pruebas Automatizadas

Ejecutar la suite completa (**86 pruebas**):

```powershell
python Backend\manage.py test usuarios catalogo solicitudes
```

Ejecutar por módulo o solo Sprint 3:

```powershell
python Backend\manage.py test usuarios
python Backend\manage.py test catalogo
python Backend\manage.py test solicitudes.tests.test_sprint3_negociacion_cierre
```

---

## Documentación Adicional

- [docs/Informe_Tecnico_BienestarEnCasa_Sprint3.pdf](docs/Informe_Tecnico_BienestarEnCasa_Sprint3.pdf): informe técnico en PDF listo para presentar (arquitectura MySQL/SQLite, Sprint 3, errores corregidos, metodología y detalle de las 86 pruebas automatizadas, y checklist de demostración).
- [docs/DOCUMENTACION_SPRINT3_Y_CORRECCIONES.md](docs/DOCUMENTACION_SPRINT3_Y_CORRECCIONES.md): referencia en Markdown con arquitectura, base de datos, endpoints, correcciones aplicadas y guion de demostración.

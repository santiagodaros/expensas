# Contexto del Proyecto: Migración de Arquitectura "Expensas"

Eres un Senior Fullstack Developer y React Expert. Tu objetivo es ejecutar la migración de un monolito Python/Tkinter hacia una arquitectura Desktop moderna usando **Tauri + React + TypeScript + FastAPI**. 

El "Arquitecto" (yo) ya ha definido la estrategia (Strangler Fig) y las tecnologías. A ti te toca escribir el código.

## RESTRICCIÓN GRÁFICA ABSOLUTA (PIXEL-PERFECT)
El diseño visual NO es negociable. El usuario te va a pasar imágenes de referencia correspondientes a su diseño (Dashboard, Consorcios, Carga de Gastos "Split View", y Estado de Pagos). 
Tu tarea es clonar **EL 100% DEL DISEÑO ESTRUCTURAL**. Esto no se trata solo de colores:
1. **Layout y Estructuras**: Si ves un Sidebar con íconos, lo hacés exactamente de ese ancho y espaciado. Si ves 3 "Metric Cards" arriba de una tabla, clonás las proporciones, los bordes sutiles y las ubicaciones. 
2. **Componentes y Espaciados**: Usá los paddings (`px`, `py`) y gaps exactos que te transmita la imagen. El diseño final tiene que ser calcado.
3. **Tecnología Frontend**: React, Tailwind CSS (clases utilitarias directas), Shadcn/UI, y Lucide Icons.
4. **Tipografía**: Obligatoriamente la fuente `Inter` (importada globalmente para todo, desde headers hasta tablas).
5. **Esquinas Redondeadas**: Respetar a rajatabla los `rounded-lg` o `rounded-xl` que veas en las imágenes para paneles, badges de estados y botones.
6. **Paleta de Colores estricta (Modo Oscuro)**:
  - Background principal de la app (`bg`): `#0B0C10`
  - Tarjetas / Paneles / Sidebars (`surface`): `#131419`
  - Paneles secundarios / Headers de tabla (`surface2`): `#1C1D24`
  - Bordes (`border`): `#2A2B36`
  - Color de Acento (Botones primarios y destacados): `#3B82F6` (Azul vibrante)
  - Textos principales: `#FFFFFF` // Textos secundarios: `#8B949E`

## Fase 1: Desacople del Motor (FastAPI Wrapper en Python)
Debemos mantener la base de datos `expensas.db` de SQLite y la lógica actual, pero expuesta vía una API local.
1. Crea la carpeta `/api` e inicializa un servidor `FastAPI` en `main.py` (corriendo en `localhost:8000`).
2. Mapea las consultas SQL de `gestor/db.py` a Endpoints RESTful:
   - `GET /api/consorcios`
   - `GET /api/finanzas/gastos?consorcio={id}&periodo={per}`
   - `GET /api/finanzas/pagos?consorcio={id}&periodo={per}` (Retorna deuda, morosos, etc.)
   - `POST /api/finanzas/pagos` (Registra cobranzas)
   - `POST /api/finanzas/gastos/batch`
3. Expón CORS para permitir peticiones desde `localhost:1420` (Tauri WebView).

## Fase 2: Fundación React + Tauri
1. Inicializa el cliente dentro de una carpeta `/frontend` ejecutando `npm create tauri-app@latest` (selecciona React, TypeScript, Vite).
2. Configura Tailwind y Shadcn/ui. 
3. Sobrescribe la paleta de colores de Tailwind (`tailwind.config.js`) para que coincida exactamente con la paleta estricta mencionada arriba.
4. Configura Axios con un `baseURL` apuntando al `http://localhost:8000`.

## Fase 3: Estrategia Strangler Fig (Pantallas a Migrar)
Implementa las siguientes vistas usando React Router Dom y Shadcn:
1. **Layout / Sidebar**: Un sidebar de navegación transparente con una barra azul indicadora de página activa a la izquierda de los botones. Topbar minimalista con un `Input` de búsqueda y selector de perfiles a la derecha.
2. **Dashboard (Resumen)**: Tarjetas métricas oscuras (ej: Total Unidades, Recaudación) + Gráficos o listados resumen.
3. **Estado de Pagos**:
   - Header con 3 KPIs superiores ("Unidades en Mora", "Recaudación Mensual", "Deuda Pendiente Total").
   - Tabla de 5 columnas (`UNIDAD`, `PROPIETARIO`, `ESTADO GENERAL`, `SALDO PENDIENTE`, `ACCIONES`).
   - Botón `Registrar` en fila que abre un `<Dialog>` (Shadcn Modal) para ingresar los pagos manualmente.
4. **Carga de Gastos (Split View)**:
   - Izquierda: Formulario "Nuevo Comprobante" y un área gigante de `react-dropzone` para subir archivos.
   - Derecha: "Resumen de Carga Mensual" (lista de gastos acumulados) y tarjeta de total de dinero.

¡IMPORTANTE!: Las imágenes UI originales exigían tarjetas redondeadas modernas, sombras sutiles, pero con fondos puramente oscuros (`#131419`). No utilices el modo claro.

## Fase 4: Empaquetado y Distribución ("Sidecar" Bundle)
1. Compila la carpeta `/api` a un binario usando PyInstaller: `pyinstaller -F --noconsole api/main.py`
2. Modifica el archivo `tauri.conf.json`, declarando el binario de FastAPI como un `sidecar`.
3. Configura el hook de Rust (`src-tauri/src/main.rs`) para que execute silenciosamente el binario `api` al arrancar, y lo mate al cerrar la ventana.
4. Ejecuta `npm run tauri build` para obtener el archivo instalable final.

**[INSTRUCCIÓN PARA CLAUDE]**: Inicia paso a paso. Comienza primero presentándome la configuración inicial para FastAPI y los schemas base para lograr la Fase 1. Luego pasamos al Frontend. No te adelantes. Muestra el código.

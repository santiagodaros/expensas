# Roadmap: Evolución a Sistema Profesional de Expensas

**Estrategia de Desarrollo:**
1. **Etapa Actual (Fases 1 a 3):** Solución 100% funcional, ejecutada localmente y de **COSTO CERO** (Tauri + SQLite). Diseñada a medida para el uso personal de una sola administración (uso interno).
2. **Etapa Futura (Fase 4):** Evolución técnica *opcional* para convertirla en un producto en la Nube (SaaS B2B) en caso de querer comercializarlo a terceros.

Este documento define la hoja de ruta para cubrir la necesidad inmediata, dejando la puerta abierta a la expansión futura.

## FASE 1: El Corazón Contable y Legal (Prioridad: Crítica)
El sistema actual agrupa todo bajo un concepto único de "Gastos" y prorratea directamente. Para ser legal y financieramente robusto, necesitamos estructurar las responsabilidades.

### 1. Ordinarias, Extraordinarias y Gastos Particulares (P0)
*   **Contexto:** Diferenciación fundamental entre inquilino (Ordinarias) y propietario (Extraordinarias). 
*   **Funcionalidades:**
    *   Nuevo campo en Gastos para clasificar tipo (Ordinario / Extraordinario).
    *   Módulo de **Gastos Particulares**: Imputación directa de un monto a un `unidad_id` específico sin pasar por el coeficiente (Ej: Multas, reserva de SUM, roturas puntuales).
    *   Generación del PDF de la Boleta separando claramente ambos subtotales.

### 2. Registro de Proveedores - ABM (P1)
*   **Contexto:** Un gasto no aparece de la nada; alguien prestó un servicio o vendió un bien.
*   **Funcionalidades:**
    *   ABM de Proveedores: Razón Social, CUIT, Domicilio, Categoría AFIP, CBU.
    *   Relación de 1 a N: Cada `Gasto` debe tener un `proveedor_id` asociado.
    *   Listado de cuenta corriente de proveedores (Saber a nivel sistema "Le debo $X al plomero").

### 3. Gestión de Sueldos y Cargas Sociales (P1)
*   **Contexto:** Separar conceptualmente una compra en la ferretería de los aportes sindicales y el sueldo del encargado.
*   **Funcionalidades:**
    *   Módulo simplificado de carga de recibos de sueldos y aportes (SUTERH / FATERYH).
    *   Impacto automático de estas cargas sociales en el libro de gastos como Gastos Ordinarios.

---

## FASE 2: Recaudación Inteligente y Cobranzas (Prioridad: Alta)
Actualmente el administrador debe "perseguir" pagos e imputar todo a mano. Esto frena la escala operativa.

### 1. Intereses Punitorios Parametrizables
*   **Funcionalidades:**
    *   Configuración a nivel `Consorcio` de tasa de recargo y algoritmo (Capitalización, diario vs mensual, día de gracia).
    *   Cálculo automático de la deuda en tiempo real en la pantalla de "Estado de Pagos".

### 2. Integración de Pagos y Conciliación Bancaria
*   **Funcionalidades:**
    *   Módulo de Importación Bancaria: Subir un reporte `.csv` del banco para matchear transferencias de los inquilinos y autorregistrar pagos (Conciliación Automática).
    *   *(A futuro)* Integración con Webhooks: SIRO (Banco Roela), MercadoPago o PagoMisCuentas para automatización 100%.

---

## FASE 3: Portal de Autogestión y Comunidad (Prioridad: Media)
Sacar al administrador como "cuello de botella" de la información. Empoderar a los copropietarios.

### 1. Portal Avanzado de Propietarios/Inquilinos (Self-Service & Transparencia)
*   **Contexto:** El portal no es solo para visualizar PDFs, es la principal herramienta de "Transparencia Activa", fidelización y automatización de cobranzas (vía Open Banking).
*   **Funcionalidades Principales:**
    *   **Dashboard Financiero del Mes:** El usuario logueado ve un desglose en tiempo real (ej. gráfico de torta) de en qué se está gastando el presupuesto del consorcio *este mes* (Sueldos, Mantenimiento, Seguros). Esto mata la desconfianza clásica hacia los administradores.
    *   **Cuenta Corriente Personal (Historial):** Un "home banking" de la unidad. Muestra el historial inmutable de: expensas emitidas, notas de crédito, pagos realizados, intereses punitorios calculados al día y el saldo actual (a favor o en deuda).
    *   **Pasarela de Pago Inteligente (QR Interoperable / Open Banking):**
        *   Generación directa de un **código QR dinámico** (estándar BCRA 3.0) vinculado al saldo exacto adeudado y al CVU/CBU del consorcio.
        *   El usuario lo escanea con *cualquier* billetera (MercadoPago, MODO, Cuenta DNI, Ualá).
        *   El sistema escucha los *Webhooks* bancarios: tan pronto el usuario paga, el banco avisa a la API, el pago se asienta solo, el estado de la deuda baja a cero, y se dispara un email automático con el recibo de pago al inquilino. Cero intervención humana.
    *   **Gestión Documental:** Repositorio para descargar PDFs históricos y subir comprobantes manuales (en caso de pagos en efectivo o transferencias manuales que requieran validación).

### 2. Repositorio Documental
*   **Funcionalidades:**
    *   Espacio en la nube (ej: carpetas locales o S3) atado al consorcio para alojar: Reglamento de Copropiedad, Actas de Asambleas, Pólizas de Seguro.

---

## FASE 4 (Visión Futura Comercial): Arquitectura SaaS B2B y Auditoría Financiera
Convertir el MVP de una herramienta local a un producto comercial en la Nube, vendible como suscripción (SaaS) a múltiples Administraciones simultáneamente.

### 1. Arquitectura Multi-Tenant (Múltiples Clientes)
*   **Contexto:** Un "Tenant" (Inquilino lógico) en este caso es una **Administración de Consorcios**. Cada Administración maneja sus N Consorcios.
*   **Funcionalidades:**
    *   Migración de base de datos a PostgreSQL (para soportar concurrencia masiva).
    *   Diseño de *Row-Level Security* (RLS) o *Schema-per-tenant*: Asegura a nivel base de datos que la Administración "Pérez" jamás pueda acceder, ver, o pisar los datos de la Administración "Gómez".
    *   Panel global de SuperAdmin (Vos) para habilitar, suspender o cobrar licencias a las distintas Administraciones.

### 2. Audit Trails y Logs Financieros Inmutables
*   **Contexto:** En finanzas y contabilidad, nada se "borra", se anula. Y todo cambio debe dejar un rastro legal.
*   **Funciones Core:**
    *   **Inmutabilidad (Soft-Delete):** Se prohíbe el uso de comandos `DELETE` en tablas financieras. Los registros erróneos se marcan inactivos (`deleted_at`) pero quedan en la historia.
    *   **Historial de Cambios (Audit Logs):** Cada vez que un Gasto o Pago se edita (ej: cambian un monto de $50k a $5k), el sistema guarda un log automático: *¿Quién modificó? ¿A qué hora? ¿Desde qué IP? ¿Cuál era el valor anterior (Before Mismatch) y el nuevo (After)?*.
    *   **Respaldo Legal:**  Si hay un fraude por parte de un administrador o una auditoría contable al consorcio, tu software emite un reporte irrefutable de todo lo que pasó con la plata en el sistema.

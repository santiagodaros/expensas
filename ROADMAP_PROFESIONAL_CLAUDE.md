# Roadmap: Evolución a Sistema Profesional de Expensas

Este documento define la hoja de ruta arquitectónica y funcional para llevar el actual MVP de gestión de expensas hacia un sistema profesional de administración de consorcios, listo para competir en el mercado.

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

### 1. Portal de Propietarios/Inquilinos (Self-Service)
*   **Funcionalidades:**
    *   Web/App simplificada con login (JWT) donde la unidad puede ver su saldo actual.
    *   Descarga de comprobantes y últimos PDFs generados.
    *   Botonera directa de Pago.

### 2. Sistema de Tickets y Reclamos
*   **Funcionalidades:**
    *   Propietario levanta ticket de mantenimiento.
    *   El administrador evalúa y asigna el ticket a un "Proveedor" (Creado en Fase 1).

### 3. Repositorio Documental
*   **Funcionalidades:**
    *   Espacio en la nube (ej: carpetas locales o S3) atado al consorcio para alojar: Reglamento de Copropiedad, Actas de Asambleas, Pólizas de Seguro.

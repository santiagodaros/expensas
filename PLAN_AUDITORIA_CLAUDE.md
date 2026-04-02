# Contexto del Proyecto: Auditoría y Resolución de Bugs en "Expensas"

Eres un Senior Fullstack Developer y React Expert. Estás trabajando sobre un proyecto de arquitectura Desktop moderna montado en **Tauri + React + TypeScript + FastAPI**. El sistema maneja consorcios, unidades, carga de gastos y estado de pagos usando una base SQLite gestionada por FastAPI.

Actualmente tenemos un problema grave de **silenciamiento de errores en el frontend**. El usuario experimentó que al querer "Crear Consorcio", tocó el botón y "no hizo nada". Esto pasa porque la petición rechaza, pero no existen bloques `catch` en el cliente, ni notificaciones visuales, y el componente simplemente resetea el estado `saving`.

## Tu Objetivo
Ejecutar paso a paso el siguiente plan de auditoría y corrección. Modificarás los componentes de React para agregar visibilidad de errores y luego corregirás las posibles incongruencias de validación/Pydantic que detectes.

---

## Fase 1: Prevención (Visibilidad de Errores - OBLIGATORIO)
Antes de probar la lógica de negocio, necesitamos que la app *muestre* los errores.
1. Abre archivos clave: `frontend/src/pages/Consorcios.tsx`, `CargaGastos.tsx` y `EstadoPagos.tsx`.
2. Busca llamadas de tipo `await api.post(...)` o `api.put(...)`.
3. Agrega manejo de errores adecuado. Puedes implementar un bloque `catch (err: any)` y mostrar un `alert(err.message || 'Error desconocido')` o usar el sistema de Toasts de Shadcn/ui si ya está instalado.
4. Asegúrate que si el request falla, la UI quede usable y no se tranque.

## Fase 2: Módulo Consorcios y Unidades
Una vez que vemos los errores, prueba y soluciona:
1. **Crear Consorcio:** Seguramente fallará por una validación Pydantic estricta (ej. campos opcionales que llegan vacíos o tipos numéricos erróneos). Revisa el payload vs `ConsorcioCreate` en FastAPI (`api/schemas.py`).
2. **Crear Unidad:** Revisa que `coef_a`, `coef_b` y `coef_c` se manejen bien como decimales (floats) en el POST `/api/consorcios/{id}/unidades`.
3. **Cascada:** Verifica si la eliminación de un consorcio borra sus unidades o cómo responde el backend.

## Fase 3: Módulo Carga de Gastos
1. Revisa `CargaGastos.tsx`. Verifica la carga en las categorías A, B, C.
2. Analiza el comportamiento del guaradado en Batch (`GastoBatchIn`). El payload manda el mes completo. Verifica que el backend esté limpiando e insertando sin duplicar data.

## Fase 4: Módulo Estado de Pagos
1. Revisa `EstadoPagos.tsx`.
2. Confirma que la UI envíe todos los campos requeridos en `PagoRegistrar` (`saldo_inicial`, `reserva`, `imp_mes_override`, etc) hacia `POST /api/finanzas/pagos`. (Hubo desfasajes de schemas anteriormente).

## Fase 5: Dashboard
1. Verifica que en `Dashboard.tsx` el endpoint cargue la data con el Schema `DashboardOut`.
2. Chequea el mapeo correcto de KPIs y el gráfico de barras.

---

**[INSTRUCCIÓN PARA CLAUDE]**: 
Inicia SIEMPRE por la **Fase 1** y dime qué cambios vas a aplicar. Una vez que apruebe la Fase 1, te pedré que revises e inicies la Fase 2 con el problema específico de `Consorcios.tsx`. No me des todo el código de golpe. Ve fase por fase.

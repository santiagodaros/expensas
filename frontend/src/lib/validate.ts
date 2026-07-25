import { toast } from "sonner";

/**
 * Reemplaza las cadenas repetidas de `if (!x) { toast.error(...); return; }`
 * que se repetian en cada formulario. Sin dependencias nuevas (no hay forma de
 * instalar paquetes en este entorno para verificar que compilen) — es deliberadamente
 * minimo en vez de traer una libreria de schemas.
 *
 * Uso:
 *   if (!validate(
 *     [!!form.descripcion.trim(), "Ingresa una descripcion"],
 *     [form.monto > 0, "El monto debe ser mayor a cero"],
 *   )) return;
 */
export function validate(...checks: Array<[boolean, string]>): boolean {
  for (const [ok, message] of checks) {
    if (!ok) {
      toast.error(message);
      return false;
    }
  }
  return true;
}

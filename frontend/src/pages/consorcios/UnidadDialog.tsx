import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useGet } from "@/hooks/useApi";
import { Unidad, UnidadCreate } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Field, TInput } from "@/components/ui/form-field";

const EMPTY_U: UnidadCreate = { unidad: "", piso: "", dpto: "", propietario: "", inquilino: "", coef_a: 0, coef_b: 0, coef_c: 0, email: "", saldo_apertura: 0 };

export function UnidadDialog({ consorcioId, initial, onClose, onSaved }: { consorcioId: number; initial?: Unidad; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<UnidadCreate>(
    initial
      ? { unidad: initial.unidad, piso: initial.piso, dpto: initial.dpto, propietario: initial.propietario ?? "", inquilino: initial.inquilino ?? "", coef_a: initial.coef_a, coef_b: initial.coef_b, coef_c: initial.coef_c, email: initial.email ?? "", saldo_apertura: initial.saldo_apertura }
      : { ...EMPTY_U }
  );
  const saldoEditable = !initial || initial.saldo_apertura_editable;
  const [saving, setSaving] = useState(false);
  const set = (k: keyof UnidadCreate, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  // Suma de coef_a del resto de las unidades del consorcio, para avisar si
  // esta unidad deja el total lejos del 100% esperado.
  const { data: otrasUnidades } = useGet<Unidad[]>(`/api/consorcios/${consorcioId}/unidades`);
  const sumaResto = (otrasUnidades ?? [])
    .filter((u) => !initial || u.id !== initial.id)
    .reduce((s, u) => s + (u.coef_a || 0), 0);
  const sumaTotal = sumaResto + (form.coef_a || 0);
  const coefDesviado = otrasUnidades && Math.abs(sumaTotal - 100) > 2;

  const handleSave = async () => {
    if (!form.unidad.trim()) return;
    setSaving(true);
    try {
      initial ? await api.put(`/api/unidades/${initial.id}`, form) : await api.post(`/api/consorcios/${consorcioId}/unidades`, form);
      onSaved(); onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error desconocido");
    } finally { setSaving(false); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="bg-surface border-border text-text">
        <DialogHeader><DialogTitle className="text-text">{initial ? "Editar Unidad" : "Nueva Unidad"}</DialogTitle></DialogHeader>
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-3 gap-3">
            <Field label="Unidad *"><TInput value={form.unidad} onChange={(e) => set("unidad", e.target.value)} placeholder="1A" /></Field>
            <Field label="Piso"><TInput value={form.piso} onChange={(e) => set("piso", e.target.value)} placeholder="1" /></Field>
            <Field label="Dpto"><TInput value={form.dpto} onChange={(e) => set("dpto", e.target.value)} placeholder="A" /></Field>
          </div>
          <Field label="Propietario"><TInput value={form.propietario ?? ""} onChange={(e) => set("propietario", e.target.value)} placeholder="Juan Garcia" /></Field>
          <Field label="Inquilino"><TInput value={form.inquilino ?? ""} onChange={(e) => set("inquilino", e.target.value)} placeholder="Maria Lopez" /></Field>
          <Field label="Email"><TInput type="email" value={form.email ?? ""} onChange={(e) => set("email", e.target.value)} placeholder="correo@ejemplo.com" /></Field>
          <Field label="Saldo inicial (deuda arrastrada; negativo = a favor)">
            <TInput
              type="number"
              value={form.saldo_apertura}
              onChange={(e) => set("saldo_apertura", parseFloat(e.target.value) || 0)}
              disabled={!saldoEditable}
              step={0.01}
            />
          </Field>
          {!saldoEditable && (
            <p className="text-xs text-text2">
              No editable: la unidad ya tiene pagos registrados. El saldo se sigue calculando a partir de ese historial.
            </p>
          )}
          <div className="grid grid-cols-3 gap-3">
            <Field label="Coef A"><TInput type="number" value={form.coef_a} onChange={(e) => set("coef_a", parseFloat(e.target.value) || 0)} step={0.001} min={0} /></Field>
            <Field label="Coef B"><TInput type="number" value={form.coef_b} onChange={(e) => set("coef_b", parseFloat(e.target.value) || 0)} step={0.001} min={0} /></Field>
            <Field label="Coef C"><TInput type="number" value={form.coef_c} onChange={(e) => set("coef_c", parseFloat(e.target.value) || 0)} step={0.001} min={0} /></Field>
          </div>
          {otrasUnidades && (
            <p className={coefDesviado ? "text-xs text-warning" : "text-xs text-text2"}>
              Suma de Coef A del consorcio con esta unidad: {sumaTotal.toFixed(2)}%
              {coefDesviado ? " — debería sumar 100%, revisá los coeficientes." : " ✓"}
            </p>
          )}
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className="text-text2">Cancelar</Button>
          <Button onClick={handleSave} disabled={saving || !form.unidad.trim()} className="bg-accent text-white">
            {saving ? "Guardando..." : initial ? "Guardar cambios" : "Crear unidad"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

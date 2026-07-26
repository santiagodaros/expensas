import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Consorcio, ConsorcioCreate } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Field, TInput } from "@/components/ui/form-field";

const EMPTY_C: ConsorcioCreate = { nombre: "", cuit: "", direccion: "", unidades: 0, reserva_pct: 5, dia_vto: 10, interes_mora_pct: 0 };

export function ConsorcioDialog({ initial, onClose, onSaved }: { initial?: Consorcio; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<ConsorcioCreate>(
    initial
      ? { nombre: initial.nombre, cuit: initial.cuit ?? "", direccion: initial.direccion ?? "", unidades: initial.unidades, reserva_pct: initial.reserva_pct, dia_vto: initial.dia_vto, interes_mora_pct: initial.interes_mora_pct }
      : { ...EMPTY_C }
  );
  const [saving, setSaving] = useState(false);
  const set = (k: keyof ConsorcioCreate, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.nombre.trim()) return;
    setSaving(true);
    try {
      initial ? await api.put(`/api/consorcios/${initial.id}`, form) : await api.post("/api/consorcios", form);
      onSaved(); onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error desconocido");
    } finally { setSaving(false); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="bg-surface border-border text-text">
        <DialogHeader><DialogTitle className="text-text">{initial ? "Editar Consorcio" : "Nuevo Consorcio"}</DialogTitle></DialogHeader>
        <div className="flex flex-col gap-3">
          <Field label="Nombre *"><TInput value={form.nombre} onChange={(e) => set("nombre", e.target.value)} placeholder="Consorcio Av. Santa Fe 1234" /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="CUIT"><TInput value={form.cuit ?? ""} onChange={(e) => set("cuit", e.target.value)} placeholder="20-12345678-9" /></Field>
            <Field label="Dia de vencimiento"><TInput type="number" value={form.dia_vto} onChange={(e) => set("dia_vto", parseInt(e.target.value) || 10)} min={1} max={31} /></Field>
          </div>
          <Field label="Direccion"><TInput value={form.direccion ?? ""} onChange={(e) => set("direccion", e.target.value)} placeholder="Av. Santa Fe 1234, CABA" /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Cant. unidades"><TInput type="number" value={form.unidades} onChange={(e) => set("unidades", parseInt(e.target.value) || 0)} min={0} /></Field>
            <Field label="Reserva (%)"><TInput type="number" value={form.reserva_pct} onChange={(e) => set("reserva_pct", parseFloat(e.target.value) || 0)} min={0} max={100} step={0.5} /></Field>
          </div>
          <Field label="Interés por mora mensual (%) — 0 desactiva">
            <TInput type="number" value={form.interes_mora_pct} onChange={(e) => set("interes_mora_pct", parseFloat(e.target.value) || 0)} min={0} max={100} step={0.5} />
          </Field>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className="text-text2">Cancelar</Button>
          <Button onClick={handleSave} disabled={saving || !form.nombre.trim()} className="bg-accent text-white">
            {saving ? "Guardando..." : initial ? "Guardar cambios" : "Crear consorcio"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

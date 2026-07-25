import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useGet } from "@/hooks/useApi";
import { Sueldo, SueldoCreate } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectingState } from "@/components/ui/connecting-state";
import { Field, TInput } from "@/components/ui/form-field";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Wallet, Plus, Pencil, Trash2, X, Users, History } from "lucide-react";
import { useApp } from "@/contexts/AppContext";
import { cn, fmtCurrency } from "@/lib/utils";
import { validate } from "@/lib/validate";

const CONCEPTOS = ["Encargado", "Encargado suplente", "Ayudante", "Administrativo", "Mantenimiento", "Otro"];

const EMPTY_FORM: SueldoCreate = {
  empleado: "",
  concepto: "Encargado",
  sueldo_bruto: 0,
  cargas_suterh: 0,
  cargas_fateryh: 0,
  otras_cargas: 0,
};

function HistorialDialog({ consorcioId, empleado, onClose }: { consorcioId: number; empleado: string; onClose: () => void }) {
  const { data: historial, loading } = useGet<Sueldo[]>(
    "/api/sueldos/historial",
    { consorcio: consorcioId, empleado }
  );
  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="bg-surface border-border text-text">
        <DialogHeader><DialogTitle className="text-text">Historial — {empleado}</DialogTitle></DialogHeader>
        <div className="flex flex-col gap-1 max-h-80 overflow-y-auto">
          {loading && <Skeleton className="h-8 rounded-lg bg-surface2" />}
          {!loading && (historial ?? []).length === 0 && (
            <p className="text-xs text-text2 py-4 text-center">Sin recibos anteriores</p>
          )}
          {!loading && (historial ?? []).map((h) => (
            <div key={h.id} className="grid grid-cols-3 px-3 py-2 rounded-lg text-xs bg-surface2 text-text">
              <span className="font-medium">{h.periodo}</span>
              <span className="text-text2">{h.concepto}</span>
              <span className="text-right font-semibold text-accent">{fmtCurrency(h.total_gasto)}</span>
            </div>
          ))}
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className="text-text2">Cerrar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

const totalGasto = (f: SueldoCreate) =>
  f.sueldo_bruto + f.cargas_suterh + f.cargas_fateryh + f.otras_cargas;

export function SueldosPage() {
  const { consorcioId, periodo } = useApp();

  const { data: sueldos, loading, connecting, refetch } = useGet<Sueldo[]>(
    "/api/sueldos",
    consorcioId && periodo ? { consorcio: consorcioId, periodo } : null
  );

  const [form, setForm] = useState<SueldoCreate>({ ...EMPTY_FORM });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Sueldo | null>(null);
  const [historialEmpleado, setHistorialEmpleado] = useState<string | null>(null);

  const resetForm = () => {
    setForm({ ...EMPTY_FORM });
    setEditingId(null);
  };

  const handleSave = async () => {
    if (!validate(
      [!!form.empleado.trim(), "El nombre del empleado es obligatorio"],
      [totalGasto(form) > 0, "El total del gasto debe ser mayor a cero"],
    )) return;
    setSaving(true);
    try {
      if (editingId !== null) {
        await api.put(`/api/sueldos/${editingId}`, form);
        toast.success("Sueldo actualizado");
      } else {
        await api.post("/api/sueldos", form, {
          params: { consorcio_id: consorcioId, periodo },
        });
        toast.success(`Sueldo cargado: ${form.empleado}`);
      }
      resetForm();
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (s: Sueldo) => {
    setEditingId(s.id);
    setForm({
      empleado: s.empleado,
      concepto: s.concepto,
      sueldo_bruto: s.sueldo_bruto,
      cargas_suterh: s.cargas_suterh,
      cargas_fateryh: s.cargas_fateryh,
      otras_cargas: s.otras_cargas,
    });
  };

  const handleDelete = async (s: Sueldo) => {
    setDeleting(s.id);
    try {
      await api.delete(`/api/sueldos/${s.id}`);
      toast.success(`Sueldo eliminado: ${s.empleado}`);
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al eliminar");
    } finally {
      setDeleting(null);
      setConfirmDelete(null);
    }
  };

  const numInput = (label: string, key: keyof SueldoCreate, placeholder = "0") => (
    <Field label={label}>
      <TInput
        type="number"
        value={(form[key] as number) || ""}
        onChange={(e) => setForm((f) => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))}
        placeholder={placeholder}
      />
    </Field>
  );

  const totalMes = (sueldos ?? []).reduce((s, r) => s + r.total_gasto, 0);

  if (connecting) return <ConnectingState />;

  return (
    <div className="grid grid-cols-2 gap-5 h-full overflow-hidden">
      {/* ── Columna izquierda: formulario ── */}
      <div className="flex flex-col gap-4 overflow-y-auto">
        <div className="rounded-xl border p-5 shadow-card bg-surface border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Wallet size={16} className="text-accent" />
              <h2 className="text-sm font-semibold text-text">
                {editingId !== null ? "Editar Recibo" : "Nuevo Recibo de Sueldo"}
              </h2>
            </div>
            {editingId !== null && (
              <button onClick={resetForm} className="text-xs flex items-center gap-1 hover:opacity-70 text-text2">
                <X size={12} />Cancelar
              </button>
            )}
          </div>

          <div className="flex flex-col gap-3">
            <Field label="Empleado *">
              <TInput
                value={form.empleado}
                onChange={(e) => setForm((f) => ({ ...f, empleado: e.target.value }))}
                placeholder="Nombre y apellido"
              />
            </Field>

            <Field label="Categoria / Concepto">
              <Select
                items={CONCEPTOS.map((c) => ({ value: c, label: c }))}
                value={CONCEPTOS.slice(0, -1).includes(form.concepto) ? form.concepto : "Otro"}
                onValueChange={(v) => setForm((f) => ({ ...f, concepto: v === "Otro" ? "" : (v ?? "") }))}
              >
                <SelectTrigger className="bg-surface2 border-border text-text w-full"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-surface2 border-border">
                  {CONCEPTOS.map((c) => (<SelectItem key={c} value={c} className="text-text">{c}</SelectItem>))}
                </SelectContent>
              </Select>
              {!CONCEPTOS.slice(0, -1).includes(form.concepto) && (
                <TInput
                  value={form.concepto}
                  onChange={(e) => setForm((f) => ({ ...f, concepto: e.target.value }))}
                  placeholder="Especificar concepto"
                  className="mt-1.5"
                />
              )}
            </Field>

            <div className="rounded-lg p-3 flex flex-col gap-2 bg-surface2 border border-border">
              <p className="text-xs font-medium text-text2">Desglose del recibo</p>
              {numInput("Sueldo bruto / Haber total", "sueldo_bruto")}
              <div className="grid grid-cols-2 gap-2">
                {numInput("Cargas SUTERH", "cargas_suterh")}
                {numInput("Cargas FATERYH", "cargas_fateryh")}
              </div>
              {numInput("Otras cargas patronales", "otras_cargas")}
            </div>

            {/* Total calculado */}
            <div className="flex items-center justify-between px-4 py-3 rounded-lg bg-accent/[0.08] border border-accent/20">
              <span className="text-xs font-medium text-text2">Total gasto consorcio</span>
              <span className="text-base font-bold text-accent">{fmtCurrency(totalGasto(form))}</span>
            </div>

            <p className="text-xs text-text2">
              Se registrara automaticamente como Gasto Ordinario Cat. A en el libro del mes.
            </p>
          </div>

          <Button
            onClick={handleSave}
            disabled={saving || !form.empleado.trim() || totalGasto(form) <= 0}
            className="w-full mt-4 gap-2 bg-accent text-white"
          >
            {editingId !== null ? <Pencil size={14} /> : <Plus size={14} />}
            {saving ? "Guardando..." : editingId !== null ? "Actualizar Recibo" : "Registrar Sueldo"}
          </Button>
        </div>
      </div>

      {/* ── Columna derecha: lista ── */}
      <div className="flex flex-col rounded-xl border shadow-card overflow-hidden bg-surface border-border">
        <div className="px-4 py-3 border-b flex items-center justify-between bg-surface2 border-border">
          <div className="flex items-center gap-2">
            <Users size={14} className="text-accent" />
            <span className="text-sm font-medium text-text">Sueldos — {periodo}</span>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-accent/15 text-accent">
            {(sueldos ?? []).length} recibos
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
          {loading && [0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-16 rounded-lg bg-surface2" />
          ))}
          {!loading && (sueldos ?? []).length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 gap-2 py-12">
              <Users size={32} className="text-border" />
              <p className="text-xs text-text2">Sin recibos cargados este mes</p>
            </div>
          )}
          {(sueldos ?? []).map((s) => (
            <div
              key={s.id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg",
                editingId === s.id ? "bg-accent/[0.08] outline outline-1 outline-accent/30" : "bg-surface2"
              )}
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 bg-accent/15">
                <Wallet size={15} className="text-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold truncate text-text">{s.empleado}</p>
                <p className="text-xs truncate text-text2">{s.concepto}</p>
                <div className="flex gap-3 mt-1">
                  <span className="text-xs text-text2">
                    Bruto: <span className="text-text">{fmtCurrency(s.sueldo_bruto)}</span>
                  </span>
                  {(s.cargas_suterh + s.cargas_fateryh + s.otras_cargas) > 0 && (
                    <span className="text-xs text-text2">
                      Cargas: <span className="text-text">
                        {fmtCurrency(s.cargas_suterh + s.cargas_fateryh + s.otras_cargas)}
                      </span>
                    </span>
                  )}
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <span className="text-sm font-bold text-accent">{fmtCurrency(s.total_gasto)}</span>
                <div className="flex gap-1">
                  <button
                    onClick={() => setHistorialEmpleado(s.empleado)}
                    className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity text-text2 bg-white/5"
                    title="Ver historial"
                  >
                    <History size={12} />
                  </button>
                  <button
                    onClick={() => handleEdit(s)}
                    className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity text-accent bg-accent/10"
                    title="Editar"
                  >
                    <Pencil size={12} />
                  </button>
                  <button
                    onClick={() => setConfirmDelete(s)}
                    disabled={deleting === s.id}
                    className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40 text-danger bg-danger/10"
                    title="Eliminar"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {(sueldos ?? []).length > 0 && (
          <div className="px-4 py-3 border-t flex items-center justify-between border-border bg-surface2">
            <span className="text-sm font-semibold text-text">Total sueldos del mes</span>
            <span className="text-lg font-bold text-accent">{fmtCurrency(totalMes)}</span>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmDelete !== null}
        title="Eliminar recibo de sueldo"
        description={confirmDelete ? `Se eliminará el recibo de "${confirmDelete.empleado}". Esta acción no se puede deshacer.` : undefined}
        loading={deleting !== null}
        onConfirm={() => confirmDelete && handleDelete(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
      {historialEmpleado && consorcioId && (
        <HistorialDialog consorcioId={consorcioId} empleado={historialEmpleado} onClose={() => setHistorialEmpleado(null)} />
      )}
    </div>
  );
}

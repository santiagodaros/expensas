import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useGet } from "@/hooks/useApi";
import { Sueldo, SueldoCreate } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Wallet, Plus, Pencil, Trash2, X, Users } from "lucide-react";
import { useApp } from "@/contexts/AppContext";

const fmt = (n: number) =>
  new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(n);

const EMPTY_FORM: SueldoCreate = {
  empleado: "",
  concepto: "Encargado",
  sueldo_bruto: 0,
  cargas_suterh: 0,
  cargas_fateryh: 0,
  otras_cargas: 0,
};

const totalGasto = (f: SueldoCreate) =>
  f.sueldo_bruto + f.cargas_suterh + f.cargas_fateryh + f.otras_cargas;

export function SueldosPage() {
  const { consorcioId, periodo } = useApp();

  const { data: sueldos, loading, refetch } = useGet<Sueldo[]>(
    "/api/sueldos",
    consorcioId && periodo ? { consorcio: consorcioId, periodo } : null
  );

  const [form, setForm] = useState<SueldoCreate>({ ...EMPTY_FORM });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);

  const resetForm = () => {
    setForm({ ...EMPTY_FORM });
    setEditingId(null);
  };

  const handleSave = async () => {
    if (!form.empleado.trim()) {
      toast.error("El nombre del empleado es obligatorio");
      return;
    }
    if (totalGasto(form) <= 0) {
      toast.error("El total del gasto debe ser mayor a cero");
      return;
    }
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
    }
  };

  const numInput = (
    label: string,
    key: keyof SueldoCreate,
    placeholder = "0"
  ) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs" style={{ color: "var(--color-text2)" }}>{label}</label>
      <Input
        type="number"
        value={(form[key] as number) || ""}
        onChange={(e) =>
          setForm((f) => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))
        }
        placeholder={placeholder}
        style={{
          backgroundColor: "var(--color-surface2)",
          borderColor: "var(--color-border)",
          color: "var(--color-text)",
        }}
      />
    </div>
  );

  const totalMes = (sueldos ?? []).reduce((s, r) => s + r.total_gasto, 0);

  return (
    <div className="grid grid-cols-2 gap-5 h-full overflow-hidden">
      {/* ── Columna izquierda: formulario ── */}
      <div className="flex flex-col gap-4 overflow-y-auto">
        <div
          className="rounded-xl border p-5 shadow-card"
          style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Wallet size={16} style={{ color: "var(--color-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>
                {editingId !== null ? "Editar Recibo" : "Nuevo Recibo de Sueldo"}
              </h2>
            </div>
            {editingId !== null && (
              <button
                onClick={resetForm}
                className="text-xs flex items-center gap-1 hover:opacity-70"
                style={{ color: "var(--color-text2)" }}
              >
                <X size={12} />Cancelar
              </button>
            )}
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs" style={{ color: "var(--color-text2)" }}>
                Empleado <span style={{ color: "var(--color-danger)" }}>*</span>
              </label>
              <Input
                value={form.empleado}
                onChange={(e) => setForm((f) => ({ ...f, empleado: e.target.value }))}
                placeholder="Nombre y apellido"
                style={{
                  backgroundColor: "var(--color-surface2)",
                  borderColor: "var(--color-border)",
                  color: "var(--color-text)",
                }}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs" style={{ color: "var(--color-text2)" }}>Categoria / Concepto</label>
              <Input
                value={form.concepto}
                onChange={(e) => setForm((f) => ({ ...f, concepto: e.target.value }))}
                placeholder="Encargado, Auxiliar, etc."
                style={{
                  backgroundColor: "var(--color-surface2)",
                  borderColor: "var(--color-border)",
                  color: "var(--color-text)",
                }}
              />
            </div>

            <div
              className="rounded-lg p-3 flex flex-col gap-2"
              style={{ backgroundColor: "var(--color-surface2)", border: "1px solid var(--color-border)" }}
            >
              <p className="text-xs font-medium" style={{ color: "var(--color-text2)" }}>Desglose del recibo</p>
              {numInput("Sueldo bruto / Haber total", "sueldo_bruto")}
              <div className="grid grid-cols-2 gap-2">
                {numInput("Cargas SUTERH", "cargas_suterh")}
                {numInput("Cargas FATERYH", "cargas_fateryh")}
              </div>
              {numInput("Otras cargas patronales", "otras_cargas")}
            </div>

            {/* Total calculado */}
            <div
              className="flex items-center justify-between px-4 py-3 rounded-lg"
              style={{ backgroundColor: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)" }}
            >
              <span className="text-xs font-medium" style={{ color: "var(--color-text2)" }}>
                Total gasto consorcio
              </span>
              <span className="text-base font-bold" style={{ color: "var(--color-accent)" }}>
                {fmt(totalGasto(form))}
              </span>
            </div>

            <p className="text-xs" style={{ color: "var(--color-text2)" }}>
              Se registrara automaticamente como Gasto Ordinario Cat. A en el libro del mes.
            </p>
          </div>

          <Button
            onClick={handleSave}
            disabled={saving || !form.empleado.trim() || totalGasto(form) <= 0}
            className="w-full mt-4 gap-2"
            style={{ backgroundColor: "var(--color-accent)", color: "white" }}
          >
            {editingId !== null ? <Pencil size={14} /> : <Plus size={14} />}
            {saving ? "Guardando..." : editingId !== null ? "Actualizar Recibo" : "Registrar Sueldo"}
          </Button>
        </div>
      </div>

      {/* ── Columna derecha: lista ── */}
      <div
        className="flex flex-col rounded-xl border shadow-card overflow-hidden"
        style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
      >
        <div
          className="px-4 py-3 border-b flex items-center justify-between"
          style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)" }}
        >
          <div className="flex items-center gap-2">
            <Users size={14} style={{ color: "var(--color-accent)" }} />
            <span className="text-sm font-medium" style={{ color: "var(--color-text)" }}>
              Sueldos — {periodo}
            </span>
          </div>
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ backgroundColor: "rgba(59,130,246,0.15)", color: "var(--color-accent)" }}
          >
            {(sueldos ?? []).length} recibos
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
          {loading && [0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-16 rounded-lg" style={{ backgroundColor: "var(--color-surface2)" }} />
          ))}
          {!loading && (sueldos ?? []).length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 gap-2 py-12">
              <Users size={32} style={{ color: "var(--color-border)" }} />
              <p className="text-xs" style={{ color: "var(--color-text2)" }}>Sin recibos cargados este mes</p>
            </div>
          )}
          {(sueldos ?? []).map((s) => (
            <div
              key={s.id}
              className="flex items-start gap-3 p-3 rounded-lg"
              style={{
                backgroundColor: editingId === s.id ? "rgba(59,130,246,0.08)" : "var(--color-surface2)",
                outline: editingId === s.id ? "1px solid rgba(59,130,246,0.3)" : "none",
              }}
            >
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                style={{ backgroundColor: "rgba(59,130,246,0.15)" }}
              >
                <Wallet size={15} style={{ color: "var(--color-accent)" }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold truncate" style={{ color: "var(--color-text)" }}>
                  {s.empleado}
                </p>
                <p className="text-xs truncate" style={{ color: "var(--color-text2)" }}>{s.concepto}</p>
                <div className="flex gap-3 mt-1">
                  <span className="text-xs" style={{ color: "var(--color-text2)" }}>
                    Bruto: <span style={{ color: "var(--color-text)" }}>{fmt(s.sueldo_bruto)}</span>
                  </span>
                  {(s.cargas_suterh + s.cargas_fateryh + s.otras_cargas) > 0 && (
                    <span className="text-xs" style={{ color: "var(--color-text2)" }}>
                      Cargas: <span style={{ color: "var(--color-text)" }}>
                        {fmt(s.cargas_suterh + s.cargas_fateryh + s.otras_cargas)}
                      </span>
                    </span>
                  )}
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <span className="text-sm font-bold" style={{ color: "var(--color-accent)" }}>
                  {fmt(s.total_gasto)}
                </span>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(s)}
                    className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity"
                    style={{ color: "var(--color-accent)", backgroundColor: "rgba(59,130,246,0.1)" }}
                    title="Editar"
                  >
                    <Pencil size={12} />
                  </button>
                  <button
                    onClick={() => handleDelete(s)}
                    disabled={deleting === s.id}
                    className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40"
                    style={{ color: "var(--color-danger)", backgroundColor: "rgba(239,68,68,0.1)" }}
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
          <div
            className="px-4 py-3 border-t flex items-center justify-between"
            style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-surface2)" }}
          >
            <span className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>
              Total sueldos del mes
            </span>
            <span className="text-lg font-bold" style={{ color: "var(--color-accent)" }}>
              {fmt(totalMes)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

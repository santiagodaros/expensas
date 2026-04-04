import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useGet } from "@/hooks/useApi";
import { Proveedor, ProveedorCreate } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Truck, Plus, Pencil, Trash2, X, BarChart2 } from "lucide-react";
import { useApp } from "@/contexts/AppContext";

const fmt = (n: number) =>
  new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(n);

const EMPTY_FORM: ProveedorCreate = {
  razon_social: "",
  cuit: "",
  domicilio: "",
  cat_afip: "",
  cbu: "",
};

export function ProveedoresPage() {
  const { consorcioId } = useApp();

  const { data: proveedores, loading, refetch } = useGet<Proveedor[]>(
    "/api/proveedores",
    consorcioId ? { consorcio: consorcioId } : null
  );

  const [form, setForm] = useState<ProveedorCreate>({ ...EMPTY_FORM });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: cuentaCorriente, loading: loadingCC, refetch: refetchCC } = useGet<
    { periodo: string; total: number; qty: number }[]
  >(
    selectedId ? `/api/proveedores/${selectedId}/cuenta_corriente` : null,
    selectedId ? {} : null
  );

  const resetForm = () => {
    setForm({ ...EMPTY_FORM });
    setEditingId(null);
  };

  const handleSave = async () => {
    if (!form.razon_social.trim()) {
      toast.error("La razon social es obligatoria");
      return;
    }
    setSaving(true);
    try {
      if (editingId !== null) {
        await api.put(`/api/proveedores/${editingId}`, form);
        toast.success("Proveedor actualizado");
      } else {
        await api.post("/api/proveedores", form, { params: { consorcio_id: consorcioId } });
        toast.success(`Proveedor creado: ${form.razon_social}`);
      }
      resetForm();
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (p: Proveedor) => {
    setEditingId(p.id);
    setForm({
      razon_social: p.razon_social,
      cuit: p.cuit ?? "",
      domicilio: p.domicilio ?? "",
      cat_afip: p.cat_afip ?? "",
      cbu: p.cbu ?? "",
    });
  };

  const handleDelete = async (p: Proveedor) => {
    setDeleting(p.id);
    try {
      await api.delete(`/api/proveedores/${p.id}`);
      toast.success(`Proveedor eliminado: ${p.razon_social}`);
      if (selectedId === p.id) setSelectedId(null);
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al eliminar");
    } finally {
      setDeleting(null);
    }
  };

  const handleSelect = (p: Proveedor) => {
    if (selectedId === p.id) {
      setSelectedId(null);
    } else {
      setSelectedId(p.id);
      setTimeout(() => refetchCC(), 0);
    }
  };

  const selectedProveedor = (proveedores ?? []).find((p) => p.id === selectedId);

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
              <Truck size={16} style={{ color: "var(--color-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>
                {editingId !== null ? "Editar Proveedor" : "Nuevo Proveedor"}
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
                Razon Social <span style={{ color: "var(--color-danger)" }}>*</span>
              </label>
              <Input
                value={form.razon_social}
                onChange={(e) => setForm((f) => ({ ...f, razon_social: e.target.value }))}
                placeholder="Nombre o razon social"
                style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs" style={{ color: "var(--color-text2)" }}>CUIT</label>
                <Input
                  value={form.cuit ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, cuit: e.target.value }))}
                  placeholder="30-12345678-9"
                  style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs" style={{ color: "var(--color-text2)" }}>Cat. AFIP</label>
                <Input
                  value={form.cat_afip ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, cat_afip: e.target.value }))}
                  placeholder="Responsable Inscripto"
                  style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
                />
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs" style={{ color: "var(--color-text2)" }}>Domicilio</label>
              <Input
                value={form.domicilio ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, domicilio: e.target.value }))}
                placeholder="Direccion del proveedor"
                style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs" style={{ color: "var(--color-text2)" }}>CBU</label>
              <Input
                value={form.cbu ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, cbu: e.target.value }))}
                placeholder="CBU para transferencias"
                style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
              />
            </div>
          </div>

          <Button
            onClick={handleSave}
            disabled={saving || !form.razon_social.trim()}
            className="w-full mt-4 gap-2"
            style={{ backgroundColor: "var(--color-accent)", color: "white" }}
          >
            {editingId !== null ? <Pencil size={14} /> : <Plus size={14} />}
            {saving ? "Guardando..." : editingId !== null ? "Actualizar Proveedor" : "Agregar Proveedor"}
          </Button>
        </div>

        {/* Panel cuenta corriente */}
        {selectedProveedor && (
          <div
            className="rounded-xl border p-4 shadow-card"
            style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
          >
            <div className="flex items-center gap-2 mb-3">
              <BarChart2 size={15} style={{ color: "var(--color-accent)" }} />
              <h3 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>
                Cuenta Corriente — {selectedProveedor.razon_social}
              </h3>
            </div>
            {loadingCC && (
              <div className="flex flex-col gap-2">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-8 rounded-lg" style={{ backgroundColor: "var(--color-surface2)" }} />
                ))}
              </div>
            )}
            {!loadingCC && (cuentaCorriente ?? []).length === 0 && (
              <p className="text-xs py-4 text-center" style={{ color: "var(--color-text2)" }}>
                Sin gastos registrados para este proveedor
              </p>
            )}
            {!loadingCC && (cuentaCorriente ?? []).length > 0 && (
              <div className="flex flex-col gap-1">
                <div
                  className="grid grid-cols-3 px-3 py-1 rounded-lg text-xs font-medium"
                  style={{ backgroundColor: "var(--color-surface2)", color: "var(--color-text2)" }}
                >
                  <span>Periodo</span>
                  <span className="text-right">Comprobantes</span>
                  <span className="text-right">Total</span>
                </div>
                {(cuentaCorriente ?? []).map((row) => (
                  <div
                    key={row.periodo}
                    className="grid grid-cols-3 px-3 py-2 rounded-lg text-xs"
                    style={{ backgroundColor: "var(--color-surface2)", color: "var(--color-text)" }}
                  >
                    <span className="font-medium">{row.periodo}</span>
                    <span className="text-right" style={{ color: "var(--color-text2)" }}>{row.qty}</span>
                    <span className="text-right font-semibold" style={{ color: "var(--color-accent)" }}>{fmt(row.total)}</span>
                  </div>
                ))}
                <div
                  className="grid grid-cols-3 px-3 py-2 rounded-lg text-xs font-bold mt-1"
                  style={{ backgroundColor: "var(--color-surface2)", borderTop: `1px solid var(--color-border)`, color: "var(--color-text)" }}
                >
                  <span>Total</span>
                  <span className="text-right" style={{ color: "var(--color-text2)" }}>
                    {(cuentaCorriente ?? []).reduce((s, r) => s + r.qty, 0)}
                  </span>
                  <span className="text-right" style={{ color: "var(--color-accent)" }}>
                    {fmt((cuentaCorriente ?? []).reduce((s, r) => s + r.total, 0))}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
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
          <span className="text-sm font-medium" style={{ color: "var(--color-text)" }}>Proveedores</span>
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ backgroundColor: "rgba(59,130,246,0.15)", color: "var(--color-accent)" }}
          >
            {(proveedores ?? []).length} registros
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
          {loading && [0, 1, 2, 4].map((i) => (
            <Skeleton key={i} className="h-14 rounded-lg" style={{ backgroundColor: "var(--color-surface2)" }} />
          ))}
          {!loading && (proveedores ?? []).length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 gap-2 py-12">
              <Truck size={32} style={{ color: "var(--color-border)" }} />
              <p className="text-xs" style={{ color: "var(--color-text2)" }}>Sin proveedores cargados</p>
            </div>
          )}
          {(proveedores ?? []).map((p) => (
            <div
              key={p.id}
              onClick={() => handleSelect(p)}
              className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all"
              style={{
                backgroundColor: selectedId === p.id ? "rgba(59,130,246,0.08)" : "var(--color-surface2)",
                outline: selectedId === p.id ? "1px solid rgba(59,130,246,0.3)" : "none",
              }}
            >
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                style={{ backgroundColor: "rgba(59,130,246,0.15)" }}
              >
                <Truck size={15} style={{ color: "var(--color-accent)" }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold truncate" style={{ color: "var(--color-text)" }}>
                  {p.razon_social}
                </p>
                <p className="text-xs truncate" style={{ color: "var(--color-text2)" }}>
                  {[p.cuit, p.cat_afip].filter(Boolean).join(" · ") || "Sin datos"}
                </p>
              </div>
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={(e) => { e.stopPropagation(); handleEdit(p); }}
                  className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity"
                  style={{ color: "var(--color-accent)", backgroundColor: "rgba(59,130,246,0.1)" }}
                  title="Editar"
                >
                  <Pencil size={12} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(p); }}
                  disabled={deleting === p.id}
                  className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40"
                  style={{ color: "var(--color-danger)", backgroundColor: "rgba(239,68,68,0.1)" }}
                  title="Eliminar"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {selectedProveedor && (
          <div
            className="px-4 py-2 border-t text-xs"
            style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-surface2)", color: "var(--color-text2)" }}
          >
            Seleccionado: <span style={{ color: "var(--color-accent)" }}>{selectedProveedor.razon_social}</span>
            {selectedProveedor.cbu && <> · CBU: <span style={{ color: "var(--color-text)" }}>{selectedProveedor.cbu}</span></>}
          </div>
        )}
      </div>
    </div>
  );
}

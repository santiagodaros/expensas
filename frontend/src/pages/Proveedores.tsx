import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useGet } from "@/hooks/useApi";
import { Proveedor, ProveedorCreate, Gasto } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectingState } from "@/components/ui/connecting-state";
import { Field, TInput } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Truck, Plus, Pencil, Trash2, X, BarChart2, Search, ChevronDown, ChevronRight } from "lucide-react";
import { useApp } from "@/contexts/AppContext";
import { cn, fmtCurrency } from "@/lib/utils";
import { validate } from "@/lib/validate";

const EMPTY_FORM: ProveedorCreate = {
  razon_social: "",
  cuit: "",
  domicilio: "",
  cat_afip: "",
  cbu: "",
};

export function ProveedoresPage() {
  const { consorcioId } = useApp();

  const { data: proveedores, loading, connecting, refetch } = useGet<Proveedor[]>(
    "/api/proveedores",
    consorcioId ? { consorcio: consorcioId } : null
  );

  const [form, setForm] = useState<ProveedorCreate>({ ...EMPTY_FORM });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Proveedor | null>(null);
  const [search, setSearch] = useState("");
  const [expandedPeriodo, setExpandedPeriodo] = useState<string | null>(null);

  const { data: cuentaCorriente, loading: loadingCC, refetch: refetchCC } = useGet<
    { periodo: string; total: number; qty: number }[]
  >(
    selectedId ? `/api/proveedores/${selectedId}/cuenta_corriente` : null,
    selectedId ? {} : null
  );

  const { data: gastosDelPeriodo, loading: loadingGastosPeriodo } = useGet<Gasto[]>(
    selectedId && expandedPeriodo ? `/api/proveedores/${selectedId}/gastos` : null,
    selectedId && expandedPeriodo ? { periodo: expandedPeriodo } : null
  );

  const resetForm = () => {
    setForm({ ...EMPTY_FORM });
    setEditingId(null);
  };

  const handleSave = async () => {
    if (!validate([!!form.razon_social.trim(), "La razon social es obligatoria"])) return;
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
      setConfirmDelete(null);
    }
  };

  const handleSelect = (p: Proveedor) => {
    setExpandedPeriodo(null);
    if (selectedId === p.id) {
      setSelectedId(null);
    } else {
      setSelectedId(p.id);
      setTimeout(() => refetchCC(), 0);
    }
  };

  const selectedProveedor = (proveedores ?? []).find((p) => p.id === selectedId);

  const proveedoresFiltrados = (proveedores ?? []).filter((p) => {
    if (!search.trim()) return true;
    const q = search.trim().toLowerCase();
    return [p.razon_social, p.cuit, p.cat_afip].some((v) => (v ?? "").toLowerCase().includes(q));
  });

  if (connecting) return <ConnectingState />;

  return (
    <div className="grid grid-cols-2 gap-5 h-full overflow-hidden">
      {/* ── Columna izquierda: formulario ── */}
      <div className="flex flex-col gap-4 overflow-y-auto">
        <div className="rounded-xl border p-5 shadow-card bg-surface border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Truck size={16} className="text-accent" />
              <h2 className="text-sm font-semibold text-text">
                {editingId !== null ? "Editar Proveedor" : "Nuevo Proveedor"}
              </h2>
            </div>
            {editingId !== null && (
              <button onClick={resetForm} className="text-xs flex items-center gap-1 hover:opacity-70 text-text2">
                <X size={12} />Cancelar
              </button>
            )}
          </div>

          <div className="flex flex-col gap-3">
            <Field label="Razon Social *">
              <TInput
                value={form.razon_social}
                onChange={(e) => setForm((f) => ({ ...f, razon_social: e.target.value }))}
                placeholder="Nombre o razon social"
              />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="CUIT">
                <TInput
                  value={form.cuit ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, cuit: e.target.value }))}
                  placeholder="30-12345678-9"
                />
              </Field>
              <Field label="Cat. AFIP">
                <TInput
                  value={form.cat_afip ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, cat_afip: e.target.value }))}
                  placeholder="Responsable Inscripto"
                />
              </Field>
            </div>

            <Field label="Domicilio">
              <TInput
                value={form.domicilio ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, domicilio: e.target.value }))}
                placeholder="Direccion del proveedor"
              />
            </Field>

            <Field label="CBU">
              <TInput
                value={form.cbu ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, cbu: e.target.value }))}
                placeholder="CBU para transferencias"
              />
            </Field>
          </div>

          <Button
            onClick={handleSave}
            disabled={saving || !form.razon_social.trim()}
            className="w-full mt-4 gap-2 bg-accent text-white"
          >
            {editingId !== null ? <Pencil size={14} /> : <Plus size={14} />}
            {saving ? "Guardando..." : editingId !== null ? "Actualizar Proveedor" : "Agregar Proveedor"}
          </Button>
        </div>

        {/* Panel cuenta corriente */}
        {selectedProveedor && (
          <div className="rounded-xl border p-4 shadow-card bg-surface border-border">
            <div className="flex items-center gap-2 mb-3">
              <BarChart2 size={15} className="text-accent" />
              <h3 className="text-sm font-semibold text-text">
                Cuenta Corriente — {selectedProveedor.razon_social}
              </h3>
            </div>
            {loadingCC && (
              <div className="flex flex-col gap-2">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-8 rounded-lg bg-surface2" />
                ))}
              </div>
            )}
            {!loadingCC && (cuentaCorriente ?? []).length === 0 && (
              <p className="text-xs py-4 text-center text-text2">
                Sin gastos registrados para este proveedor
              </p>
            )}
            {!loadingCC && (cuentaCorriente ?? []).length > 0 && (
              <div className="flex flex-col gap-1">
                <div className="grid grid-cols-3 px-3 py-1 rounded-lg text-xs font-medium bg-surface2 text-text2">
                  <span>Periodo</span>
                  <span className="text-right">Comprobantes</span>
                  <span className="text-right">Total</span>
                </div>
                {(cuentaCorriente ?? []).map((row) => {
                  const expanded = expandedPeriodo === row.periodo;
                  return (
                    <div key={row.periodo} className="rounded-lg bg-surface2 overflow-hidden">
                      <button
                        onClick={() => setExpandedPeriodo(expanded ? null : row.periodo)}
                        className="w-full grid grid-cols-[16px_1fr_1fr_1fr] items-center gap-1 px-3 py-2 text-xs text-text hover:bg-white/5 transition-colors"
                      >
                        {expanded ? <ChevronDown size={12} className="text-text2" /> : <ChevronRight size={12} className="text-text2" />}
                        <span className="font-medium text-left">{row.periodo}</span>
                        <span className="text-right text-text2">{row.qty}</span>
                        <span className="text-right font-semibold text-accent">{fmtCurrency(row.total)}</span>
                      </button>
                      {expanded && (
                        <div className="px-3 pb-2 flex flex-col gap-1 border-t border-border/50 pt-2">
                          {loadingGastosPeriodo && <Skeleton className="h-6 rounded bg-surface" />}
                          {!loadingGastosPeriodo && (gastosDelPeriodo ?? []).map((g) => (
                            <div key={g.id} className="flex items-center justify-between text-xs text-text2">
                              <span className="truncate">{g.descripcion}</span>
                              <span className="shrink-0 ml-2 text-text">{fmtCurrency(g.monto)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
                <div className="grid grid-cols-3 px-3 py-2 rounded-lg text-xs font-bold mt-1 bg-surface2 border-t border-border text-text">
                  <span>Total</span>
                  <span className="text-right text-text2">
                    {(cuentaCorriente ?? []).reduce((s, r) => s + r.qty, 0)}
                  </span>
                  <span className="text-right text-accent">
                    {fmtCurrency((cuentaCorriente ?? []).reduce((s, r) => s + r.total, 0))}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Columna derecha: lista ── */}
      <div className="flex flex-col rounded-xl border shadow-card overflow-hidden bg-surface border-border">
        <div className="px-4 py-3 border-b flex items-center justify-between bg-surface2 border-border">
          <span className="text-sm font-medium text-text">Proveedores</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-accent/15 text-accent">
            {(proveedores ?? []).length} registros
          </span>
        </div>
        {(proveedores ?? []).length > 0 && (
          <div className="relative px-3 pt-3 shrink-0">
            <Search size={13} className="absolute left-6 top-1/2 -translate-y-1/2 text-text2" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por razón social o CUIT..."
              className="pl-8 h-8 text-sm bg-surface2 border-border text-text"
            />
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
          {loading && [0, 1, 2, 4].map((i) => (
            <Skeleton key={i} className="h-14 rounded-lg bg-surface2" />
          ))}
          {!loading && (proveedores ?? []).length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 gap-2 py-12">
              <Truck size={32} className="text-border" />
              <p className="text-xs text-text2">Sin proveedores cargados</p>
            </div>
          )}
          {!loading && (proveedores ?? []).length > 0 && proveedoresFiltrados.length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 gap-2 py-12">
              <Search size={28} className="text-border" />
              <p className="text-xs text-text2">Ningún proveedor coincide con "{search}"</p>
            </div>
          )}
          {proveedoresFiltrados.map((p) => (
            <div
              key={p.id}
              onClick={() => handleSelect(p)}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all",
                selectedId === p.id ? "bg-accent/[0.08] outline outline-1 outline-accent/30" : "bg-surface2"
              )}
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-accent/15">
                <Truck size={15} className="text-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold truncate text-text">
                  {p.razon_social}
                </p>
                <p className="text-xs truncate text-text2">
                  {[p.cuit, p.cat_afip].filter(Boolean).join(" · ") || "Sin datos"}
                </p>
              </div>
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={(e) => { e.stopPropagation(); handleEdit(p); }}
                  className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity text-accent bg-accent/10"
                  title="Editar"
                >
                  <Pencil size={12} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setConfirmDelete(p); }}
                  disabled={deleting === p.id}
                  className="w-7 h-7 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40 text-danger bg-danger/10"
                  title="Eliminar"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {selectedProveedor && (
          <div className="px-4 py-2 border-t text-xs border-border bg-surface2 text-text2">
            Seleccionado: <span className="text-accent">{selectedProveedor.razon_social}</span>
            {selectedProveedor.cbu && <> · CBU: <span className="text-text">{selectedProveedor.cbu}</span></>}
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmDelete !== null}
        title="Eliminar proveedor"
        description={confirmDelete ? `Se eliminará "${confirmDelete.razon_social}". Esta acción no se puede deshacer.` : undefined}
        loading={deleting !== null}
        onConfirm={() => confirmDelete && handleDelete(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

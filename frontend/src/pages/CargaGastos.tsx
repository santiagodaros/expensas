import { useState, useCallback } from "react";
import { toast } from "sonner";
import { useGet, usePost, usePut, useDelete } from "@/hooks/useApi";
import { Gasto, GastoBatchItem } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useDropzone } from "react-dropzone";
import { UploadCloud, Plus, Receipt, FileText, Pencil, Trash2, X } from "lucide-react";
import { useApp } from "@/contexts/AppContext";

const API_BASE = "http://localhost:8000";
async function openPdf(url: string) {
  try {
    const res = await fetch(API_BASE + url);
    if (!res.ok) throw new Error("Error al generar PDF");
    const blob = await res.blob();
    window.open(URL.createObjectURL(blob), "_blank");
  } catch { /* toast shown by caller */ }
}

const fmt = (n: number) => new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(n);
const CATEGORIAS = [{ value: "A", label: "Cat A - Gastos Comunes" }, { value: "B", label: "Cat B - Fuerza Motriz" }, { value: "C", label: "Cat C - Locales" }];
const EMPTY_FORM: GastoBatchItem = { categoria: "A", descripcion: "", monto: 0 };

export function CargaGastosPage() {
  const { consorcioId: CONSORCIO, periodo: PERIODO } = useApp();
  const [form, setForm] = useState<GastoBatchItem>({ ...EMPTY_FORM });
  const [file, setFile] = useState<File | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { data: gastos, loading, refetch } = useGet<Gasto[]>("/api/finanzas/gastos", CONSORCIO ? { consorcio: CONSORCIO, periodo: PERIODO } : null);
  const { post: postBatch, loading: saving } = usePost<object, object>("/api/finanzas/gastos/batch");
  const { put, loading: updating } = usePut<object, object>("/api/finanzas/gastos");
  const { remove, loading: deleting } = useDelete("/api/finanzas/gastos");
  const onDrop = useCallback((files: File[]) => { if (files[0]) setFile(files[0]); }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { "application/pdf": [], "image/*": [] }, maxFiles: 1 });

  const resetForm = () => { setForm({ ...EMPTY_FORM }); setEditingId(null); setFile(null); };

  const handleSave = async () => {
    if (!form.descripcion.trim()) { toast.error("Ingresa una descripcion"); return; }
    if (!form.monto || form.monto <= 0) { toast.error("El monto debe ser mayor a cero"); return; }
    if (editingId !== null) {
      const res = await put(editingId, { categoria: form.categoria, descripcion: form.descripcion, monto: form.monto });
      if (res !== null) { toast.success("Gasto actualizado"); resetForm(); refetch(); }
      else { toast.error("Error al actualizar el gasto"); }
    } else {
      const res = await postBatch({ consorcio_id: CONSORCIO, periodo: PERIODO, gastos: [form] });
      if (res) { toast.success(`Gasto guardado: ${form.descripcion}`); resetForm(); refetch(); }
      else { toast.error("Error al guardar el gasto"); }
    }
  };

  const handleEdit = (g: Gasto) => {
    setEditingId(g.id);
    setForm({ categoria: g.categoria, descripcion: g.descripcion, monto: g.monto });
  };

  const handleDelete = async (g: Gasto) => {
    const ok = await remove(g.id);
    if (ok) { toast.success(`Gasto eliminado: ${g.descripcion}`); refetch(); }
    else { toast.error("Error al eliminar el gasto"); }
  };

  const totalCat = (cat: string) => (gastos ?? []).filter((g) => g.categoria === cat).reduce((s, g) => s + g.monto, 0);
  const totalGeneral = (gastos ?? []).reduce((s, g) => s + g.monto, 0);
  const isBusy = saving || updating;

  return (
    <div className="grid grid-cols-2 gap-5 h-full">
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border p-5 shadow-card" style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Receipt size={16} style={{ color: "var(--color-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>
                {editingId !== null ? "Editar Comprobante" : "Nuevo Comprobante"}
              </h2>
            </div>
            {editingId !== null && (
              <button onClick={resetForm} className="text-xs flex items-center gap-1 hover:opacity-70" style={{ color: "var(--color-text2)" }}>
                <X size={12} />Cancelar
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1"><label className="text-xs" style={{ color: "var(--color-text2)" }}>Categoria</label>
              <Select value={form.categoria} onValueChange={(v) => setForm((f) => ({ ...f, categoria: v as "A" | "B" | "C" }))}>
                <SelectTrigger style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}><SelectValue /></SelectTrigger>
                <SelectContent style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)" }}>
                  {CATEGORIAS.map((cat) => (<SelectItem key={cat.value} value={cat.value} style={{ color: "var(--color-text)" }}>{cat.label}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1"><label className="text-xs" style={{ color: "var(--color-text2)" }}>Monto</label>
              <Input type="number" value={form.monto || ""} onChange={(e) => setForm((f) => ({ ...f, monto: parseFloat(e.target.value) || 0 }))} placeholder="0.00" style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }} />
            </div>
            <div className="col-span-2 flex flex-col gap-1"><label className="text-xs" style={{ color: "var(--color-text2)" }}>Descripcion</label>
              <Input value={form.descripcion} onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))} placeholder="Descripcion del gasto" style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }} />
            </div>
          </div>
          <Button onClick={handleSave} disabled={isBusy || !form.descripcion} className="w-full mt-4 gap-2" style={{ backgroundColor: "var(--color-accent)", color: "white" }}>
            {editingId !== null ? <Pencil size={14} /> : <Plus size={14} />}
            {isBusy ? "Guardando..." : (editingId !== null ? "Actualizar Comprobante" : "Agregar Comprobante")}
          </Button>
        </div>
        <div {...getRootProps()} className="flex-1 rounded-xl border-2 border-dashed flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors min-h-40"
          style={{ borderColor: isDragActive ? "var(--color-accent)" : "var(--color-border)", backgroundColor: isDragActive ? "rgba(59,130,246,0.05)" : "var(--color-surface)" }}>
          <input {...getInputProps()} />
          <UploadCloud size={32} style={{ color: isDragActive ? "var(--color-accent)" : "var(--color-border)" }} />
          {file ? (<div className="text-center"><p className="text-sm font-medium" style={{ color: "var(--color-text)" }}>{file.name}</p><p className="text-xs mt-1" style={{ color: "var(--color-text2)" }}>{(file.size / 1024).toFixed(1)} KB</p></div>
          ) : (<div className="text-center px-4"><p className="text-sm font-medium" style={{ color: "var(--color-text2)" }}>Arrastra el comprobante aqui</p><p className="text-xs mt-1" style={{ color: "var(--color-border)" }}>PDF o imagen (JPG, PNG)</p></div>)}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-3 gap-3">
          {["A","B","C"].map((cat) => (<div key={cat} className="rounded-xl p-3 border shadow-card text-center" style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}><p className="text-xs mb-1" style={{ color: "var(--color-text2)" }}>Cat {cat}</p><p className="text-sm font-bold" style={{ color: "var(--color-accent)" }}>{fmt(totalCat(cat))}</p></div>))}
        </div>
        <div className="flex-1 rounded-xl border shadow-card overflow-hidden flex flex-col" style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}>
          <div className="px-4 py-3 border-b flex items-center justify-between" style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)" }}>
            <span className="text-sm font-medium" style={{ color: "var(--color-text)" }}>Carga mensual - {PERIODO}</span>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: "rgba(59,130,246,0.15)", color: "var(--color-accent)" }}>{(gastos ?? []).length} items</span>
          </div>
          <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
            {loading && [0,1,2].map((i) => <Skeleton key={i} className="h-12 rounded-lg" style={{ backgroundColor: "var(--color-surface2)" }} />)}
            {!loading && (gastos ?? []).length === 0 && (<div className="flex flex-col items-center justify-center flex-1 gap-2 py-8"><Receipt size={28} style={{ color: "var(--color-border)" }} /><p className="text-xs" style={{ color: "var(--color-text2)" }}>Sin gastos cargados</p></div>)}
            {(gastos ?? []).map((g) => (
              <div key={g.id} className="flex items-center gap-3 p-3 rounded-lg transition-all" style={{ backgroundColor: editingId === g.id ? "rgba(59,130,246,0.08)" : "var(--color-surface2)", outline: editingId === g.id ? "1px solid rgba(59,130,246,0.3)" : "none" }}>
                <span className="w-6 h-6 rounded-md text-xs font-bold flex items-center justify-center text-white shrink-0" style={{ backgroundColor: g.categoria === "A" ? "var(--color-accent)" : g.categoria === "B" ? "var(--color-success)" : "var(--color-warning)" }}>{g.categoria}</span>
                <div className="flex-1 min-w-0"><p className="text-xs font-medium truncate" style={{ color: "var(--color-text)" }}>{g.descripcion}</p></div>
                <span className="text-sm font-semibold shrink-0" style={{ color: "var(--color-text)" }}>{fmt(g.monto)}</span>
                <div className="flex gap-1 shrink-0">
                  <button onClick={() => handleEdit(g)} className="w-6 h-6 rounded flex items-center justify-center hover:opacity-70 transition-opacity" style={{ color: "var(--color-accent)", backgroundColor: "rgba(59,130,246,0.1)" }} title="Editar"><Pencil size={11} /></button>
                  <button onClick={() => handleDelete(g)} disabled={deleting} className="w-6 h-6 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40" style={{ color: "var(--color-danger)", backgroundColor: "rgba(239,68,68,0.1)" }} title="Eliminar"><Trash2 size={11} /></button>
                </div>
              </div>
            ))}
          </div>
          <div className="px-4 py-3 border-t flex items-center justify-between" style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-surface2)" }}>
            <span className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>Total del mes</span>
            <span className="text-lg font-bold" style={{ color: "var(--color-accent)" }}>{fmt(totalGeneral)}</span>
            <Button size="sm" onClick={() => { toast.promise(openPdf(`/api/reportes/general/${CONSORCIO}/${PERIODO}`), { loading: "Generando PDF...", success: "PDF abierto", error: "Error al generar PDF" }); }} className="h-7 px-3 text-xs gap-1" style={{ backgroundColor: "var(--color-accent-subtle)", color: "var(--color-accent)", border: "1px solid rgba(59,130,246,0.3)" }}><FileText size={12} />PDF General</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

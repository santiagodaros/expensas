import { useState, useCallback } from "react";
import { toast } from "sonner";
import api, { openPdf, uploadFile } from "@/lib/api";
import { useGet, usePut, useDelete } from "@/hooks/useApi";
import { Gasto, GastoBatchItem, GastoParticular, GastoParticularCreate, Unidad, Proveedor, Config } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectingState } from "@/components/ui/connecting-state";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useDropzone } from "react-dropzone";
import { UploadCloud, Plus, Receipt, FileText, Pencil, Trash2, X, User, Paperclip } from "lucide-react";
import { useApp } from "@/contexts/AppContext";
import { cn, fmtCurrency } from "@/lib/utils";
import { validate } from "@/lib/validate";

const TIPOS = [{ value: "ordinario", label: "Ordinario" }, { value: "extraordinario", label: "Extraordinario" }];
const EMPTY_FORM: GastoBatchItem = { categoria: "A", descripcion: "", monto: 0, tipo: "ordinario", proveedor_id: undefined };
const EMPTY_PART: GastoParticularCreate = { unidad_id: 0, descripcion: "", monto: 0 };

type Tab = "generales" | "particulares";

export function CargaGastosPage() {
  const { consorcioId: CONSORCIO, periodo: PERIODO } = useApp();
  const [activeTab, setActiveTab] = useState<Tab>("generales");
  const { data: config } = useGet<Config>("/api/config");
  const CATEGORIAS = [
    { value: "A", label: `Cat A - ${config?.nombre_cat_a ?? "Gastos Comunes"}` },
    { value: "B", label: `Cat B - ${config?.nombre_cat_b ?? "Fuerza Motriz"}` },
    { value: "C", label: `Cat C - ${config?.nombre_cat_c ?? "Locales"}` },
  ];

  // ── Tab Generales ──────────────────────────────────────────────────────────
  const [form, setForm] = useState<GastoBatchItem>({ ...EMPTY_FORM });
  const [file, setFile] = useState<File | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { data: gastos, loading, connecting, refetch } = useGet<Gasto[]>("/api/finanzas/gastos", CONSORCIO ? { consorcio: CONSORCIO, periodo: PERIODO } : null);
  const { data: proveedores } = useGet<Proveedor[]>("/api/proveedores", CONSORCIO ? { consorcio: CONSORCIO } : null);
  const [saving, setSaving] = useState(false);
  const { put, loading: updating } = usePut<object, object>("/api/finanzas/gastos");
  const { remove, loading: deleting } = useDelete("/api/finanzas/gastos");
  const onDrop = useCallback((files: File[]) => { if (files[0]) setFile(files[0]); }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { "application/pdf": [], "image/*": [] }, maxFiles: 1 });

  const [confirmDeleteGasto, setConfirmDeleteGasto] = useState<Gasto | null>(null);
  const [uploadingFor, setUploadingFor] = useState<number | null>(null);

  const resetForm = () => { setForm({ ...EMPTY_FORM }); setEditingId(null); setFile(null); };

  const subirComprobanteSiCorresponde = async (gastoId: number) => {
    if (!file) return;
    try {
      await uploadFile(`/api/finanzas/gastos/${gastoId}/comprobante`, file);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "El gasto se guardó, pero el comprobante no se pudo subir");
    }
  };

  const handleSave = async () => {
    if (!validate(
      [!!form.descripcion.trim(), "Ingresa una descripcion"],
      [!!form.monto && form.monto > 0, "El monto debe ser mayor a cero"],
    )) return;
    if (editingId !== null) {
      const res = await put(editingId, { categoria: form.categoria, descripcion: form.descripcion, monto: form.monto, tipo: form.tipo, proveedor_id: form.proveedor_id });
      if (res !== null) {
        await subirComprobanteSiCorresponde(editingId);
        toast.success("Gasto actualizado"); resetForm(); refetch();
      }
      else { toast.error("Error al actualizar el gasto"); }
    } else {
      setSaving(true);
      try {
        const res = await api.post("/api/finanzas/gastos", form, { params: { consorcio_id: CONSORCIO, periodo: PERIODO } });
        await subirComprobanteSiCorresponde(res.data.id);
        toast.success(`Gasto guardado: ${form.descripcion}`);
        resetForm(); refetch();
      } catch (err: any) {
        toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al guardar el gasto");
      } finally {
        setSaving(false);
      }
    }
  };

  const handleEdit = (g: Gasto) => {
    setEditingId(g.id);
    setForm({ categoria: g.categoria, descripcion: g.descripcion, monto: g.monto, tipo: g.tipo ?? undefined, proveedor_id: g.proveedor_id });
    setFile(null);
  };

  const proveedorNombre = (pid?: number) => {
    if (!pid) return null;
    return (proveedores ?? []).find((p) => p.id === pid)?.razon_social ?? null;
  };

  const handleDelete = async (g: Gasto) => {
    const ok = await remove(g.id);
    if (ok) { toast.success(`Gasto eliminado: ${g.descripcion}`); refetch(); }
    else { toast.error("Error al eliminar el gasto"); }
    setConfirmDeleteGasto(null);
  };

  const handleAbrirComprobante = async (g: Gasto) => {
    setUploadingFor(g.id);
    try {
      await openPdf(`/api/finanzas/gastos/${g.id}/comprobante`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "No se pudo abrir el comprobante");
    } finally {
      setUploadingFor(null);
    }
  };

  const totalCat = (cat: string) => (gastos ?? []).filter((g) => g.categoria === cat).reduce((s, g) => s + g.monto, 0);
  const totalGeneral = (gastos ?? []).reduce((s, g) => s + g.monto, 0);
  const isBusy = saving || updating;

  const [gastoSearch, setGastoSearch] = useState("");
  const gastosFiltrados = (gastos ?? []).filter((g) => {
    if (!gastoSearch.trim()) return true;
    const q = gastoSearch.trim().toLowerCase();
    return [g.descripcion, proveedorNombre(g.proveedor_id)].some((v) => (v ?? "").toLowerCase().includes(q));
  });

  // ── Tab Particulares ───────────────────────────────────────────────────────
  const [partForm, setPartForm] = useState<GastoParticularCreate>({ ...EMPTY_PART });
  const [savingPart, setSavingPart] = useState(false);
  const { data: unidades } = useGet<Unidad[]>(
    `/api/consorcios/${CONSORCIO ?? 0}/unidades`,
    CONSORCIO ? {} : null
  );
  const { data: particulares, loading: loadingPart, refetch: refetchPart } = useGet<GastoParticular[]>(
    "/api/finanzas/gastos_particulares",
    CONSORCIO ? { consorcio: CONSORCIO, periodo: PERIODO } : null
  );
  const { put: putPart, loading: updatingPart } = usePut<object, object>("/api/finanzas/gastos_particulares");
  const { remove: removePart, loading: deletingPart } = useDelete("/api/finanzas/gastos_particulares");
  const [editingPartId, setEditingPartId] = useState<number | null>(null);
  const [confirmDeletePart, setConfirmDeletePart] = useState<GastoParticular | null>(null);

  const resetPartForm = () => { setPartForm({ ...EMPTY_PART }); setEditingPartId(null); };

  const handleSavePart = async () => {
    if (!validate(
      [!!partForm.unidad_id && partForm.unidad_id !== 0, "Selecciona una unidad"],
      [!!partForm.descripcion.trim(), "Ingresa una descripcion"],
      [!!partForm.monto && partForm.monto > 0, "El monto debe ser mayor a cero"],
    )) return;
    if (editingPartId !== null) {
      const res = await putPart(editingPartId, partForm);
      if (res !== null) { toast.success("Gasto particular actualizado"); resetPartForm(); refetchPart(); }
      else { toast.error("Error al actualizar"); }
      return;
    }
    setSavingPart(true);
    try {
      await api.post("/api/finanzas/gastos_particulares", partForm, { params: { consorcio_id: CONSORCIO, periodo: PERIODO } });
      toast.success(`Gasto particular guardado: ${partForm.descripcion}`);
      resetPartForm(); refetchPart();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al guardar");
    } finally {
      setSavingPart(false);
    }
  };

  const handleEditPart = (p: GastoParticular) => {
    setEditingPartId(p.id);
    setPartForm({ unidad_id: p.unidad_id, descripcion: p.descripcion, monto: p.monto });
  };

  const handleDeletePart = async (p: GastoParticular) => {
    const ok = await removePart(p.id);
    if (ok) { toast.success(`Eliminado: ${p.descripcion}`); refetchPart(); }
    else { toast.error("Error al eliminar"); }
    setConfirmDeletePart(null);
  };

  const unidadNombre = (uid: number) => {
    const u = (unidades ?? []).find((u) => u.id === uid);
    if (!u) return `UF ${uid}`;
    const nombre = u.propietario || u.inquilino || "";
    return `UF ${u.unidad}${nombre ? " - " + nombre : ""}`;
  };

  const totalParticulares = (particulares ?? []).reduce((s, p) => s + p.monto, 0);

  // ── Render ─────────────────────────────────────────────────────────────────

  const tabClass = (tab: Tab) =>
    cn(
      "px-4 py-1.5 text-[13px] border-b-2 transition-colors",
      activeTab === tab ? "font-semibold text-accent border-accent" : "font-normal text-text2 border-transparent"
    );

  if (connecting) return <ConnectingState />;

  return (
    <div className="flex flex-col h-full gap-0">
      {/* Tabs */}
      <div className="flex gap-0 border-b mb-4 border-border">
        <button className={tabClass("generales")} onClick={() => setActiveTab("generales")}>Gastos Generales</button>
        <button className={tabClass("particulares")} onClick={() => setActiveTab("particulares")}>Gastos Particulares</button>
      </div>

      {/* ── Tab: Gastos Generales ── */}
      {activeTab === "generales" && (
        <div className="grid grid-cols-2 gap-5 flex-1 overflow-hidden">
          <div className="flex flex-col gap-4">
            <div className="rounded-xl border p-5 shadow-card bg-surface border-border">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Receipt size={16} className="text-accent" />
                  <h2 className="text-sm font-semibold text-text">
                    {editingId !== null ? "Editar Comprobante" : "Nuevo Comprobante"}
                  </h2>
                </div>
                {editingId !== null && (
                  <button onClick={resetForm} className="text-xs flex items-center gap-1 hover:opacity-70 text-text2">
                    <X size={12} />Cancelar
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1"><label className="text-xs text-text2">Categoria</label>
                  <Select items={CATEGORIAS} value={form.categoria} onValueChange={(v) => setForm((f) => ({ ...f, categoria: v as "A" | "B" | "C" }))}>
                    <SelectTrigger className="bg-surface2 border-border text-text"><SelectValue /></SelectTrigger>
                    <SelectContent className="bg-surface2 border-border">
                      {CATEGORIAS.map((cat) => (<SelectItem key={cat.value} value={cat.value} className="text-text">{cat.label}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1"><label className="text-xs text-text2">Tipo</label>
                  <Select items={TIPOS} value={form.tipo ?? "ordinario"} onValueChange={(v) => setForm((f) => ({ ...f, tipo: v ?? undefined }))}>
                    <SelectTrigger className="bg-surface2 border-border text-text"><SelectValue /></SelectTrigger>
                    <SelectContent className="bg-surface2 border-border">
                      {TIPOS.map((t) => (<SelectItem key={t.value} value={t.value} className="text-text">{t.label}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1"><label className="text-xs text-text2">Monto</label>
                  <Input type="number" value={form.monto || ""} onChange={(e) => setForm((f) => ({ ...f, monto: parseFloat(e.target.value) || 0 }))} placeholder="0.00" className="bg-surface2 border-border text-text" />
                </div>
                <div className="flex flex-col gap-1"><label className="text-xs text-text2">&nbsp;</label>
                  {/* spacer para alinear monto con tipo en la grilla */}
                  <div />
                </div>
                <div className="col-span-2 flex flex-col gap-1"><label className="text-xs text-text2">Descripcion</label>
                  <Input value={form.descripcion} onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))} placeholder="Descripcion del gasto" className="bg-surface2 border-border text-text" />
                </div>
                <div className="col-span-2 flex flex-col gap-1"><label className="text-xs text-text2">Proveedor (opcional)</label>
                  <Select
                    items={[{ value: "none", label: "Sin proveedor" }, ...(proveedores ?? []).map((p) => ({ value: String(p.id), label: p.razon_social }))]}
                    value={form.proveedor_id ? String(form.proveedor_id) : "none"}
                    onValueChange={(v) => setForm((f) => ({ ...f, proveedor_id: v && v !== "none" ? parseInt(v) : undefined }))}
                  >
                    <SelectTrigger className="bg-surface2 border-border text-text">
                      <SelectValue placeholder="Sin proveedor" />
                    </SelectTrigger>
                    <SelectContent className="bg-surface2 border-border">
                      <SelectItem value="none" className="text-text2">Sin proveedor</SelectItem>
                      {(proveedores ?? []).map((p) => (
                        <SelectItem key={p.id} value={String(p.id)} className="text-text">{p.razon_social}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button onClick={handleSave} disabled={isBusy || !form.descripcion} className="w-full mt-4 gap-2 bg-accent text-white">
                {editingId !== null ? <Pencil size={14} /> : <Plus size={14} />}
                {isBusy ? "Guardando..." : (editingId !== null ? "Actualizar Comprobante" : "Agregar Comprobante")}
              </Button>
            </div>
            <div {...getRootProps()} className={cn(
              "flex-1 rounded-xl border-2 border-dashed flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors min-h-40",
              isDragActive ? "border-accent bg-accent/5" : "border-border bg-surface"
            )}>
              <input {...getInputProps()} />
              <UploadCloud size={32} className={isDragActive ? "text-accent" : "text-border"} />
              {file ? (<div className="text-center"><p className="text-sm font-medium text-text">{file.name}</p><p className="text-xs mt-1 text-text2">{(file.size / 1024).toFixed(1)} KB</p></div>
              ) : (<div className="text-center px-4"><p className="text-sm font-medium text-text2">Arrastra el comprobante aqui</p><p className="text-xs mt-1 text-border">PDF o imagen (JPG, PNG)</p></div>)}
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-3 gap-3">
              {CATEGORIAS.map((cat) => (<div key={cat.value} title={cat.label} className="rounded-xl p-3 border shadow-card text-center bg-surface border-border"><p className="text-xs mb-1 text-text2">Cat {cat.value}</p><p className="text-sm font-bold text-accent">{fmtCurrency(totalCat(cat.value))}</p></div>))}
            </div>
            <div className="flex-1 rounded-xl border shadow-card overflow-hidden flex flex-col bg-surface border-border">
              <div className="px-4 py-3 border-b flex flex-col gap-2 bg-surface2 border-border">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-text">Carga mensual - {PERIODO}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-accent/15 text-accent">{(gastos ?? []).length} items</span>
                </div>
                {(gastos ?? []).length > 0 && (
                  <Input value={gastoSearch} onChange={(e) => setGastoSearch(e.target.value)} placeholder="Buscar por descripcion o proveedor..." className="h-7 text-xs bg-surface border-border text-text" />
                )}
              </div>
              <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
                {loading && [0,1,2].map((i) => <Skeleton key={i} className="h-12 rounded-lg bg-surface2" />)}
                {!loading && (gastos ?? []).length === 0 && (<div className="flex flex-col items-center justify-center flex-1 gap-2 py-8"><Receipt size={28} className="text-border" /><p className="text-xs text-text2">Sin gastos cargados</p></div>)}
                {!loading && (gastos ?? []).length > 0 && gastosFiltrados.length === 0 && (<div className="flex flex-col items-center justify-center flex-1 gap-2 py-8"><Receipt size={28} className="text-border" /><p className="text-xs text-text2">Ningún gasto coincide con "{gastoSearch}"</p></div>)}
                {gastosFiltrados.map((g) => (
                  <div key={g.id} className={cn(
                    "flex items-center gap-3 p-3 rounded-lg transition-all",
                    editingId === g.id ? "bg-accent/10 outline outline-1 outline-accent/30" : "bg-surface2"
                  )}>
                    <span className={cn(
                      "w-6 h-6 rounded-md text-xs font-bold flex items-center justify-center text-white shrink-0",
                      g.categoria === "A" ? "bg-accent" : g.categoria === "B" ? "bg-success" : "bg-warning"
                    )}>{g.categoria}</span>
                    {/* Badge tipo */}
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded shrink-0",
                      (g.tipo ?? "ordinario") === "extraordinario" ? "bg-warning/15 text-warning" : "bg-accent/10 text-accent"
                    )}>
                      {(g.tipo ?? "ordinario") === "extraordinario" ? "Ext" : "Ord"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate text-text">{g.descripcion}</p>
                      {proveedorNombre(g.proveedor_id) && <p className="text-xs truncate text-text2">{proveedorNombre(g.proveedor_id)}</p>}
                    </div>
                    <span className="text-sm font-semibold shrink-0 text-text">{fmtCurrency(g.monto)}</span>
                    <div className="flex gap-1 shrink-0">
                      {g.comprobante_path && (
                        <button onClick={() => handleAbrirComprobante(g)} disabled={uploadingFor === g.id} className="w-6 h-6 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40 text-success bg-success/10" title="Ver comprobante adjunto"><Paperclip size={11} /></button>
                      )}
                      <button onClick={() => handleEdit(g)} className="w-6 h-6 rounded flex items-center justify-center hover:opacity-70 transition-opacity text-accent bg-accent/10" title="Editar"><Pencil size={11} /></button>
                      <button onClick={() => setConfirmDeleteGasto(g)} disabled={deleting} className="w-6 h-6 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40 text-danger bg-danger/10" title="Eliminar"><Trash2 size={11} /></button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-4 py-3 border-t flex items-center justify-between border-border bg-surface2">
                <span className="text-sm font-semibold text-text">Total del mes</span>
                <span className="text-lg font-bold text-accent">{fmtCurrency(totalGeneral)}</span>
                <Button size="sm" onClick={() => { toast.promise(openPdf(`/api/reportes/general/${CONSORCIO}/${PERIODO}`), { loading: "Generando PDF...", success: "PDF abierto", error: (e: unknown) => e instanceof Error ? e.message : "Error al generar PDF" }); }} variant="soft" className="h-7 px-3 text-xs gap-1"><FileText size={12} />PDF General</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Gastos Particulares ── */}
      {activeTab === "particulares" && (
        <div className="grid grid-cols-2 gap-5 flex-1 overflow-hidden">
          {/* Formulario */}
          <div className="flex flex-col gap-4">
            <div className="rounded-xl border p-5 shadow-card bg-surface border-border">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <User size={16} className="text-accent" />
                  <h2 className="text-sm font-semibold text-text">
                    {editingPartId !== null ? "Editar Gasto Particular" : "Nuevo Gasto Particular"}
                  </h2>
                </div>
                {editingPartId !== null && (
                  <button onClick={resetPartForm} className="text-xs flex items-center gap-1 hover:opacity-70 text-text2">
                    <X size={12} />Cancelar
                  </button>
                )}
              </div>
              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-1"><label className="text-xs text-text2">Unidad</label>
                  <Select
                    items={(unidades ?? []).map((u) => ({
                      value: String(u.id),
                      label: `UF ${u.unidad}${(u.propietario || u.inquilino) ? ` - ${u.propietario || u.inquilino}` : ""}`,
                    }))}
                    value={partForm.unidad_id ? String(partForm.unidad_id) : ""}
                    onValueChange={(v) => setPartForm((f) => ({ ...f, unidad_id: parseInt(v ?? "0") }))}
                  >
                    <SelectTrigger className="bg-surface2 border-border text-text">
                      <SelectValue placeholder="Seleccionar unidad..." />
                    </SelectTrigger>
                    <SelectContent className="bg-surface2 border-border">
                      {(unidades ?? []).map((u) => (
                        <SelectItem key={u.id} value={String(u.id)} className="text-text">
                          UF {u.unidad}{(u.propietario || u.inquilino) ? ` - ${u.propietario || u.inquilino}` : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1"><label className="text-xs text-text2">Descripcion</label>
                  <Input value={partForm.descripcion} onChange={(e) => setPartForm((f) => ({ ...f, descripcion: e.target.value }))} placeholder="Descripcion del gasto" className="bg-surface2 border-border text-text" />
                </div>
                <div className="flex flex-col gap-1"><label className="text-xs text-text2">Monto</label>
                  <Input type="number" value={partForm.monto || ""} onChange={(e) => setPartForm((f) => ({ ...f, monto: parseFloat(e.target.value) || 0 }))} placeholder="0.00" className="bg-surface2 border-border text-text" />
                </div>
              </div>
              <Button onClick={handleSavePart} disabled={savingPart || updatingPart || !partForm.descripcion || !partForm.unidad_id} className="w-full mt-4 gap-2 bg-accent text-white">
                {editingPartId !== null ? <Pencil size={14} /> : <Plus size={14} />}
                {savingPart || updatingPart ? "Guardando..." : (editingPartId !== null ? "Actualizar Gasto Particular" : "Agregar Gasto Particular")}
              </Button>
            </div>
          </div>

          {/* Lista */}
          <div className="flex flex-col gap-4">
            <div className="flex-1 rounded-xl border shadow-card overflow-hidden flex flex-col bg-surface border-border">
              <div className="px-4 py-3 border-b flex items-center justify-between bg-surface2 border-border">
                <span className="text-sm font-medium text-text">Particulares - {PERIODO}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-accent/15 text-accent">{(particulares ?? []).length} items</span>
              </div>
              <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
                {loadingPart && [0,1,2].map((i) => <Skeleton key={i} className="h-12 rounded-lg bg-surface2" />)}
                {!loadingPart && (particulares ?? []).length === 0 && (
                  <div className="flex flex-col items-center justify-center flex-1 gap-2 py-8">
                    <User size={28} className="text-border" />
                    <p className="text-xs text-text2">Sin gastos particulares</p>
                  </div>
                )}
                {(particulares ?? []).map((p) => (
                  <div key={p.id} className={cn(
                    "flex items-center gap-3 p-3 rounded-lg",
                    editingPartId === p.id ? "bg-accent/10 outline outline-1 outline-accent/30" : "bg-surface2"
                  )}>
                    <span className="w-6 h-6 rounded-md text-xs font-bold flex items-center justify-center text-white shrink-0 bg-success">U</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate text-text">{p.descripcion}</p>
                      <p className="text-xs truncate text-text2">{unidadNombre(p.unidad_id)}</p>
                    </div>
                    <span className="text-sm font-semibold shrink-0 text-text">{fmtCurrency(p.monto)}</span>
                    <div className="flex gap-1 shrink-0">
                      <button onClick={() => handleEditPart(p)} className="w-6 h-6 rounded flex items-center justify-center hover:opacity-70 transition-opacity text-accent bg-accent/10" title="Editar"><Pencil size={11} /></button>
                      <button onClick={() => setConfirmDeletePart(p)} disabled={deletingPart} className="w-6 h-6 rounded flex items-center justify-center hover:opacity-70 transition-opacity disabled:opacity-40 text-danger bg-danger/10" title="Eliminar"><Trash2 size={11} /></button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-4 py-3 border-t flex items-center justify-between border-border bg-surface2">
                <span className="text-sm font-semibold text-text">Total particulares</span>
                <span className="text-lg font-bold text-accent">{fmtCurrency(totalParticulares)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={confirmDeleteGasto !== null}
        title="Eliminar gasto"
        description={confirmDeleteGasto ? `Se eliminará "${confirmDeleteGasto.descripcion}". Esta acción no se puede deshacer.` : undefined}
        loading={deleting}
        onConfirm={() => confirmDeleteGasto && handleDelete(confirmDeleteGasto)}
        onCancel={() => setConfirmDeleteGasto(null)}
      />
      <ConfirmDialog
        open={confirmDeletePart !== null}
        title="Eliminar gasto particular"
        description={confirmDeletePart ? `Se eliminará "${confirmDeletePart.descripcion}". Esta acción no se puede deshacer.` : undefined}
        loading={deletingPart}
        onConfirm={() => confirmDeletePart && handleDeletePart(confirmDeletePart)}
        onCancel={() => setConfirmDeletePart(null)}
      />
    </div>
  );
}

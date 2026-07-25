import { useState } from "react";
import { toast } from "sonner";
import { useGet } from "@/hooks/useApi";
import { Consorcio, Unidad } from "@/types/api";
import { useApp } from "@/contexts/AppContext";
import api from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectingState } from "@/components/ui/connecting-state";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Building2, Plus, Pencil, Trash2, Users, ChevronRight, MapPin, Hash, UploadCloud, Search } from "lucide-react";
import { ConsorcioDialog } from "./consorcios/ConsorcioDialog";
import { UnidadDialog } from "./consorcios/UnidadDialog";
import { ImportarPadronDialog } from "./consorcios/ImportarPadronDialog";
import { cn } from "@/lib/utils";

export function ConsorciosPage() {
  const { setConsorcio } = useApp();
  const { data: consorcios, loading: loadingC, connecting: connectingC, error: errorC, refetch: refetchC } = useGet<Consorcio[]>("/api/consorcios");
  const [selected, setSelected] = useState<Consorcio | null>(null);
  const { data: unidades, loading: loadingU, refetch: refetchU } = useGet<Unidad[]>(
    selected ? `/api/consorcios/${selected.id}/unidades` : "",
  );
  const [consorcioDialog, setConsorcioDialog] = useState<{ open: boolean; edit?: Consorcio }>({ open: false });
  const [unidadDialog, setUnidadDialog] = useState<{ open: boolean; edit?: Unidad }>({ open: false });
  const [importDialog, setImportDialog] = useState(false);
  const [deletingC, setDeletingC] = useState<number | null>(null);
  const [deletingU, setDeletingU] = useState<number | null>(null);
  const [confirmDeleteC, setConfirmDeleteC] = useState<Consorcio | null>(null);
  const [confirmDeleteU, setConfirmDeleteU] = useState<Unidad | null>(null);
  const [deleteImpact, setDeleteImpact] = useState<number | null>(null);
  const [unitSearch, setUnitSearch] = useState("");

  const askDeleteConsorcio = async (c: Consorcio) => {
    setConfirmDeleteC(c);
    setDeleteImpact(null);
    try {
      const res = await api.get<Unidad[]>(`/api/consorcios/${c.id}/unidades`);
      setDeleteImpact(res.data.length);
    } catch { /* si falla el conteo, igual se puede confirmar sin el detalle */ }
  };

  const deleteConsorcio = async (c: Consorcio) => {
    setDeletingC(c.id);
    try {
      await api.delete(`/api/consorcios/${c.id}`);
      if (selected?.id === c.id) setSelected(null);
      refetchC();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al eliminar consorcio");
    } finally { setDeletingC(null); setConfirmDeleteC(null); }
  };

  const unidadesFiltradas = (unidades ?? []).filter((u) => {
    if (!unitSearch.trim()) return true;
    const q = unitSearch.trim().toLowerCase();
    return [u.unidad, u.propietario, u.inquilino, u.email].some((v) => (v ?? "").toLowerCase().includes(q));
  });

  const deleteUnidad = async (u: Unidad) => {
    setDeletingU(u.id);
    try {
      await api.delete(`/api/unidades/${u.id}`);
      refetchU();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al eliminar unidad");
    } finally { setDeletingU(null); setConfirmDeleteU(null); }
  };

  return (
    <div className="grid grid-cols-5 gap-5 h-[calc(100vh-112px)]">
      <div className="col-span-2 flex flex-col gap-3 overflow-hidden">
        <div className="flex items-center justify-between shrink-0">
          <h2 className="text-sm font-semibold text-text">Consorcios</h2>
          <Button size="sm" onClick={() => setConsorcioDialog({ open: true })} variant="soft" className="h-7 px-3 text-xs gap-1">
            <Plus size={12} /> Nuevo
          </Button>
        </div>
        <div className="flex flex-col gap-2 overflow-y-auto flex-1">
          {connectingC && <ConnectingState />}
          {!connectingC && loadingC && [0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-20 rounded-xl bg-surface" />
          ))}
          {errorC && (
            <div className="flex flex-col items-center justify-center gap-3 py-12 rounded-xl border border-danger bg-danger/5">
              <p className="text-xs font-mono px-3 text-center text-danger">Error: {errorC}</p>
              <button onClick={refetchC} className="text-xs underline text-accent">Reintentar</button>
            </div>
          )}
          {!connectingC && !loadingC && !errorC && (consorcios ?? []).length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 py-12">
              <Building2 size={36} className="text-border" />
              <p className="text-xs text-text2">Sin consorcios registrados</p>
            </div>
          )}
          {(consorcios ?? []).map((c) => {
            const isActive = selected?.id === c.id;
            return (
              <div key={c.id} onClick={() => { const next = isActive ? null : c; setSelected(next); if (next) setConsorcio(next.id, next.nombre); }}
                className={cn(
                  "rounded-xl border p-4 cursor-pointer transition-all",
                  isActive ? "bg-accent/[0.08] border-accent/40" : "bg-surface border-border"
                )}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center shrink-0", isActive ? "bg-accent/20" : "bg-white/5")}>
                      <Building2 size={16} className={isActive ? "text-accent" : "text-text2"} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate text-text">{c.nombre}</p>
                      {c.direccion && (
                        <p className="text-xs flex items-center gap-1 mt-0.5 truncate text-text2">
                          <MapPin size={10} />{c.direccion}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
                    <button onClick={() => setConsorcioDialog({ open: true, edit: c })}
                      className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/10 transition-colors">
                      <Pencil size={12} className="text-text2" />
                    </button>
                    <button onClick={() => askDeleteConsorcio(c)} disabled={deletingC === c.id}
                      className="w-6 h-6 rounded flex items-center justify-center hover:bg-red-500/10 transition-colors">
                      <Trash2 size={12} className="text-danger" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-white/5 text-text2">
                    <Users size={10} />{c.unidades} unidades
                  </span>
                  {c.cuit && (
                    <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-white/5 text-text2">
                      <Hash size={10} />{c.cuit}
                    </span>
                  )}
                  {isActive && <ChevronRight size={12} className="ml-auto text-accent" />}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="col-span-3 flex flex-col gap-3 overflow-hidden">
        {!selected ? (
          <div className="flex-1 rounded-xl border flex flex-col items-center justify-center gap-3 bg-surface border-border">
            <Building2 size={40} className="text-border" />
            <p className="text-sm text-text2">Selecciona un consorcio para ver sus unidades</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between shrink-0">
              <div>
                <h2 className="text-sm font-semibold text-text">{selected.nombre}</h2>
                <p className="text-xs mt-0.5 text-text2">{(unidades ?? []).length} unidades registradas</p>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={() => setImportDialog(true)} className="h-7 px-3 text-xs gap-1 bg-white/5 text-text2 border border-border">
                  <UploadCloud size={12} /> Importar UF
                </Button>
                <Button size="sm" onClick={() => setUnidadDialog({ open: true })} variant="soft" className="h-7 px-3 text-xs gap-1">
                  <Plus size={12} /> Nueva unidad
                </Button>
              </div>
            </div>
            {(unidades ?? []).length > 0 && (
              <div className="relative shrink-0">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text2" />
                <Input
                  value={unitSearch}
                  onChange={(e) => setUnitSearch(e.target.value)}
                  placeholder="Buscar por unidad, propietario, inquilino o email..."
                  className="pl-8 h-8 text-sm bg-surface2 border-border text-text"
                />
              </div>
            )}
            <div className="flex-1 rounded-xl border overflow-hidden flex flex-col bg-surface border-border">
              {loadingU ? (
                <div className="flex flex-col gap-2 p-3">
                  {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-10 rounded-lg bg-surface2" />)}
                </div>
              ) : (unidades ?? []).length === 0 ? (
                <div className="flex flex-col items-center justify-center flex-1 gap-3 py-12">
                  <Users size={36} className="text-border" />
                  <p className="text-xs text-text2">Sin unidades registradas</p>
                </div>
              ) : unidadesFiltradas.length === 0 ? (
                <div className="flex flex-col items-center justify-center flex-1 gap-3 py-12">
                  <Search size={36} className="text-border" />
                  <p className="text-xs text-text2">Ninguna unidad coincide con "{unitSearch}"</p>
                </div>
              ) : (
                <div className="overflow-y-auto flex-1">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border">
                        {["NRO", "PROPIETARIO", "PISO/DPTO", "EMAIL", "COEF A", ""].map((h) => (
                          <TableHead key={h} className="text-xs font-semibold uppercase tracking-wider text-text2 bg-surface2">{h}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {unidadesFiltradas.map((u) => (
                        <TableRow key={u.id} className="transition-colors hover:bg-white/[0.02] border-border">
                          <TableCell className="font-mono text-sm font-semibold text-text">{u.unidad}</TableCell>
                          <TableCell>
                            <p className="text-sm text-text">{u.propietario || "—"}</p>
                            {u.inquilino && <p className="text-xs text-text2">Inq: {u.inquilino}</p>}
                          </TableCell>
                          <TableCell className="text-sm text-text2">
                            {[u.piso, u.dpto].filter(Boolean).join(" ") || "—"}
                          </TableCell>
                          <TableCell className="text-xs text-text2">{u.email || "—"}</TableCell>
                          <TableCell className="font-mono text-xs text-text2">{u.coef_a.toFixed(4)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <button onClick={() => setUnidadDialog({ open: true, edit: u })}
                                className="w-7 h-7 rounded flex items-center justify-center hover:bg-white/10 transition-colors">
                                <Pencil size={13} className="text-text2" />
                              </button>
                              <button onClick={() => setConfirmDeleteU(u)} disabled={deletingU === u.id}
                                className="w-7 h-7 rounded flex items-center justify-center hover:bg-red-500/10 transition-colors">
                                <Trash2 size={13} className="text-danger" />
                              </button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {consorcioDialog.open && (
        <ConsorcioDialog initial={consorcioDialog.edit} onClose={() => setConsorcioDialog({ open: false })} onSaved={refetchC} />
      )}
      {unidadDialog.open && selected && (
        <UnidadDialog consorcioId={selected.id} initial={unidadDialog.edit} onClose={() => setUnidadDialog({ open: false })} onSaved={refetchU} />
      )}
      {importDialog && selected && (
        <ImportarPadronDialog
          consorcioId={selected.id}
          onClose={() => setImportDialog(false)}
          onSaved={() => { setImportDialog(false); refetchU(); }}
        />
      )}

      <ConfirmDialog
        open={confirmDeleteC !== null}
        title="Eliminar consorcio"
        description={confirmDeleteC
          ? `Se eliminará "${confirmDeleteC.nombre}"${deleteImpact !== null ? ` junto con sus ${deleteImpact} unidades` : ""} y todos los gastos, pagos y proveedores asociados. Esta acción no se puede deshacer.`
          : undefined}
        loading={deletingC !== null}
        onConfirm={() => confirmDeleteC && deleteConsorcio(confirmDeleteC)}
        onCancel={() => { setConfirmDeleteC(null); setDeleteImpact(null); }}
      />
      <ConfirmDialog
        open={confirmDeleteU !== null}
        title="Eliminar unidad"
        description={confirmDeleteU ? `Se eliminará la unidad ${confirmDeleteU.unidad}. Esta acción no se puede deshacer.` : undefined}
        loading={deletingU !== null}
        onConfirm={() => confirmDeleteU && deleteUnidad(confirmDeleteU)}
        onCancel={() => setConfirmDeleteU(null)}
      />
    </div>
  );
}

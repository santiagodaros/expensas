import { useState } from "react";
import { useGet } from "@/hooks/useApi";
import { Consorcio, ConsorcioCreate, Unidad, UnidadCreate } from "@/types/api";
import api from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Building2, Plus, Pencil, Trash2, Users, ChevronRight, MapPin, Hash } from "lucide-react";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium" style={{ color: "var(--color-text2)" }}>{label}</label>
      {children}
    </div>
  );
}

function TInput(props: React.ComponentProps<typeof Input>) {
  return (
    <Input
      {...props}
      style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)", ...props.style }}
    />
  );
}

const EMPTY_C: ConsorcioCreate = { nombre: "", cuit: "", direccion: "", unidades: 0, reserva_pct: 5, dia_vto: 10 };

function ConsorcioDialog({ initial, onClose, onSaved }: { initial?: Consorcio; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<ConsorcioCreate>(
    initial
      ? { nombre: initial.nombre, cuit: initial.cuit ?? "", direccion: initial.direccion ?? "", unidades: initial.unidades, reserva_pct: initial.reserva_pct, dia_vto: initial.dia_vto }
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
    } finally { setSaving(false); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", color: "var(--color-text)" }}>
        <DialogHeader><DialogTitle style={{ color: "var(--color-text)" }}>{initial ? "Editar Consorcio" : "Nuevo Consorcio"}</DialogTitle></DialogHeader>
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
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} style={{ color: "var(--color-text2)" }}>Cancelar</Button>
          <Button onClick={handleSave} disabled={saving || !form.nombre.trim()} style={{ backgroundColor: "var(--color-accent)", color: "white" }}>
            {saving ? "Guardando..." : initial ? "Guardar cambios" : "Crear consorcio"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

const EMPTY_U: UnidadCreate = { unidad: "", piso: "", dpto: "", propietario: "", inquilino: "", coef_a: 0, coef_b: 0, coef_c: 0, email: "" };

function UnidadDialog({ consorcioId, initial, onClose, onSaved }: { consorcioId: number; initial?: Unidad; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<UnidadCreate>(
    initial
      ? { unidad: initial.unidad, piso: initial.piso, dpto: initial.dpto, propietario: initial.propietario ?? "", inquilino: initial.inquilino ?? "", coef_a: initial.coef_a, coef_b: initial.coef_b, coef_c: initial.coef_c, email: initial.email ?? "" }
      : { ...EMPTY_U }
  );
  const [saving, setSaving] = useState(false);
  const set = (k: keyof UnidadCreate, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.unidad.trim()) return;
    setSaving(true);
    try {
      initial ? await api.put(`/api/unidades/${initial.id}`, form) : await api.post(`/api/consorcios/${consorcioId}/unidades`, form);
      onSaved(); onClose();
    } finally { setSaving(false); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", color: "var(--color-text)" }}>
        <DialogHeader><DialogTitle style={{ color: "var(--color-text)" }}>{initial ? "Editar Unidad" : "Nueva Unidad"}</DialogTitle></DialogHeader>
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-3 gap-3">
            <Field label="Unidad *"><TInput value={form.unidad} onChange={(e) => set("unidad", e.target.value)} placeholder="1A" /></Field>
            <Field label="Piso"><TInput value={form.piso} onChange={(e) => set("piso", e.target.value)} placeholder="1" /></Field>
            <Field label="Dpto"><TInput value={form.dpto} onChange={(e) => set("dpto", e.target.value)} placeholder="A" /></Field>
          </div>
          <Field label="Propietario"><TInput value={form.propietario ?? ""} onChange={(e) => set("propietario", e.target.value)} placeholder="Juan Garcia" /></Field>
          <Field label="Inquilino"><TInput value={form.inquilino ?? ""} onChange={(e) => set("inquilino", e.target.value)} placeholder="Maria Lopez" /></Field>
          <Field label="Email"><TInput type="email" value={form.email ?? ""} onChange={(e) => set("email", e.target.value)} placeholder="correo@ejemplo.com" /></Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Coef A"><TInput type="number" value={form.coef_a} onChange={(e) => set("coef_a", parseFloat(e.target.value) || 0)} step={0.001} min={0} /></Field>
            <Field label="Coef B"><TInput type="number" value={form.coef_b} onChange={(e) => set("coef_b", parseFloat(e.target.value) || 0)} step={0.001} min={0} /></Field>
            <Field label="Coef C"><TInput type="number" value={form.coef_c} onChange={(e) => set("coef_c", parseFloat(e.target.value) || 0)} step={0.001} min={0} /></Field>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} style={{ color: "var(--color-text2)" }}>Cancelar</Button>
          <Button onClick={handleSave} disabled={saving || !form.unidad.trim()} style={{ backgroundColor: "var(--color-accent)", color: "white" }}>
            {saving ? "Guardando..." : initial ? "Guardar cambios" : "Crear unidad"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ConsorciosPage() {
  const { data: consorcios, loading: loadingC, error: errorC, refetch: refetchC } = useGet<Consorcio[]>("/api/consorcios");
  const [selected, setSelected] = useState<Consorcio | null>(null);
  const { data: unidades, loading: loadingU, refetch: refetchU } = useGet<Unidad[]>(
    selected ? `/api/consorcios/${selected.id}/unidades` : "",
  );
  const [consorcioDialog, setConsorcioDialog] = useState<{ open: boolean; edit?: Consorcio }>({ open: false });
  const [unidadDialog, setUnidadDialog] = useState<{ open: boolean; edit?: Unidad }>({ open: false });
  const [deletingC, setDeletingC] = useState<number | null>(null);
  const [deletingU, setDeletingU] = useState<number | null>(null);

  const deleteConsorcio = async (id: number) => {
    if (!confirm("Eliminar este consorcio y todas sus unidades?")) return;
    setDeletingC(id);
    try {
      await api.delete(`/api/consorcios/${id}`);
      if (selected?.id === id) setSelected(null);
      refetchC();
    } finally { setDeletingC(null); }
  };

  const deleteUnidad = async (id: number) => {
    if (!confirm("Eliminar esta unidad?")) return;
    setDeletingU(id);
    try {
      await api.delete(`/api/unidades/${id}`);
      refetchU();
    } finally { setDeletingU(null); }
  };

  return (
    <div className="grid grid-cols-5 gap-5" style={{ height: "calc(100vh - 112px)" }}>
      <div className="col-span-2 flex flex-col gap-3 overflow-hidden">
        <div className="flex items-center justify-between shrink-0">
          <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>Consorcios</h2>
          <Button size="sm" onClick={() => setConsorcioDialog({ open: true })} className="h-7 px-3 text-xs gap-1"
            style={{ backgroundColor: "rgba(59,130,246,0.15)", color: "var(--color-accent)", border: "1px solid rgba(59,130,246,0.3)" }}>
            <Plus size={12} /> Nuevo
          </Button>
        </div>
        <div className="flex flex-col gap-2 overflow-y-auto flex-1">
          {loadingC && [0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-20 rounded-xl" style={{ backgroundColor: "var(--color-surface)" }} />
          ))}
          {errorC && (
            <div className="flex flex-col items-center justify-center gap-3 py-12 rounded-xl border" style={{ borderColor: "var(--color-danger)", backgroundColor: "rgba(239,68,68,0.05)" }}>
              <p className="text-xs font-mono px-3 text-center" style={{ color: "var(--color-danger)" }}>Error: {errorC}</p>
              <button onClick={refetchC} className="text-xs underline" style={{ color: "var(--color-accent)" }}>Reintentar</button>
            </div>
          )}
          {!loadingC && !errorC && (consorcios ?? []).length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 py-12">
              <Building2 size={36} style={{ color: "var(--color-border)" }} />
              <p className="text-xs" style={{ color: "var(--color-text2)" }}>Sin consorcios registrados</p>
            </div>
          )}
          {(consorcios ?? []).map((c) => {
            const isActive = selected?.id === c.id;
            return (
              <div key={c.id} onClick={() => setSelected(isActive ? null : c)}
                className="rounded-xl border p-4 cursor-pointer transition-all"
                style={{ backgroundColor: isActive ? "rgba(59,130,246,0.08)" : "var(--color-surface)", borderColor: isActive ? "rgba(59,130,246,0.4)" : "var(--color-border)" }}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                      style={{ backgroundColor: isActive ? "rgba(59,130,246,0.2)" : "rgba(255,255,255,0.05)" }}>
                      <Building2 size={16} style={{ color: isActive ? "var(--color-accent)" : "var(--color-text2)" }} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate" style={{ color: "var(--color-text)" }}>{c.nombre}</p>
                      {c.direccion && (
                        <p className="text-xs flex items-center gap-1 mt-0.5 truncate" style={{ color: "var(--color-text2)" }}>
                          <MapPin size={10} />{c.direccion}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
                    <button onClick={() => setConsorcioDialog({ open: true, edit: c })}
                      className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/10 transition-colors">
                      <Pencil size={12} style={{ color: "var(--color-text2)" }} />
                    </button>
                    <button onClick={() => deleteConsorcio(c.id)} disabled={deletingC === c.id}
                      className="w-6 h-6 rounded flex items-center justify-center hover:bg-red-500/10 transition-colors">
                      <Trash2 size={12} style={{ color: "var(--color-danger)" }} />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: "rgba(255,255,255,0.05)", color: "var(--color-text2)" }}>
                    <Users size={10} />{c.unidades} unidades
                  </span>
                  {c.cuit && (
                    <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: "rgba(255,255,255,0.05)", color: "var(--color-text2)" }}>
                      <Hash size={10} />{c.cuit}
                    </span>
                  )}
                  {isActive && <ChevronRight size={12} className="ml-auto" style={{ color: "var(--color-accent)" }} />}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="col-span-3 flex flex-col gap-3 overflow-hidden">
        {!selected ? (
          <div className="flex-1 rounded-xl border flex flex-col items-center justify-center gap-3"
            style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}>
            <Building2 size={40} style={{ color: "var(--color-border)" }} />
            <p className="text-sm" style={{ color: "var(--color-text2)" }}>Selecciona un consorcio para ver sus unidades</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between shrink-0">
              <div>
                <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>{selected.nombre}</h2>
                <p className="text-xs mt-0.5" style={{ color: "var(--color-text2)" }}>{(unidades ?? []).length} unidades registradas</p>
              </div>
              <Button size="sm" onClick={() => setUnidadDialog({ open: true })} className="h-7 px-3 text-xs gap-1"
                style={{ backgroundColor: "rgba(59,130,246,0.15)", color: "var(--color-accent)", border: "1px solid rgba(59,130,246,0.3)" }}>
                <Plus size={12} /> Nueva unidad
              </Button>
            </div>
            <div className="flex-1 rounded-xl border overflow-hidden flex flex-col"
              style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}>
              {loadingU ? (
                <div className="flex flex-col gap-2 p-3">
                  {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-10 rounded-lg" style={{ backgroundColor: "var(--color-surface2)" }} />)}
                </div>
              ) : (unidades ?? []).length === 0 ? (
                <div className="flex flex-col items-center justify-center flex-1 gap-3 py-12">
                  <Users size={36} style={{ color: "var(--color-border)" }} />
                  <p className="text-xs" style={{ color: "var(--color-text2)" }}>Sin unidades registradas</p>
                </div>
              ) : (
                <div className="overflow-y-auto flex-1">
                  <Table>
                    <TableHeader>
                      <TableRow style={{ borderColor: "var(--color-border)" }}>
                        {["NRO", "PROPIETARIO", "PISO/DPTO", "EMAIL", "COEF A", ""].map((h) => (
                          <TableHead key={h} className="text-xs font-semibold uppercase tracking-wider"
                            style={{ color: "var(--color-text2)", backgroundColor: "var(--color-surface2)" }}>{h}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(unidades ?? []).map((u) => (
                        <TableRow key={u.id} className="transition-colors hover:bg-white/[0.02]" style={{ borderColor: "var(--color-border)" }}>
                          <TableCell className="font-mono text-sm font-semibold" style={{ color: "var(--color-text)" }}>{u.unidad}</TableCell>
                          <TableCell>
                            <p className="text-sm" style={{ color: "var(--color-text)" }}>{u.propietario || "—"}</p>
                            {u.inquilino && <p className="text-xs" style={{ color: "var(--color-text2)" }}>Inq: {u.inquilino}</p>}
                          </TableCell>
                          <TableCell className="text-sm" style={{ color: "var(--color-text2)" }}>
                            {[u.piso, u.dpto].filter(Boolean).join(" ") || "—"}
                          </TableCell>
                          <TableCell className="text-xs" style={{ color: "var(--color-text2)" }}>{u.email || "—"}</TableCell>
                          <TableCell className="font-mono text-xs" style={{ color: "var(--color-text2)" }}>{u.coef_a.toFixed(4)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <button onClick={() => setUnidadDialog({ open: true, edit: u })}
                                className="w-7 h-7 rounded flex items-center justify-center hover:bg-white/10 transition-colors">
                                <Pencil size={13} style={{ color: "var(--color-text2)" }} />
                              </button>
                              <button onClick={() => deleteUnidad(u.id)} disabled={deletingU === u.id}
                                className="w-7 h-7 rounded flex items-center justify-center hover:bg-red-500/10 transition-colors">
                                <Trash2 size={13} style={{ color: "var(--color-danger)" }} />
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
    </div>
  );
}

import { useState } from "react";
import { toast } from "sonner";
import { useGet, usePost } from "@/hooks/useApi";
import { PagosResumen, PagoUnitRow } from "@/types/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { useApp } from "@/contexts/AppContext";
import { AlertTriangle, TrendingUp, DollarSign, CheckCircle2, Plus, FileText } from "lucide-react";
import { openPath } from "@tauri-apps/plugin-opener";

const API_BASE = "http://localhost:8000";
async function openPdf(url: string) {
  const res = await fetch(API_BASE + url);
  if (!res.ok) throw new Error("Error al generar PDF");
  const { path } = await res.json();
  await openPath(path);
}
const fmt = (n: number) =>
  new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(n);

type Filtro = "todos" | "mora" | "aldia";

function estadoBadge(row: PagoUnitRow) {
  if (row.pagado)
    return <Badge style={{ backgroundColor: "var(--color-success-subtle)", color: "var(--color-success)", border: "none" }}>Al dia</Badge>;
  if (row.en_mora)
    return <Badge style={{ backgroundColor: "var(--color-danger-subtle)", color: "var(--color-danger)", border: "none" }}>En Mora</Badge>;
  return <Badge style={{ backgroundColor: "var(--color-warning-subtle)", color: "var(--color-warning)", border: "none" }}>Pendiente</Badge>;
}

function Avatar({ nombre }: { nombre: string }) {
  const initials = nombre.split(" ").slice(0, 2).map((w: string) => w[0]).join("").toUpperCase();
  return (
    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
      style={{ backgroundColor: "var(--color-accent)", opacity: 0.85 }}>
      {initials}
    </div>
  );
}

interface RegistrarDialogProps { row: PagoUnitRow; onClose: () => void; onSaved: () => void; }

function RegistrarDialog({ row, onClose, onSaved }: RegistrarDialogProps) {
  const { periodo: PERIODO } = useApp();
  const [monto, setMonto] = useState(String(row.total_pagar > 0 ? row.total_pagar : 0));
  const { post, loading } = usePost<object, object>("/api/finanzas/pagos");
  const handleSave = async () => {
    const montoRecibido = parseFloat(monto) || 0;
    if (montoRecibido <= 0) { toast.error("El monto debe ser mayor a cero"); return; }
    const res = await post({
      unidad_id: row.unidad_id,
      periodo: PERIODO,
      pagado: 1,
      monto_recibido: montoRecibido,
      saldo_inicial: row.saldo_anterior,
      telec: row.telec,
      reserva: row.reserva,
      redondeo: row.redondeo,
      imp_mes_override: row.imp_mes > 0 ? row.imp_mes : undefined,
    });
    if (res) {
      toast.success(`Pago de ${row.nombre} registrado correctamente`);
      onSaved(); onClose();
    } else {
      toast.error("Error al registrar el pago");
    }
  };
  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", color: "var(--color-text)" }}>
        <DialogHeader><DialogTitle style={{ color: "var(--color-text)" }}>Registrar Pago</DialogTitle></DialogHeader>
        <div className="flex items-center gap-3 py-2">
          <Avatar nombre={row.nombre} />
          <div>
            <p className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>{row.nombre}</p>
            <p className="text-xs" style={{ color: "var(--color-text2)" }}>Unidad {row.unidad}</p>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium" style={{ color: "var(--color-text2)" }}>Monto recibido</label>
          <Input type="number" value={monto} onChange={(e) => setMonto(e.target.value)}
            style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }} />
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} style={{ color: "var(--color-text2)" }}>Cancelar</Button>
          <Button onClick={handleSave} disabled={loading} style={{ backgroundColor: "var(--color-accent)", color: "white" }}>
            {loading ? "Guardando..." : "Confirmar pago"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function EstadoPagosPage() {
  const { consorcioId: CONSORCIO, periodo: PERIODO } = useApp();
  const [filtro, setFiltro] = useState<Filtro>("todos");
  const [selected, setSelected] = useState<PagoUnitRow | null>(null);
  const { data, loading, refetch } = useGet<PagosResumen>("/api/finanzas/pagos", CONSORCIO ? { consorcio: CONSORCIO, periodo: PERIODO } : null);
  const rows = (data?.unidades ?? []).filter((r) => {
    if (filtro === "mora") return r.en_mora;
    if (filtro === "aldia") return r.pagado;
    return true;
  });
  const FiltroBtn = ({ id, label }: { id: Filtro; label: string }) => (
    <button
      onClick={() => setFiltro(id)}
      className={"px-3 py-1.5 rounded-lg text-xs font-medium transition-colors" + (filtro !== id ? " hover:bg-white/10 hover:border-white/20" : "")}
      style={{
        backgroundColor: filtro === id ? "var(--color-accent-ghost)" : "var(--color-surface2)",
        color: filtro === id ? "var(--color-accent)" : "var(--color-text2)",
        border: "1px solid " + (filtro === id ? "rgba(59,130,246,0.4)" : "var(--color-border)"),
      }}
    >
      {label}
    </button>
  );
  if (loading) return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        {[0,1,2].map((i) => <Skeleton key={i} className="h-28 rounded-xl" style={{ backgroundColor: "var(--color-surface)" }} />)}
      </div>
      <Skeleton className="h-96 rounded-xl" style={{ backgroundColor: "var(--color-surface)" }} />
    </div>
  );
  const kpis = [
    { label: "Unidades en Mora", value: String(data?.kpi_mora ?? 0), icon: <AlertTriangle size={16} style={{ color: "var(--color-danger)" }} />, color: "var(--color-danger)" },
    { label: "Recaudacion Mensual", value: fmt(data?.kpi_recaudado ?? 0), icon: <TrendingUp size={16} style={{ color: "var(--color-success)" }} />, color: "var(--color-success)" },
    { label: "Deuda Pendiente Total", value: fmt(data?.kpi_total_deuda ?? 0), icon: <DollarSign size={16} style={{ color: "var(--color-warning)" }} />, color: "var(--color-warning)" },
  ];
  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-3 gap-4">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-xl p-4 border shadow-card flex items-center gap-4" style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}>
            <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "rgba(255,255,255,0.05)" }}>{k.icon}</div>
            <div>
              <p className="text-xs" style={{ color: "var(--color-text2)" }}>{k.label}</p>
              <p className="text-xl font-bold" style={{ color: k.color }}>{k.value}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-xl border shadow-card overflow-hidden" style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}>
        <div className="flex items-center justify-between px-5 py-3 border-b" style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)" }}>
          <div className="flex items-center gap-2"><CheckCircle2 size={15} style={{ color: "var(--color-accent)" }} />
            <span className="text-sm font-medium" style={{ color: "var(--color-text)" }}>Periodo {PERIODO} - {(data?.unidades ?? []).length} unidades</span>
          </div>
          <div className="flex items-center gap-2">
            <FiltroBtn id="todos" label="Todos" /><FiltroBtn id="mora" label="En Mora" /><FiltroBtn id="aldia" label="Al dia" />
            <Button size="sm" onClick={() => { toast.promise(openPdf(`/api/reportes/general/${CONSORCIO}/${PERIODO}`), { loading: "Generando PDF...", success: "PDF abierto", error: "Error al generar PDF" }); }} className="h-7 px-3 text-xs gap-1 ml-1" style={{ backgroundColor: "var(--color-accent-subtle)", color: "var(--color-accent)", border: "1px solid rgba(59,130,246,0.3)" }}><FileText size={12} />PDF General</Button>
          </div>
        </div>
        <Table>
          <TableHeader><TableRow style={{ borderColor: "var(--color-border)" }}>
            {["UNIDAD","PROPIETARIO","ESTADO","TOTAL A PAGAR","ACCIONES"].map((h) => (
              <TableHead key={h} className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--color-text2)", backgroundColor: "var(--color-surface2)" }}>{h}</TableHead>
            ))}
          </TableRow></TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.unidad_id} className="transition-colors hover:bg-white/[0.02]" style={{ borderColor: "var(--color-border)" }}>
                <TableCell className="font-mono text-sm font-semibold" style={{ color: "var(--color-text)" }}>{row.unidad}</TableCell>
                <TableCell><div className="flex items-center gap-2.5"><Avatar nombre={row.nombre} /><span className="text-sm" style={{ color: "var(--color-text)" }}>{row.nombre}</span></div></TableCell>
                <TableCell>{estadoBadge(row)}</TableCell>
                <TableCell className="font-semibold" style={{ color: row.total_pagar > 0 ? "var(--color-danger)" : "var(--color-success)" }}>{fmt(row.total_pagar)}</TableCell>
                <TableCell><div className="flex gap-2"><Button size="sm" onClick={() => setSelected(row)} className="h-7 px-3 text-xs gap-1" style={{ backgroundColor: "var(--color-accent-subtle)", color: "var(--color-accent)", border: "1px solid rgba(59,130,246,0.3)" }}><Plus size={12} />Registrar</Button><Button size="sm" onClick={() => { toast.promise(openPdf(`/api/reportes/boleta/${row.unidad_id}/${PERIODO}`), { loading: "Generando boleta...", success: "Boleta abierta", error: "Error al generar boleta" }); }} className="h-7 px-3 text-xs gap-1" style={{ backgroundColor: "rgba(139,92,246,0.1)", color: "#8b5cf6", border: "1px solid rgba(139,92,246,0.3)" }}><FileText size={12} />Boleta</Button></div></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {selected && <RegistrarDialog row={selected} onClose={() => setSelected(null)} onSaved={refetch} />}
    </div>
  );
}

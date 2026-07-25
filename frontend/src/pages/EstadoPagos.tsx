import { useState, useEffect } from "react";
import { toast } from "sonner";
import { useGet, usePost } from "@/hooks/useApi";
import { PagosResumen, PagoUnitRow } from "@/types/api";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectingState } from "@/components/ui/connecting-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { useApp } from "@/contexts/AppContext";
import { AlertTriangle, TrendingUp, DollarSign, CheckCircle2, Plus, FileText, FileSpreadsheet, Mail, RotateCcw } from "lucide-react";
import api, { openPdf } from "@/lib/api";
import { cn, fmtCurrency } from "@/lib/utils";

type Filtro = "todos" | "mora" | "aldia";

function estadoBadge(row: PagoUnitRow) {
  if (row.pagado)
    return <Badge className="bg-success-subtle text-success border-none">Al dia</Badge>;
  if (row.en_mora)
    return <Badge className="bg-danger-subtle text-danger border-none">En Mora</Badge>;
  return <Badge className="bg-warning-subtle text-warning border-none">Pendiente</Badge>;
}

function Avatar({ nombre }: { nombre: string }) {
  const initials = nombre.split(" ").slice(0, 2).map((w: string) => w[0]).join("").toUpperCase();
  return (
    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 bg-accent opacity-85">
      {initials}
    </div>
  );
}

interface RegistrarDialogProps { row: PagoUnitRow; onClose: () => void; onSaved: () => void; }

function RegistrarDialog({ row, onClose, onSaved }: RegistrarDialogProps) {
  const { periodo: PERIODO } = useApp();
  // Si ya hay un pago registrado, mostramos y editamos lo que realmente se
  // cobró (monto_recibido) — antes se pre-llenaba con el saldo recalculado,
  // que da $0 apenas está al día y hace perder de vista cuánto se recibió.
  const [monto, setMonto] = useState(String(
    row.pagado ? row.monto_recibido : (row.total_pagar > 0 ? row.total_pagar : 0)
  ));
  const { post, loading } = usePost<object, object>("/api/finanzas/pagos");
  const { post: postUndo, loading: undoing } = usePost<object, object>("/api/finanzas/pagos");

  const handleSave = async () => {
    const montoRecibido = parseFloat(monto) || 0;
    // Si no hay nada que cobrar este período (p. ej. un saldo a favor cubre
    // todo), se permite confirmar con monto 0 — igual hace falta registrar el
    // período para que el crédito se traslade correctamente al mes siguiente.
    if (montoRecibido <= 0 && row.total_pagar > 0) { toast.error("El monto debe ser mayor a cero"); return; }
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

  const handleUndo = async () => {
    const res = await postUndo({
      unidad_id: row.unidad_id,
      periodo: PERIODO,
      pagado: 0,
      monto_recibido: row.monto_recibido,
      saldo_inicial: row.saldo_anterior,
      telec: row.telec,
      reserva: row.reserva,
      redondeo: row.redondeo,
      imp_mes_override: row.imp_mes > 0 ? row.imp_mes : undefined,
    });
    if (res) {
      toast.success(`Se desmarcó el pago de ${row.nombre}`);
      onSaved(); onClose();
    } else {
      toast.error("Error al desmarcar el pago");
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="bg-surface border-border text-text">
        <DialogHeader><DialogTitle className="text-text">Registrar Pago</DialogTitle></DialogHeader>
        <div className="flex items-center gap-3 py-2">
          <Avatar nombre={row.nombre} />
          <div>
            <p className="text-sm font-semibold text-text">{row.nombre}</p>
            <p className="text-xs text-text2">Unidad {row.unidad}</p>
          </div>
        </div>
        {row.pagado && (
          <div className="rounded-lg px-3 py-2 text-xs bg-success-subtle text-success">
            Ya registrado como pagado — se recibieron {fmtCurrency(row.monto_recibido)}.
          </div>
        )}
        {!row.pagado && row.total_pagar < -0.01 && (
          <div className="rounded-lg px-3 py-2 text-xs bg-success-subtle text-success">
            Esta unidad tiene un saldo a favor de {fmtCurrency(-row.total_pagar)}, que ya se descontó de este período.
          </div>
        )}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-text2">Monto recibido</label>
          <Input type="number" value={monto} onChange={(e) => setMonto(e.target.value)} className="bg-surface2 border-border text-text" />
        </div>
        <DialogFooter>
          {row.pagado && (
            <Button variant="ghost" onClick={handleUndo} disabled={undoing} className="text-warning gap-1.5">
              <RotateCcw size={13} />{undoing ? "Desmarcando..." : "Desmarcar como pagado"}
            </Button>
          )}
          <Button variant="ghost" onClick={onClose} className="text-text2">Cancelar</Button>
          <Button onClick={handleSave} disabled={loading} className="bg-accent text-white">
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
  const [sendingMail, setSendingMail] = useState<Set<number>>(new Set());
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const [marcando, setMarcando] = useState(false);
  const { data, loading, connecting, refetch } = useGet<PagosResumen>("/api/finanzas/pagos", CONSORCIO ? { consorcio: CONSORCIO, periodo: PERIODO } : null);

  // Si se cambia de período/consorcio con unidades tildadas, la selección
  // queda referida al contexto viejo — al confirmar aplicaría la acción
  // masiva al período/consorcio equivocado sin que el usuario lo note.
  useEffect(() => { setChecked(new Set()); }, [CONSORCIO, PERIODO]);

  const toggleCheck = (uid: number) => setChecked((prev) => {
    const next = new Set(prev);
    next.has(uid) ? next.delete(uid) : next.add(uid);
    return next;
  });

  const handleExportCsv = () => {
    const csvCell = (v: string | number) => {
      const s = String(v);
      return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const header = ["Unidad", "Propietario", "Estado", "Saldo anterior", "Expensas del mes", "Total a pagar"];
    const lines = [header.map(csvCell).join(";")];
    for (const row of rows) {
      lines.push([
        row.unidad, row.nombre,
        row.pagado ? "Al día" : row.en_mora ? "En mora" : "Pendiente",
        row.saldo_anterior, row.imp_mes, row.total_pagar,
      ].map(csvCell).join(";"));
    }
    const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `estado_pagos_${PERIODO}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleBatchMarcar = async () => {
    if (checked.size === 0) return;
    setMarcando(true);
    try {
      const res = await api.post<{ message: string }>("/api/finanzas/pagos/batch_marcar", {
        consorcio_id: CONSORCIO, periodo: PERIODO, unidad_ids: Array.from(checked),
      });
      toast.success(res.data.message);
      setChecked(new Set());
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al marcar los pagos");
    } finally {
      setMarcando(false);
    }
  };

  const handleEnviarBoleta = async (row: PagoUnitRow) => {
    setSendingMail((prev) => new Set(prev).add(row.unidad_id));
    try {
      await api.post(`/api/reportes/boleta/${row.unidad_id}/${PERIODO}/enviar`);
      toast.success(`Boleta enviada a ${row.email}`);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al enviar boleta");
    } finally {
      setSendingMail((prev) => { const s = new Set(prev); s.delete(row.unidad_id); return s; });
    }
  };
  const rows = (data?.unidades ?? []).filter((r) => {
    if (filtro === "mora") return r.en_mora;
    if (filtro === "aldia") return r.pagado;
    return true;
  });
  const FiltroBtn = ({ id, label }: { id: Filtro; label: string }) => (
    <button
      onClick={() => setFiltro(id)}
      className={cn(
        "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border",
        filtro === id
          ? "bg-accent-ghost text-accent border-accent/40"
          : "bg-surface2 text-text2 border-border hover:bg-white/10 hover:border-white/20"
      )}
    >
      {label}
    </button>
  );
  if (connecting) return <ConnectingState />;
  if (loading) return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        {[0,1,2].map((i) => <Skeleton key={i} className="h-28 rounded-xl bg-surface" />)}
      </div>
      <Skeleton className="h-96 rounded-xl bg-surface" />
    </div>
  );
  const kpis = [
    { label: "Unidades en Mora", value: String(data?.kpi_mora ?? 0), icon: <AlertTriangle size={16} className="text-danger" />, color: "text-danger" },
    { label: "Recaudacion Mensual", value: fmtCurrency(data?.kpi_recaudado ?? 0), icon: <TrendingUp size={16} className="text-success" />, color: "text-success" },
    { label: "Deuda Pendiente Total", value: fmtCurrency(data?.kpi_total_deuda ?? 0), icon: <DollarSign size={16} className="text-warning" />, color: "text-warning" },
  ];
  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-3 gap-4">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-xl p-4 border shadow-card flex items-center gap-4 bg-surface border-border">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 bg-white/5">{k.icon}</div>
            <div>
              <p className="text-xs text-text2">{k.label}</p>
              <p className={cn("text-xl font-bold", k.color)}>{k.value}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-xl border shadow-card overflow-hidden bg-surface border-border">
        <div className="flex items-center justify-between px-5 py-3 border-b bg-surface2 border-border">
          <div className="flex items-center gap-2"><CheckCircle2 size={15} className="text-accent" />
            <span className="text-sm font-medium text-text">Periodo {PERIODO} - {(data?.unidades ?? []).length} unidades</span>
          </div>
          <div className="flex items-center gap-2">
            {checked.size > 0 && (
              <Button size="sm" onClick={handleBatchMarcar} disabled={marcando} className="h-7 px-3 text-xs gap-1 bg-accent text-white">
                <CheckCircle2 size={12} />{marcando ? "Marcando..." : `Marcar ${checked.size} como pagadas`}
              </Button>
            )}
            <FiltroBtn id="todos" label="Todos" /><FiltroBtn id="mora" label="En Mora" /><FiltroBtn id="aldia" label="Al dia" />
            <Button size="sm" onClick={handleExportCsv} variant="soft" className="h-7 px-3 text-xs gap-1 ml-1"><FileSpreadsheet size={12} />Exportar CSV</Button>
            <Button size="sm" onClick={() => { toast.promise(openPdf(`/api/reportes/general/${CONSORCIO}/${PERIODO}`), { loading: "Generando PDF...", success: "PDF abierto", error: (e: unknown) => e instanceof Error ? e.message : "Error al generar PDF" }); }} variant="soft" className="h-7 px-3 text-xs gap-1"><FileText size={12} />PDF General</Button>
          </div>
        </div>
        <Table>
          <TableHeader><TableRow className="border-border">
            <TableHead className="w-8 bg-surface2" />
            {["UNIDAD","PROPIETARIO","ESTADO","TOTAL A PAGAR","ACCIONES"].map((h) => (
              <TableHead key={h} className="text-xs font-semibold uppercase tracking-wider text-text2 bg-surface2">{h}</TableHead>
            ))}
          </TableRow></TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.unidad_id} className="transition-colors hover:bg-white/[0.02] border-border">
                <TableCell>
                  {!row.pagado && (
                    <input
                      type="checkbox"
                      checked={checked.has(row.unidad_id)}
                      onChange={() => toggleCheck(row.unidad_id)}
                      className="w-4 h-4 accent-accent cursor-pointer"
                    />
                  )}
                </TableCell>
                <TableCell className="font-mono text-sm font-semibold text-text">{row.unidad}</TableCell>
                <TableCell><div className="flex items-center gap-2.5"><Avatar nombre={row.nombre} /><span className="text-sm text-text">{row.nombre}</span></div></TableCell>
                <TableCell>{estadoBadge(row)}</TableCell>
                <TableCell className={cn("font-semibold", row.total_pagar > 0 ? "text-danger" : "text-success")}>
                  {row.total_pagar < -0.01 ? `Saldo a favor: ${fmtCurrency(-row.total_pagar)}` : fmtCurrency(row.total_pagar)}
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button size="sm" variant="soft" onClick={() => setSelected(row)} className="h-7 px-3 text-xs gap-1">
                      <Plus size={12} />Registrar
                    </Button>
                    <Button size="sm" variant="soft-violet" onClick={() => { toast.promise(openPdf(`/api/reportes/boleta/${row.unidad_id}/${PERIODO}`), { loading: "Generando boleta...", success: "Boleta abierta", error: (e: unknown) => e instanceof Error ? e.message : "Error al generar boleta" }); }} className="h-7 px-3 text-xs gap-1">
                      <FileText size={12} />Boleta
                    </Button>
                    {row.email && (
                      <Button
                        size="sm"
                        variant="soft-emerald"
                        onClick={() => handleEnviarBoleta(row)}
                        disabled={sendingMail.has(row.unidad_id)}
                        className="h-7 px-3 text-xs gap-1"
                        title={`Enviar boleta a ${row.email}`}
                      >
                        <Mail size={12} />{sendingMail.has(row.unidad_id) ? "Enviando..." : "Enviar"}
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {selected && <RegistrarDialog row={selected} onClose={() => setSelected(null)} onSaved={refetch} />}
    </div>
  );
}

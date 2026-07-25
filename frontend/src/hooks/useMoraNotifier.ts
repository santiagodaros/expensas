import { useEffect, useRef } from "react";
import api from "@/lib/api";
import { fmtCurrency } from "@/lib/utils";
import { useApp } from "@/contexts/AppContext";

interface DashboardKpi {
  pendientes: number;
  v_deuda: number;
}

/**
 * Notificación nativa (Web Notification API, soportada por WebView2 sin
 * plugins de Tauri) avisando si hay unidades en mora del período actual.
 * Se dispara una sola vez por combinación consorcio+período en la sesión,
 * para no repetir el aviso cada vez que se navega al Dashboard.
 */
export function useMoraNotifier() {
  const { consorcioId, consorcioNombre, periodo } = useApp();
  const notificados = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!consorcioId) return;
    const key = `${consorcioId}:${periodo}`;
    if (notificados.current.has(key)) return;

    let cancelled = false;
    api.get<{ kpi: DashboardKpi }>("/api/dashboard", { params: { consorcio: consorcioId, periodo } })
      .then(async (res) => {
        if (cancelled) return;
        const { pendientes, v_deuda } = res.data.kpi;
        if (pendientes <= 0) return;
        notificados.current.add(key);

        if (typeof Notification === "undefined") return;
        let permission = Notification.permission;
        if (permission === "default") permission = await Notification.requestPermission();
        if (permission !== "granted") return;

        const n = new Notification(`${consorcioNombre}: ${pendientes} unidad${pendientes === 1 ? "" : "es"} en mora`, {
          body: `Período ${periodo} — deuda pendiente total: ${fmtCurrency(v_deuda)}`,
        });
        n.onclick = () => window.focus();
      })
      .catch(() => {});

    return () => { cancelled = true; };
  }, [consorcioId, consorcioNombre, periodo]);
}

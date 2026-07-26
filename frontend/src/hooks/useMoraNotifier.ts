import { useEffect, useRef } from "react";
import { isPermissionGranted, requestPermission, sendNotification } from "@tauri-apps/plugin-notification";
import api from "@/lib/api";
import { fmtCurrency } from "@/lib/utils";
import { useApp } from "@/contexts/AppContext";

interface DashboardKpi {
  pendientes: number;
  v_deuda: number;
}

/**
 * Notificación nativa del sistema operativo (plugin de notificaciones de
 * Tauri, se integra con el Centro de Actividades de Windows) avisando si hay
 * unidades en mora del período actual. La Web Notification API del navegador
 * NO sirve acá: WebView2 deniega el permiso en silencio sin mostrar ningún
 * diálogo, así que la notificación nunca llegaba a aparecer.
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

        let granted = await isPermissionGranted();
        if (!granted) granted = (await requestPermission()) === "granted";
        if (!granted) return;

        sendNotification({
          title: `${consorcioNombre}: ${pendientes} unidad${pendientes === 1 ? "" : "es"} en mora`,
          body: `Período ${periodo} — deuda pendiente total: ${fmtCurrency(v_deuda)}`,
        });
      })
      .catch(() => {});

    return () => { cancelled = true; };
  }, [consorcioId, consorcioNombre, periodo]);
}

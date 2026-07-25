import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { useMoraNotifier } from "@/hooks/useMoraNotifier";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/":            { title: "Dashboard", subtitle: "Resumen general del consorcio" },
  "/consorcios":  { title: "Consorcios", subtitle: "Administración de propiedades" },
  "/gastos":      { title: "Carga de Gastos", subtitle: "Registro de comprobantes del período" },
  "/pagos":       { title: "Estado de Pagos", subtitle: "Cobranza y seguimiento de unidades" },
  "/proveedores": { title: "Proveedores", subtitle: "ABM de proveedores del consorcio" },
  "/sueldos":     { title: "Sueldos", subtitle: "Recibos de sueldos y cargas sociales" },
  "/config":      { title: "Configuración", subtitle: "Ajustes del sistema" },
};

export function AppLayout() {
  const { pathname } = useLocation();
  const meta = PAGE_TITLES[pathname] ?? { title: "Gestor", subtitle: "" };
  useMoraNotifier();

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { getVersion } from "@tauri-apps/api/app";
import {
  LayoutDashboard,
  Building2,
  Receipt,
  CreditCard,
  Settings,
  ChevronRight,
  ChevronDown,
  Truck,
  Wallet,
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { useApp } from "@/contexts/AppContext";

const NAV_ITEMS = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/consorcios", icon: Building2, label: "Consorcios" },
  { to: "/gastos", icon: Receipt, label: "Gastos" },
  { to: "/pagos", icon: CreditCard, label: "Pagos" },
  { to: "/proveedores", icon: Truck, label: "Proveedores" },
  { to: "/sueldos", icon: Wallet, label: "Sueldos" },
  { to: "/config", icon: Settings, label: "Configuracion" },
];

interface ConsorcioItem { id: number; nombre: string; }

export function Sidebar() {
  const { consorcioId, consorcioNombre, periodo, setConsorcio, setPeriodo } = useApp();
  const [consorcios, setConsorcios] = useState<ConsorcioItem[]>([]);
  const [showCons, setShowCons] = useState(false);
  const [loadingCons, setLoadingCons] = useState(false);
  const [appVersion, setAppVersion] = useState("");

  useEffect(() => {
    getVersion().then(setAppVersion);
  }, []);

  const fetchConsorcios = async () => {
    setLoadingCons(true);
    try {
      const res = await api.get<ConsorcioItem[]>("/api/consorcios");
      setConsorcios(res.data);
      if (res.data.length > 0 && consorcioId === 0) {
        setConsorcio(res.data[0].id, res.data[0].nombre);
      }
    } catch { /* sin internet o backend no listo */ }
    finally { setLoadingCons(false); }
  };

  useEffect(() => { fetchConsorcios(); }, []);

  const periodoLabel = periodo
    ? new Date(periodo + "-02").toLocaleDateString("es-AR", { month: "long", year: "numeric" })
    : "";

  const adjMonth = (delta: number) => {
    const [y, m] = periodo.split("-").map(Number);
    const d = new Date(y, m - 1 + delta, 1);
    setPeriodo(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };

  return (
    <aside className="flex flex-col w-60 min-h-screen shrink-0 bg-surface border-r border-border shadow-[4px_0_16px_rgba(0,0,0,0.3)]">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 h-16 shrink-0 border-b border-border">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold bg-accent">GC</div>
        <div>
          <p className="text-sm font-semibold leading-tight text-text">Gestor</p>
          <p className="text-xs leading-tight text-text2">Consorcios</p>
        </div>
      </div>

      {/* Selectors */}
      <div className="px-3 py-3 flex flex-col gap-2 border-b border-border">
        {/* Consorcio selector */}
        <div className="relative">
          <button
            onClick={() => { if (!showCons) fetchConsorcios(); setShowCons(!showCons); }}
            className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-xs transition-colors hover:bg-white/5 bg-surface2 border border-border text-text"
          >
            <div className="flex items-center gap-2 min-w-0">
              <Building2 size={13} className="text-accent shrink-0" />
              <span className="truncate font-medium">{consorcioNombre || "Seleccionar..."}</span>
            </div>
            <ChevronDown size={12} className="text-text2 shrink-0" />
          </button>
          {showCons && (
            <>
            <div className="fixed inset-0 z-40" onClick={() => setShowCons(false)} />
            <div className="absolute left-0 right-0 top-full mt-1 rounded-lg z-50 overflow-hidden bg-surface2 border border-border shadow-dialog">
              {loadingCons ? (
                <p className="px-3 py-2 text-xs text-text2">Cargando...</p>
              ) : consorcios.map((c) => (
                <button
                  key={c.id}
                  onClick={() => { setConsorcio(c.id, c.nombre); setShowCons(false); }}
                  className={cn(
                    "w-full text-left px-3 py-2 text-xs transition-colors hover:bg-white/5",
                    c.id === consorcioId ? "text-accent bg-accent-subtle" : "text-text"
                  )}
                >
                  {c.nombre}
                </button>
              ))}
            </div>
            </>
          )}
        </div>

        {/* Periodo selector */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => adjMonth(-1)}
            className="w-6 h-7 rounded flex items-center justify-center text-xs transition-colors hover:bg-white/10 text-text2 border border-border"
          >&#8249;</button>
          <div className="flex-1 text-center py-1.5 rounded text-xs font-medium capitalize bg-surface2 border border-border text-text">
            {periodoLabel}
          </div>
          <button
            onClick={() => adjMonth(1)}
            className="w-6 h-7 rounded flex items-center justify-center text-xs transition-colors hover:bg-white/10 text-text2 border border-border"
          >&#8250;</button>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 flex flex-col gap-1">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group",
                isActive ? "text-text bg-accent-subtle" : "text-text2 hover:bg-white/5"
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full transition-all duration-200 bg-accent" />}
                <Icon size={17} className={cn("shrink-0", isActive ? "text-accent" : "text-text2")} />
                <span className="flex-1">{label}</span>
                {isActive && <ChevronRight size={14} className="text-accent" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 text-xs text-text2 border-t border-border">
        {appVersion ? `v${appVersion}` : ""}
      </div>
    </aside>
  );
}

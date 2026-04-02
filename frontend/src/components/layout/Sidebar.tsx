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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useApp } from "@/contexts/AppContext";

const API_BASE = "http://localhost:8000";

const NAV_ITEMS = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/consorcios", icon: Building2, label: "Consorcios" },
  { to: "/gastos", icon: Receipt, label: "Gastos" },
  { to: "/pagos", icon: CreditCard, label: "Pagos" },
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
      const r = await fetch(`${API_BASE}/api/consorcios`);
      const data: ConsorcioItem[] = await r.json();
      setConsorcios(data);
      if (data.length > 0 && consorcioId === 0) {
        setConsorcio(data[0].id, data[0].nombre);
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
    <aside
      className="flex flex-col w-60 min-h-screen shrink-0"
      style={{ backgroundColor: "var(--color-surface)", borderRight: "1px solid var(--color-border)", boxShadow: "4px 0 16px rgba(0,0,0,0.3)" }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 h-16 shrink-0" style={{ borderBottom: "1px solid var(--color-border)" }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{ backgroundColor: "var(--color-accent)" }}>GC</div>
        <div>
          <p className="text-sm font-semibold leading-tight" style={{ color: "var(--color-text)" }}>Gestor</p>
          <p className="text-xs leading-tight" style={{ color: "var(--color-text2)" }}>Consorcios</p>
        </div>
      </div>

      {/* Selectors */}
      <div className="px-3 py-3 flex flex-col gap-2" style={{ borderBottom: "1px solid var(--color-border)" }}>
        {/* Consorcio selector */}
        <div className="relative">
          <button
            onClick={() => { if (!showCons) fetchConsorcios(); setShowCons(!showCons); }}
            className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-xs transition-colors hover:bg-white/5"
            style={{ backgroundColor: "var(--color-surface2)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <Building2 size={13} style={{ color: "var(--color-accent)", flexShrink: 0 }} />
              <span className="truncate font-medium">{consorcioNombre || "Seleccionar..."}</span>
            </div>
            <ChevronDown size={12} style={{ color: "var(--color-text2)", flexShrink: 0 }} />
          </button>
          {showCons && (
            <>
            <div className="fixed inset-0 z-40" onClick={() => setShowCons(false)} />
            <div
              className="absolute left-0 right-0 top-full mt-1 rounded-lg z-50 overflow-hidden"
              style={{ backgroundColor: "var(--color-surface2)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-dialog)" }}
            >
              {loadingCons ? (
                <p className="px-3 py-2 text-xs" style={{ color: "var(--color-text2)" }}>Cargando...</p>
              ) : consorcios.map((c) => (
                <button
                  key={c.id}
                  onClick={() => { setConsorcio(c.id, c.nombre); setShowCons(false); }}
                  className="w-full text-left px-3 py-2 text-xs transition-colors hover:bg-white/5"
                  style={{ color: c.id === consorcioId ? "var(--color-accent)" : "var(--color-text)", backgroundColor: c.id === consorcioId ? "var(--color-accent-subtle)" : "transparent" }}
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
            className="w-6 h-7 rounded flex items-center justify-center text-xs transition-colors hover:bg-white/10"
            style={{ color: "var(--color-text2)", border: "1px solid var(--color-border)" }}
          >&#8249;</button>
          <div className="flex-1 text-center py-1.5 rounded text-xs font-medium capitalize"
            style={{ backgroundColor: "var(--color-surface2)", border: "1px solid var(--color-border)", color: "var(--color-text)" }}>
            {periodoLabel}
          </div>
          <button
            onClick={() => adjMonth(1)}
            className="w-6 h-7 rounded flex items-center justify-center text-xs transition-colors hover:bg-white/10"
            style={{ color: "var(--color-text2)", border: "1px solid var(--color-border)" }}
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
              cn("relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group", isActive ? "text-white" : "hover:bg-white/5")
            }
            style={({ isActive }) =>
              isActive ? { backgroundColor: "var(--color-accent-subtle)", color: "var(--color-text)" } : { color: "var(--color-text2)" }
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full transition-all duration-200" style={{ backgroundColor: "var(--color-accent)" }} />}
                <Icon size={17} style={{ color: isActive ? "var(--color-accent)" : "var(--color-text2)" }} className="shrink-0" />
                <span className="flex-1">{label}</span>
                {isActive && <ChevronRight size={14} style={{ color: "var(--color-accent)" }} />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 text-xs" style={{ color: "var(--color-text2)", borderTop: "1px solid var(--color-border)" }}>
        {appVersion ? `v${appVersion}` : ""}
      </div>
    </aside>
  );
}

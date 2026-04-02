import { useGet } from "@/hooks/useApi";
import { useApp } from "@/contexts/AppContext";
import { Dashboard as DashboardData } from "@/types/api";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import {
  Building2, TrendingUp, AlertTriangle, DollarSign, Users,
} from "lucide-react";

const fmt = (n: number) =>
  new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(n);

const pct = (n: number) => `${Math.round(n)}%`;

interface KpiCardProps {
  label: string;
  value: string;
  sub?: string;
  icon: React.ReactNode;
  accent?: boolean;
}
function KpiCard({ label, value, sub, icon, accent }: KpiCardProps) {
  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-3 border shadow-card"
      style={{
        backgroundColor: "var(--color-surface)",
        borderColor: "var(--color-border)",
      }}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--color-text2)" }}>
          {label}
        </span>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{
            backgroundColor: accent ? "var(--color-accent-subtle)" : "rgba(255,255,255,0.05)",
          }}
        >
          {icon}
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold" style={{ color: "var(--color-text)" }}>
          {value}
        </p>
        {sub && (
          <p className="text-xs mt-1" style={{ color: "var(--color-text2)" }}>
            {sub}
          </p>
        )}
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg p-3 text-xs border shadow-lg"
      style={{ backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
    >
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {fmt(p.value)}
        </p>
      ))}
    </div>
  );
};

export function DashboardPage() {
  const { consorcioId, periodo } = useApp();
  const { data, loading } = useGet<DashboardData>("/api/dashboard", consorcioId ? { consorcio: consorcioId, periodo } : null);

  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" style={{ backgroundColor: "var(--color-surface)" }} />
          ))}
        </div>
        <Skeleton className="h-64 rounded-xl" style={{ backgroundColor: "var(--color-surface)" }} />
      </div>
    );
  }

  const kpi = data?.kpi;
  const bars = data?.chart ?? [];
  const deudores = data?.deudores ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          label="Total Unidades"
          value={String(kpi?.total_unidades ?? 0)}
          sub="propietarios registrados"
          icon={<Building2 size={16} style={{ color: "var(--color-accent)" }} />}
          accent
        />
        <KpiCard
          label="Recaudacion Mes"
          value={fmt(kpi?.v_recaudado ?? 0)}
          sub={`${pct(kpi?.pct_cobranza ?? 0)} del total`}
          icon={<TrendingUp size={16} style={{ color: "var(--color-success)" }} />}
        />
        <KpiCard
          label="Unidades en Mora"
          value={String(kpi?.pendientes ?? 0)}
          sub="pendientes de pago"
          icon={<AlertTriangle size={16} style={{ color: "var(--color-warning)" }} />}
        />
        <KpiCard
          label="Deuda Pendiente"
          value={fmt(kpi?.v_deuda ?? 0)}
          sub="saldo sin cobrar"
          icon={<DollarSign size={16} style={{ color: "var(--color-danger)" }} />}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div
          className="col-span-2 rounded-xl p-5 border shadow-card"
          style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
        >
          <div className="mb-4">
            <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>
              Ingresos vs Egresos - Ultimos 8 periodos
            </h2>
            <p className="text-xs mt-0.5" style={{ color: "var(--color-text2)" }}>
              Comparativa mensual acumulada
            </p>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={bars} barCategoryGap="30%" barGap={4}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="label" tick={{ fill: "var(--color-text2)", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "var(--color-text2)", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Bar dataKey="ingresos" name="Ingresos" fill="var(--color-accent)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="egresos" name="Egresos" fill="var(--color-danger)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div
          className="rounded-xl p-5 border shadow-card flex flex-col"
          style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}
        >
          <div className="mb-4">
            <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>Top Deudores</h2>
            <p className="text-xs mt-0.5" style={{ color: "var(--color-text2)" }}>Mayor saldo pendiente</p>
          </div>
          <div className="flex flex-col gap-2 flex-1">
            {deudores.length === 0 && (
              <div className="flex items-center justify-center flex-1">
                <div className="flex flex-col items-center gap-2">
                  <Users size={32} style={{ color: "var(--color-border)" }} />
                  <p className="text-xs" style={{ color: "var(--color-text2)" }}>Sin deudores</p>
                </div>
              </div>
            )}
            {deudores.slice(0, 6).map((d, i) => (
              <div key={d.unidad_id} className="flex items-center gap-3 p-2 rounded-lg" style={{ backgroundColor: "var(--color-surface2)" }}>
                <span
                  className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
                  style={{ backgroundColor: i < 3 ? "var(--color-danger)" : "var(--color-border)" }}
                >
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate" style={{ color: "var(--color-text)" }}>{d.nombre}</p>
                  <p className="text-xs" style={{ color: "var(--color-text2)" }}>Unidad {d.unidad}</p>
                </div>
                <span className="text-xs font-semibold shrink-0" style={{ color: "var(--color-danger)" }}>{fmt(d.total_pagar)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

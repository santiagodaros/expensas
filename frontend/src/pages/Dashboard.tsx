import { useGet } from "@/hooks/useApi";
import { useApp } from "@/contexts/AppContext";
import { Dashboard as DashboardData } from "@/types/api";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectingState } from "@/components/ui/connecting-state";
import { fmtCurrency } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import {
  Building2, TrendingUp, AlertTriangle, DollarSign, Users,
} from "lucide-react";

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
    <div className="rounded-xl p-5 flex flex-col gap-3 border shadow-card bg-surface border-border">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-text2">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${accent ? "bg-accent-subtle" : "bg-white/5"}`}>
          {icon}
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold text-text">{value}</p>
        {sub && <p className="text-xs mt-1 text-text2">{sub}</p>}
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg p-3 text-xs border shadow-lg bg-surface2 border-border text-text">
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {fmtCurrency(p.value)}
        </p>
      ))}
    </div>
  );
};

export function DashboardPage() {
  const { consorcioId, periodo } = useApp();
  const { data, loading, connecting } = useGet<DashboardData>("/api/dashboard", consorcioId ? { consorcio: consorcioId, periodo } : null);

  if (connecting) return <ConnectingState />;

  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl bg-surface" />
          ))}
        </div>
        <Skeleton className="h-64 rounded-xl bg-surface" />
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
          icon={<Building2 size={16} className="text-accent" />}
          accent
        />
        <KpiCard
          label="Recaudacion Mes"
          value={fmtCurrency(kpi?.v_recaudado ?? 0)}
          sub={`${pct(kpi?.pct_cobranza ?? 0)} del total`}
          icon={<TrendingUp size={16} className="text-success" />}
        />
        <KpiCard
          label="Unidades en Mora"
          value={String(kpi?.pendientes ?? 0)}
          sub="pendientes de pago"
          icon={<AlertTriangle size={16} className="text-warning" />}
        />
        <KpiCard
          label="Deuda Pendiente"
          value={fmtCurrency(kpi?.v_deuda ?? 0)}
          sub="saldo sin cobrar"
          icon={<DollarSign size={16} className="text-danger" />}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 rounded-xl p-5 border shadow-card bg-surface border-border">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-text">Ingresos vs Egresos - Ultimos 8 periodos</h2>
            <p className="text-xs mt-0.5 text-text2">Comparativa mensual acumulada</p>
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

        <div className="rounded-xl p-5 border shadow-card flex flex-col bg-surface border-border">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-text">Top Deudores</h2>
            <p className="text-xs mt-0.5 text-text2">Mayor saldo pendiente</p>
          </div>
          <div className="flex flex-col gap-2 flex-1">
            {deudores.length === 0 && (
              <div className="flex items-center justify-center flex-1">
                <div className="flex flex-col items-center gap-2">
                  <Users size={32} className="text-border" />
                  <p className="text-xs text-text2">Sin deudores</p>
                </div>
              </div>
            )}
            {deudores.slice(0, 6).map((d, i) => (
              <div key={d.unidad_id} className="flex items-center gap-3 p-2 rounded-lg bg-surface2">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${i < 3 ? "bg-danger" : "bg-border"}`}>
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate text-text">{d.nombre}</p>
                  <p className="text-xs text-text2">Unidad {d.unidad}</p>
                </div>
                <span className="text-xs font-semibold shrink-0 text-danger">{fmtCurrency(d.total_pagar)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

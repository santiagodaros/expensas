import { Search, Bell, ChevronDown } from "lucide-react";
import { Input } from "@/components/ui/input";

interface TopbarProps {
  title: string;
  subtitle?: string;
}

export function Topbar({ title, subtitle }: TopbarProps) {
  return (
    <header
      className="flex items-center justify-between px-6 h-16 shrink-0"
      style={{
        backgroundColor: "var(--color-surface)",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      {/* Left: page title */}
      <div>
        <h1 className="text-base font-semibold leading-tight" style={{ color: "var(--color-text)" }}>
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs" style={{ color: "var(--color-text2)" }}>
            {subtitle}
          </p>
        )}
      </div>

      {/* Right: search + bell + profile */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: "var(--color-text2)" }}
          />
          <Input
            placeholder="Buscar..."
            className="pl-8 h-8 w-48 text-sm"
            style={{
              backgroundColor: "var(--color-surface2)",
              borderColor: "var(--color-border)",
              color: "var(--color-text)",
            }}
          />
        </div>

        <button
          className="relative w-8 h-8 rounded-lg flex items-center justify-center transition-colors hover:bg-white/5"
          style={{ color: "var(--color-text2)" }}
        >
          <Bell size={16} />
        </button>

        <button
          className="flex items-center gap-2 px-2 py-1 rounded-lg transition-colors hover:bg-white/5"
          style={{ color: "var(--color-text2)" }}
        >
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold text-white"
            style={{ backgroundColor: "var(--color-accent)" }}
          >
            A
          </div>
          <span className="text-sm" style={{ color: "var(--color-text)" }}>
            Admin
          </span>
          <ChevronDown size={12} />
        </button>
      </div>
    </header>
  );
}

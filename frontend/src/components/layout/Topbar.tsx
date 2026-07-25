interface TopbarProps {
  title: string;
  subtitle?: string;
}

export function Topbar({ title, subtitle }: TopbarProps) {
  return (
    <header className="flex items-center justify-between px-6 h-16 shrink-0 bg-surface border-b border-border">
      <div>
        <h1 className="text-base font-semibold leading-tight text-text">{title}</h1>
        {subtitle && <p className="text-xs text-text2">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-2 px-2 py-1 text-text2">
        <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold text-white bg-accent">
          A
        </div>
        <span className="text-sm text-text">Admin</span>
      </div>
    </header>
  );
}

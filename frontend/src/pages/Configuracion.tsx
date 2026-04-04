import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Config } from "@/types/api";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, Tag, Eye, EyeOff, Save } from "lucide-react";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium" style={{ color: "var(--color-text2)" }}>{label}</label>
      {children}
    </div>
  );
}

function TInput(props: React.ComponentProps<typeof Input>) {
  return (
    <Input
      {...props}
      style={{
        backgroundColor: "var(--color-surface2)",
        borderColor: "var(--color-border)",
        color: "var(--color-text)",
        ...props.style,
      }}
    />
  );
}

function SectionCard({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)" }}>
      <div className="flex items-center gap-2.5 pb-1 border-b" style={{ borderColor: "var(--color-border)" }}>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: "var(--color-accent-ghost)" }}>
          {icon}
        </div>
        <h3 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

export function ConfiguracionPage() {
  const [form, setForm] = useState({
    nombre_cat_a: "",
    nombre_cat_b: "",
    nombre_cat_c: "",
    smtp_server: "smtp.gmail.com",
    smtp_port: "587",
    smtp_user: "",
    smtp_pass: "",
  });
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get<Config>("/api/config")
      .then((res) => {
        const d = res.data;
        setForm((f) => ({
          ...f,
          nombre_cat_a: d.nombre_cat_a ?? f.nombre_cat_a,
          nombre_cat_b: d.nombre_cat_b ?? f.nombre_cat_b,
          nombre_cat_c: d.nombre_cat_c ?? f.nombre_cat_c,
          smtp_server:  d.smtp_server  ?? f.smtp_server,
          smtp_port:    d.smtp_port    ?? f.smtp_port,
          smtp_user:    d.smtp_user    ?? f.smtp_user,
        }));
      })
      .catch(() => toast.error("Error al cargar configuración"))
      .finally(() => setLoading(false));
  }, []);

  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload: Record<string, string> = {
        nombre_cat_a: form.nombre_cat_a,
        nombre_cat_b: form.nombre_cat_b,
        nombre_cat_c: form.nombre_cat_c,
        smtp_server:  form.smtp_server,
        smtp_port:    form.smtp_port,
        smtp_user:    form.smtp_user,
      };
      if (form.smtp_pass) payload.smtp_pass = form.smtp_pass;
      await api.put("/api/config", payload);
      toast.success("Configuración guardada correctamente");
      setForm((f) => ({ ...f, smtp_pass: "" }));
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <p className="text-sm" style={{ color: "var(--color-text2)" }}>Cargando configuración...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 max-w-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>Configuración</h2>
        <Button
          onClick={handleSave}
          disabled={saving}
          className="h-8 px-4 text-xs gap-1.5"
          style={{ backgroundColor: "var(--color-accent)", color: "white" }}
        >
          <Save size={13} />
          {saving ? "Guardando..." : "Guardar cambios"}
        </Button>
      </div>

      {/* ─── SMTP ────────────────────────────────────────────────────── */}
      <SectionCard icon={<Mail size={14} style={{ color: "var(--color-accent)" }} />} title="Correo Saliente (SMTP)">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Servidor SMTP">
            <TInput value={form.smtp_server} onChange={(e) => set("smtp_server", e.target.value)} placeholder="smtp.gmail.com" />
          </Field>
          <Field label="Puerto">
            <TInput type="number" value={form.smtp_port} onChange={(e) => set("smtp_port", e.target.value)} placeholder="587" />
          </Field>
        </div>
        <Field label="Email remitente">
          <TInput type="email" value={form.smtp_user} onChange={(e) => set("smtp_user", e.target.value)} placeholder="envio.expensas1@gmail.com" />
        </Field>
        <Field label="Contraseña de aplicación">
          <div className="relative">
            <TInput
              type={showPass ? "text" : "password"}
              value={form.smtp_pass}
              onChange={(e) => set("smtp_pass", e.target.value)}
              placeholder="Dejá vacío para no modificar la contraseña guardada"
              style={{ paddingRight: "2.5rem", backgroundColor: "var(--color-surface2)", borderColor: "var(--color-border)", color: "var(--color-text)" }}
            />
            <button
              type="button"
              onClick={() => setShowPass((v) => !v)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100 transition-opacity"
            >
              {showPass ? <EyeOff size={15} style={{ color: "var(--color-text2)" }} /> : <Eye size={15} style={{ color: "var(--color-text2)" }} />}
            </button>
          </div>
          <p className="text-xs mt-0.5" style={{ color: "var(--color-text2)" }}>
            Para Gmail necesitás una <strong style={{ color: "var(--color-text)" }}>Contraseña de Aplicación</strong> (no tu password normal).
            Activá la verificación en dos pasos y generala en Cuenta Google → Seguridad → Contraseñas de aplicaciones.
          </p>
        </Field>
      </SectionCard>

      {/* ─── CATEGORÍAS ──────────────────────────────────────────────── */}
      <SectionCard icon={<Tag size={14} style={{ color: "var(--color-accent)" }} />} title="Nombres de Categorías de Gastos">
        <div className="grid grid-cols-3 gap-4">
          <Field label="Categoría A">
            <TInput value={form.nombre_cat_a} onChange={(e) => set("nombre_cat_a", e.target.value)} placeholder="Gastos Comunes" />
          </Field>
          <Field label="Categoría B">
            <TInput value={form.nombre_cat_b} onChange={(e) => set("nombre_cat_b", e.target.value)} placeholder="Fuerza Motriz" />
          </Field>
          <Field label="Categoría C">
            <TInput value={form.nombre_cat_c} onChange={(e) => set("nombre_cat_c", e.target.value)} placeholder="Locales" />
          </Field>
        </div>
      </SectionCard>
    </div>
  );
}

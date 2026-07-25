import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Config } from "@/types/api";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Field, TInput } from "@/components/ui/form-field";
import { Mail, Tag, Eye, EyeOff, Save, Plug, DatabaseBackup } from "lucide-react";
import { validate } from "@/lib/validate";

function SectionCard({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border p-5 flex flex-col gap-4 bg-surface border-border">
      <div className="flex items-center gap-2.5 pb-1 border-b border-border">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-accent-ghost">
          {icon}
        </div>
        <h3 className="text-sm font-semibold text-text">{title}</h3>
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
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [backingUp, setBackingUp] = useState(false);

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

  const handleTestSmtp = async () => {
    if (!validate([!!form.smtp_user.trim(), "Completá el email remitente antes de probar"])) return;
    setTestingSmtp(true);
    try {
      await api.post("/api/config/test_smtp", {
        smtp_server: form.smtp_server,
        smtp_port: form.smtp_port,
        smtp_user: form.smtp_user,
        smtp_pass: form.smtp_pass || undefined,
      });
      toast.success("Conexión SMTP exitosa");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "No se pudo conectar");
    } finally {
      setTestingSmtp(false);
    }
  };

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

  const handleBackup = async () => {
    setBackingUp(true);
    try {
      const res = await api.post<{ path: string; total_backups: number }>("/api/config/backup");
      toast.success(`Backup creado en ${res.data.path}`, {
        description: `Se conservan los últimos ${res.data.total_backups} backups.`,
      });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al crear el backup");
    } finally {
      setBackingUp(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <p className="text-sm text-text2">Cargando configuración...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 max-w-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text">Configuración</h2>
        <Button onClick={handleSave} disabled={saving} className="h-8 px-4 text-xs gap-1.5 bg-accent text-white">
          <Save size={13} />
          {saving ? "Guardando..." : "Guardar cambios"}
        </Button>
      </div>

      {/* ─── SMTP ────────────────────────────────────────────────────── */}
      <SectionCard icon={<Mail size={14} className="text-accent" />} title="Correo Saliente (SMTP)">
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
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPass((v) => !v)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100 transition-opacity"
            >
              {showPass ? <EyeOff size={15} className="text-text2" /> : <Eye size={15} className="text-text2" />}
            </button>
          </div>
          <p className="text-xs mt-0.5 text-text2">
            Para Gmail necesitás una <strong className="text-text">Contraseña de Aplicación</strong> (no tu password normal).
            Activá la verificación en dos pasos y generala en Cuenta Google → Seguridad → Contraseñas de aplicaciones.
          </p>
        </Field>
        <Button
          onClick={handleTestSmtp}
          disabled={testingSmtp}
          variant="soft"
          className="h-8 px-4 text-xs gap-1.5 w-fit"
        >
          <Plug size={13} />
          {testingSmtp ? "Probando..." : "Probar conexión"}
        </Button>
      </SectionCard>

      {/* ─── CATEGORÍAS ──────────────────────────────────────────────── */}
      <SectionCard icon={<Tag size={14} className="text-accent" />} title="Nombres de Categorías de Gastos">
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

      {/* ─── BACKUP ──────────────────────────────────────────────────── */}
      <SectionCard icon={<DatabaseBackup size={14} className="text-accent" />} title="Respaldo de la Base de Datos">
        <p className="text-xs text-text2">
          La app crea un backup automático cada vez que arranca. Usá este botón para forzar uno ahora mismo
          (por ejemplo, antes de una importación grande o un cambio importante).
        </p>
        <Button onClick={handleBackup} disabled={backingUp} variant="soft" className="h-8 px-4 text-xs gap-1.5 w-fit">
          <DatabaseBackup size={13} />
          {backingUp ? "Creando backup..." : "Backup ahora"}
        </Button>
      </SectionCard>
    </div>
  );
}

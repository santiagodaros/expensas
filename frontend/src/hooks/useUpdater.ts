import { useEffect } from "react";
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";
import { toast } from "sonner";

export function useUpdater() {
  useEffect(() => {
    checkForUpdates();
  }, []);
}

async function checkForUpdates() {
  try {
    const update = await check();
    if (!update?.available) return;

    toast.info(`Nueva versión disponible: v${update.version}`, {
      description: update.body ?? "Actualizá para obtener las últimas mejoras.",
      duration: Infinity,
      action: {
        label: "Instalar",
        onClick: () => installUpdate(update),
      },
    });
  } catch {
    // Sin internet o endpoint no disponible — falla silenciosamente
  }
}

async function installUpdate(update: Awaited<ReturnType<typeof check>>) {
  if (!update) return;

  let downloaded = 0;
  let total = 0;
  const toastId = "updater";

  try {
    toast.loading("Descargando actualización...", { id: toastId });

    await update.downloadAndInstall((event) => {
      if (event.event === "Started") {
        total = event.data.contentLength ?? 0;
      } else if (event.event === "Progress") {
        downloaded += event.data.chunkLength;
        if (total > 0) {
          const pct = Math.round((downloaded / total) * 100);
          toast.loading(`Descargando... ${pct}%`, { id: toastId });
        }
      } else if (event.event === "Finished") {
        toast.success("Actualización lista. Reiniciando...", { id: toastId });
        await relaunch();
      }
    });
  } catch {
    toast.error("Error al instalar la actualización.", { id: toastId });
  }
}

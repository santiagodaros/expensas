import { Loader2 } from "lucide-react";

/**
 * useGet reintenta en silencio contra el backend (hasta 10 veces, cada 2s) antes
 * de mostrar un error. Sin este aviso, la UI se ve como "sin datos" durante ese
 * lapso en vez de "conectando", lo cual es enganoso en el arranque en frio de Tauri.
 */
export function ConnectingState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-text2">
      <Loader2 size={24} className="animate-spin text-accent" />
      <p className="text-sm">Conectando con el servidor...</p>
    </div>
  );
}

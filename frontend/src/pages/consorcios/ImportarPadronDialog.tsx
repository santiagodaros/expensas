import { useState, useCallback } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { UnidadCreate, UnidadBatchOut } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { UploadCloud } from "lucide-react";
import { useDropzone } from "react-dropzone";
import Papa from "papaparse";
import { cn } from "@/lib/utils";
import { parseRows } from "./padronImport";

export function ImportarPadronDialog({
  consorcioId,
  onClose,
  onSaved,
}: {
  consorcioId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [parsed, setParsed] = useState<UnidadCreate[] | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [coefSum, setCoefSum] = useState<number>(0);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<UnidadBatchOut | null>(null);

  const processFile = useCallback((file: File) => {
    setFileName(file.name);
    setParsed(null);
    setResult(null);

    const handleRows = (rawRows: Record<string, any>[]) => {
      const units = parseRows(rawRows);
      const sum = units.reduce((acc, u) => acc + u.coef_a, 0);
      setParsed(units);
      setCoefSum(sum);
    };

    if (file.name.toLowerCase().endsWith(".csv")) {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (res) => handleRows(res.data as Record<string, any>[]),
      });
    } else {
      const reader = new FileReader();
      // xlsx es una dependencia pesada (parser de formato binario de Excel) que
      // solo hace falta para este caso puntual: se carga bajo demanda en vez de
      // ir en el bundle principal de la app de escritorio.
      reader.onload = async (e) => {
        const XLSX = await import("xlsx");
        const wb = XLSX.read(e.target?.result, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json<Record<string, any>>(ws, { defval: "" });
        handleRows(rows);
      };
      reader.readAsArrayBuffer(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxFiles: 1,
    onDrop: (accepted) => { if (accepted[0]) processFile(accepted[0]); },
  });

  // Validación: la suma debe ser ≈ 100 (base porcentaje)
  const coefOk = parsed && parsed.length > 0 && Math.abs(coefSum - 100) < 2;
  const coefWarning = parsed && parsed.length > 0 && !coefOk;

  const handleImport = async () => {
    if (!parsed || parsed.length === 0) return;
    setImporting(true);
    try {
      const res = await api.post(`/api/consorcios/${consorcioId}/unidades/batch`, { unidades: parsed });
      const data = res.data as UnidadBatchOut;
      setResult(data);
      toast.success(data.message);
      onSaved();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al importar");
    } finally {
      setImporting(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="bg-surface border-border text-text max-w-[480px] sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="text-text">Importar UF</DialogTitle>
        </DialogHeader>

        <div
          {...getRootProps()}
          className={cn(
            "rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors",
            isDragActive ? "border-accent bg-accent/5" : "border-border bg-surface2"
          )}
        >
          <input {...getInputProps()} />
          <UploadCloud size={32} className="mx-auto mb-3 text-text2" />
          {fileName ? (
            <p className="text-sm font-medium text-text">{fileName}</p>
          ) : (
            <>
              <p className="text-sm text-text">
                {isDragActive ? "Soltá el archivo acá" : "Arrastrá o hacé click para seleccionar"}
              </p>
              <p className="text-xs mt-1 text-text2">Soporta .csv y .xlsx</p>
            </>
          )}
        </div>

        {parsed && (
          <div className="flex flex-col gap-2 text-xs">
            <div className="flex items-center justify-between px-1">
              <span className="text-text2">{parsed.length} unidades detectadas</span>
              <span className={coefOk ? "text-[#22c55e]" : "text-danger"}>
                Suma Coef A = {coefSum.toFixed(2)}% {coefOk ? "✓" : "⚠"}
              </span>
            </div>
            {coefWarning && (
              <div className="rounded-lg px-3 py-2 text-xs bg-yellow-500/10 text-yellow-600 border border-yellow-500/30">
                La suma de coeficientes A es {coefSum.toFixed(2)}%, debería ser 100%. Podés continuar igual, pero revisá el archivo.
              </div>
            )}
          </div>
        )}

        {result && (
          <div className="rounded-lg px-3 py-2 text-xs bg-green-500/10 text-green-600 border border-green-500/30">
            {result.insertados} insertadas · {result.actualizados} actualizadas · {result.sin_cambios} sin cambios
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className="text-text2">
            {result ? "Cerrar" : "Cancelar"}
          </Button>
          {!result && (
            <Button
              onClick={handleImport}
              disabled={!parsed || parsed.length === 0 || importing}
              variant="soft"
            >
              {importing ? "Importando..." : `Importar ${parsed?.length ?? 0} unidades`}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

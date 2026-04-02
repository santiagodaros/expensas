import { AppProvider } from "@/contexts/AppContext";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/Dashboard";
import { EstadoPagosPage } from "@/pages/EstadoPagos";
import { CargaGastosPage } from "@/pages/CargaGastos";
import { ConsorciosPage } from "@/pages/Consorcios";
import { useUpdater } from "@/hooks/useUpdater";

function Placeholder({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-64">
      <p className="text-sm" style={{ color: "var(--color-text2)" }}>{title} - Proximamente</p>
    </div>
  );
}

export default function App() {
  useUpdater();

  return (
    <AppProvider>
      <Toaster position="bottom-right" richColors theme="dark" />
      <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="consorcios" element={<ConsorciosPage />} />
          <Route path="gastos" element={<CargaGastosPage />} />
          <Route path="pagos" element={<EstadoPagosPage />} />
          <Route path="config" element={<Placeholder title="Configuracion" />} />
        </Route>
      </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}

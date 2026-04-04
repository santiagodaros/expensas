import { AppProvider } from "@/contexts/AppContext";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/Dashboard";
import { EstadoPagosPage } from "@/pages/EstadoPagos";
import { CargaGastosPage } from "@/pages/CargaGastos";
import { ConsorciosPage } from "@/pages/Consorcios";
import { ConfiguracionPage } from "@/pages/Configuracion";
import { ProveedoresPage } from "@/pages/Proveedores";
import { SueldosPage } from "@/pages/Sueldos";
import { useUpdater } from "@/hooks/useUpdater";

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
          <Route path="config" element={<ConfiguracionPage />} />
          <Route path="proveedores" element={<ProveedoresPage />} />
          <Route path="sueldos" element={<SueldosPage />} />
        </Route>
      </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}

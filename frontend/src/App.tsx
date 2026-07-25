import { lazy, Suspense } from "react";
import { AppProvider } from "@/contexts/AppContext";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AppLayout } from "@/components/layout/AppLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { useUpdater } from "@/hooks/useUpdater";

const DashboardPage = lazy(() => import("@/pages/Dashboard").then((m) => ({ default: m.DashboardPage })));
const EstadoPagosPage = lazy(() => import("@/pages/EstadoPagos").then((m) => ({ default: m.EstadoPagosPage })));
const CargaGastosPage = lazy(() => import("@/pages/CargaGastos").then((m) => ({ default: m.CargaGastosPage })));
const ConsorciosPage = lazy(() => import("@/pages/Consorcios").then((m) => ({ default: m.ConsorciosPage })));
const ConfiguracionPage = lazy(() => import("@/pages/Configuracion").then((m) => ({ default: m.ConfiguracionPage })));
const ProveedoresPage = lazy(() => import("@/pages/Proveedores").then((m) => ({ default: m.ProveedoresPage })));
const SueldosPage = lazy(() => import("@/pages/Sueldos").then((m) => ({ default: m.SueldosPage })));

function PageFallback() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-28 rounded-xl bg-surface" />
      <Skeleton className="h-96 rounded-xl bg-surface" />
    </div>
  );
}

export default function App() {
  useUpdater();

  return (
    <ErrorBoundary>
      <AppProvider>
        <Toaster position="bottom-right" richColors theme="dark" />
        <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Suspense fallback={<PageFallback />}><DashboardPage /></Suspense>} />
            <Route path="consorcios" element={<Suspense fallback={<PageFallback />}><ConsorciosPage /></Suspense>} />
            <Route path="gastos" element={<Suspense fallback={<PageFallback />}><CargaGastosPage /></Suspense>} />
            <Route path="pagos" element={<Suspense fallback={<PageFallback />}><EstadoPagosPage /></Suspense>} />
            <Route path="config" element={<Suspense fallback={<PageFallback />}><ConfiguracionPage /></Suspense>} />
            <Route path="proveedores" element={<Suspense fallback={<PageFallback />}><ProveedoresPage /></Suspense>} />
            <Route path="sueldos" element={<Suspense fallback={<PageFallback />}><SueldosPage /></Suspense>} />
          </Route>
        </Routes>
        </BrowserRouter>
      </AppProvider>
    </ErrorBoundary>
  );
}

import { Component, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Sin esto, un error de render en cualquier pagina tira toda la app a blanco
 * (pantalla en negro sobre Tauri, sin forma de recuperarse salvo reiniciar).
 * Los error boundaries de React solo pueden implementarse como class component.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-screen w-screen flex-col items-center justify-center gap-4 bg-bg p-6 text-center">
          <AlertTriangle size={40} className="text-danger" />
          <div>
            <p className="text-base font-semibold text-text">Ocurrió un error inesperado</p>
            <p className="mt-1 text-sm text-text2">{this.state.error.message}</p>
          </div>
          <button
            onClick={() => { this.setState({ error: null }); window.location.href = "/"; }}
            className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white"
          >
            Volver al inicio
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

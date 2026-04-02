import { createContext, useContext, useState, ReactNode } from "react";

interface AppState {
  consorcioId: number;
  consorcioNombre: string;
  periodo: string;
  setConsorcio: (id: number, nombre: string) => void;
  setPeriodo: (p: string) => void;
}

const defaultPeriodo = new Date().toISOString().slice(0, 7);

const AppContext = createContext<AppState>({
  consorcioId: 0,
  consorcioNombre: "",
  periodo: defaultPeriodo,
  setConsorcio: () => {},
  setPeriodo: () => {},
});

export function AppProvider({ children }: { children: ReactNode }) {
  const [consorcioId, setConsorcioId] = useState(0);
  const [consorcioNombre, setConsorcioNombre] = useState("");
  const [periodo, setPeriodo] = useState(defaultPeriodo);

  const setConsorcio = (id: number, nombre: string) => {
    setConsorcioId(id);
    setConsorcioNombre(nombre);
  };

  return (
    <AppContext.Provider value={{ consorcioId, consorcioNombre, periodo, setConsorcio, setPeriodo }}>
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => useContext(AppContext);

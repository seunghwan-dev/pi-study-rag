import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

interface AppState {
  isLive: boolean;
  isLoading: boolean;
}

const AppContext = createContext<AppState>({ isLive: false, isLoading: true });

export function useApp() {
  return useContext(AppContext);
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [isLive, setIsLive] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("/health", { signal: AbortSignal.timeout(3000) });
        setIsLive(res.ok);
      } catch {
        // Backend unreachable — DEMO mode
        setIsLive(false);
      } finally {
        setIsLoading(false);
      }
    };
    check();
  }, []);

  return (
    <AppContext.Provider value={{ isLive, isLoading }}>
      {children}
    </AppContext.Provider>
  );
}

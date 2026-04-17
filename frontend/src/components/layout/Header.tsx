import { Sun, Moon, Wifi, WifiOff } from "lucide-react";
import { useApp } from "../../contexts/AppContext";

interface Props {
  darkMode: boolean;
  onToggleDark: () => void;
}

export default function Header({ darkMode, onToggleDark }: Props) {
  const { isLive, isLoading } = useApp();

  return (
    <header className="sticky top-0 z-20 h-14 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 flex items-center justify-end px-5">
      <div className="flex items-center gap-3">
        {/* LIVE / DEMO badge */}
        {!isLoading &&
          (isLive ? (
            <span className="flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs bg-emerald-500/15 text-emerald-600">
              <Wifi className="w-3 h-3" />
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              LIVE
            </span>
          ) : (
            <span className="flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs bg-amber-500/15 text-amber-600">
              <WifiOff className="w-3 h-3" />
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              DEMO
            </span>
          ))}

        {/* Dark mode toggle */}
        <button
          onClick={onToggleDark}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
}

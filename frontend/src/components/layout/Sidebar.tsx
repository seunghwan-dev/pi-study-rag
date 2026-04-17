import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { BookOpen, Search, Bot, PenLine, BarChart3, History } from "lucide-react";
import { useApp } from "../../contexts/AppContext";
import type { ProgressResponse } from "../../types/study";

const NAV = [
  { to: "/", icon: BookOpen, label: "論文を追加", flow: "P1" },
  { to: "/search", icon: Search, label: "ナレッジ検索", flow: "P2" },
  { to: "/survey", icon: Bot, label: "論文サーベイ", flow: "P3" },
  { to: "/quiz", icon: PenLine, label: "クイズモード", flow: "P4" },
  { to: "/dashboard", icon: BarChart3, label: "ダッシュボード", flow: "P5" },
  { to: "/history", icon: History, label: "学習履歴", flow: "P6" },
];

export default function Sidebar() {
  const { isLive, isLoading } = useApp();
  const [stats, setStats] = useState<{ papers: number; chunks: number } | null>(null);

  useEffect(() => {
    if (isLive) {
      fetch("/api/v1/study/progress")
        .then((r) => r.json())
        .then((d: ProgressResponse) =>
          setStats({ papers: d.overview.total_papers, chunks: d.overview.total_chunks })
        )
        .catch(() => {});
    } else if (!isLoading) {
      setStats({ papers: 5, chunks: 463 });
    }
  }, [isLive, isLoading]);

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col z-30">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">📚</span>
          <div>
            <h1 className="text-sm font-semibold tracking-tight">PI Study RAG</h1>
            <p className="text-[10px] text-gray-500 font-mono">
              v0.3 · {isLoading ? "..." : isLive ? "LIVE" : "DEMO"}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label, flow }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 group ${
                isActive
                  ? "bg-blue-100 text-blue-700 dark:bg-blue-600/15 dark:text-blue-400"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-gray-200"
              }`
            }
          >
            <Icon size={18} strokeWidth={1.8} />
            <span className="flex-1 font-medium">{label}</span>
            <span className="text-[10px] font-mono text-gray-400 dark:text-gray-600 group-hover:text-gray-500">
              {flow}
            </span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-200 dark:border-gray-800">
        <p className="text-[10px] text-gray-500 font-mono leading-relaxed">
          Gemma 4 E4B · Oracle 26ai
          <br />
          PyMuPDF + e5-large
          <br />
          {stats ? `${stats.papers} papers · ${stats.chunks} chunks` : "loading..."}
        </p>
      </div>
    </aside>
  );
}

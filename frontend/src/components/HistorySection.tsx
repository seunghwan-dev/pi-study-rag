import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import { mockHistory } from "../mock/mockData";
import type { HistoryItem } from "../types/study";

const MODE_STYLES: Record<string, string> = {
  tutor:    "bg-blue-500/10 text-blue-600",
  socratic: "bg-purple-500/10 text-purple-600",
  quiz:     "bg-emerald-500/10 text-emerald-600",
};

const SCORE_STYLES: Record<string, string> = {
  correct:           "bg-emerald-500/10 text-emerald-600",
  partially_correct: "bg-amber-500/10 text-amber-600",
  incorrect:         "bg-red-500/10 text-red-600",
};

function relativeTime(iso: string | null): string {
  if (!iso) return "";
  // Append "Z" if no timezone info so JS parses as UTC
  const utcIso = iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z";
  const diff = Date.now() - new Date(utcIso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "たった今";
  if (mins < 60) return `${mins}分前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}時間前`;
  const days = Math.floor(hours / 24);
  return `${days}日前`;
}

export default function HistorySection() {
  const { isLive } = useApp();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = () => {
    fetch("/api/v1/study/history?limit=20")
      .then((r) => r.json())
      .then(setItems)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isLive) {
      setItems(mockHistory);
      setLoading(false);
      return;
    }
    fetchHistory();
  }, [isLive]);

  // Refresh on window focus (e.g. returning from another page)
  useEffect(() => {
    const handler = () => { if (isLive) fetchHistory(); };
    window.addEventListener("focus", handler);
    return () => window.removeEventListener("focus", handler);
  }, [isLive]);

  return (
    <section className="animate-[fade-in_0.4s_ease-out]">
      <div className="rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" /> 読み込み中...
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-gray-500">まだ学習履歴がありません。質問を始めましょう！</p>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={item.history_id}
                className="rounded-lg border border-gray-100 dark:border-gray-700 p-3 space-y-1"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${MODE_STYLES[item.study_mode] || "bg-gray-200 text-gray-600"}`}>
                    {item.study_mode}
                  </span>
                  {item.category && (
                    <span className="rounded-full px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                      {item.category}
                    </span>
                  )}
                  {item.quiz_score && (
                    <span className={`rounded-full px-2 py-0.5 text-xs ${SCORE_STYLES[item.quiz_score] || ""}`}>
                      {item.quiz_score}
                    </span>
                  )}
                  <span className="text-xs text-gray-400 ml-auto">{relativeTime(item.created_at)}</span>
                </div>
                <p className="text-sm font-medium truncate">{item.question}</p>
                <p className="text-xs text-gray-500 line-clamp-2">{item.answer_preview}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

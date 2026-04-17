import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import { mockProgress } from "../mock/mockData";
import type { ProgressResponse } from "../types/study";

const STATUS_STYLES: Record<string, { dot: string; label: string }> = {
  recent:              { dot: "bg-emerald-500", label: "最近" },
  review_recommended:  { dot: "bg-amber-500",  label: "復習推奨" },
  review_needed:       { dot: "bg-red-500",     label: "復習必要" },
  not_started:         { dot: "bg-gray-400",    label: "未着手" },
};

export default function DashboardSection() {
  const { isLive } = useApp();
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProgress = () => {
    fetch("/api/v1/study/progress")
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isLive) {
      setData(mockProgress);
      setLoading(false);
      return;
    }
    fetchProgress();
  }, [isLive]);

  // Refresh on window focus (e.g. returning from another page)
  useEffect(() => {
    const handler = () => { if (isLive) fetchProgress(); };
    window.addEventListener("focus", handler);
    return () => window.removeEventListener("focus", handler);
  }, [isLive]);

  if (loading) {
    return (
      <section className="animate-[fade-in_0.4s_ease-out]">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" /> 読み込み中...
        </div>
      </section>
    );
  }

  if (!data) return null;

  const { overview, by_category, study_streak, recommendation } = data;
  const activeCats = by_category.filter((c) => c.chunk_count > 0);

  return (
    <section className="animate-[fade-in_0.4s_ease-out]">
      <div className="rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 space-y-5">
        {/* Overview stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="論文数" value={overview.total_papers} />
          <StatCard label="チャンク数" value={overview.total_chunks} />
          <StatCard label="質問数" value={overview.total_questions} />
          <StatCard label="カバー率" value={`${(overview.overall_coverage * 100).toFixed(1)}%`} />
        </div>

        {/* Study streak */}
        <div className="flex gap-4 text-center">
          <div>
            <p className="text-2xl font-bold">{study_streak.today}</p>
            <p className="text-xs text-gray-500">今日</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{study_streak.this_week}</p>
            <p className="text-xs text-gray-500">今週</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{study_streak.this_month}</p>
            <p className="text-xs text-gray-500">今月</p>
          </div>
        </div>

        {/* Category progress */}
        <div className="space-y-2">
          {activeCats.map((cat) => {
            const pct = Math.round(cat.coverage * 100);
            const status = STATUS_STYLES[cat.review_status] || STATUS_STYLES.not_started;
            return (
              <div key={cat.category} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium">{cat.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">
                      {cat.days_since_last !== null ? `${cat.days_since_last}日前` : "-"}
                    </span>
                    <span className={`flex items-center gap-1 rounded-full px-2 py-0.5 ${
                      status.dot === "bg-emerald-500" ? "bg-emerald-500/10 text-emerald-600" :
                      status.dot === "bg-amber-500" ? "bg-amber-500/10 text-amber-600" :
                      status.dot === "bg-red-500" ? "bg-red-500/10 text-red-600" :
                      "bg-gray-200 dark:bg-gray-700 text-gray-500"
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
                      {status.label}
                    </span>
                    <span className="font-mono">{pct}%</span>
                  </div>
                </div>
                <div className="h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Recommendation */}
        {recommendation && (
          <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
            <p className="text-sm font-medium text-amber-700 dark:text-amber-400">{recommendation.message}</p>
            <p className="text-xs text-amber-600 mt-0.5">{recommendation.reason}</p>
          </div>
        )}
      </div>
    </section>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-gray-900 p-3 text-center">
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

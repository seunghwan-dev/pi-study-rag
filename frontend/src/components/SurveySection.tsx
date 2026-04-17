import { useState } from "react";
import { Bot, Loader2, Plus, X, CheckCircle } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import { mockSurveyResult } from "../mock/mockData";
import type { SurveyResponse } from "../types/study";

const EXPECTED_STEPS = [
  "あなたの知識ベースを分析しています...",
  "最近の学習パターンからトレンドを特定しています...",
  "4つの戦略で検索キーワードを生成しています...",
  "arXivで論文を探索しています...",
  "既存知識との接続を分析しています...",
];

export default function SurveySection() {
  const { isLive } = useApp();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SurveyResponse | null>(null);
  const [fakeSteps, setFakeSteps] = useState<string[]>([]);
  const [fetchingId, setFetchingId] = useState<string | null>(null);
  const [skipped, setSkipped] = useState<Set<string>>(new Set());
  const [fetched, setFetched] = useState<Set<string>>(new Set());

  const handleRun = async () => {
    setLoading(true);
    setResult(null);
    setFakeSteps([]);
    setSkipped(new Set());
    setFetched(new Set());

    // Fake streaming steps
    const streamPromise = (async () => {
      for (const step of EXPECTED_STEPS) {
        await new Promise((r) => setTimeout(r, 800));
        setFakeSteps((prev) => [...prev, step]);
      }
    })();

    if (!isLive) {
      await streamPromise;
      await new Promise((r) => setTimeout(r, 500));
      setResult(mockSurveyResult);
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/v1/study/survey");
      if (res.ok) {
        await streamPromise;
        setResult(await res.json());
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const handleFetch = async (_pdfUrl: string, _title: string, arxivId: string) => {
    setFetchingId(arxivId);
    if (!isLive) {
      await new Promise((r) => setTimeout(r, 1000));
      setFetched((prev) => new Set(prev).add(arxivId));
      setFetchingId(null);
      return;
    }
    try {
      const res = await fetch("/api/v1/study/fetch-paper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pdf_url: _pdfUrl, title: _title }),
      });
      if (res.ok) setFetched((prev) => new Set(prev).add(arxivId));
    } catch {
      // silent
    } finally {
      setFetchingId(null);
    }
  };

  // Show fake steps while loading, real monologue once result arrives
  const displaySteps = result ? result.monologue : fakeSteps;

  return (
    <section className="animate-[fade-in_0.4s_ease-out]">
      <div className="rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 space-y-4">
        <button
          onClick={handleRun}
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bot className="w-4 h-4" />}
          {loading ? "エージェント実行中..." : "サーベイ開始"}
        </button>

        {/* Monologue (fake or real) */}
        {displaySteps.length > 0 && (
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 space-y-1">
            {displaySteps.map((line, i) => (
              <p key={i} className="font-mono text-sm text-gray-600 dark:text-gray-400 animate-[fade-in_0.4s_ease-out]">
                {line}
              </p>
            ))}
          </div>
        )}

        {/* Analysis */}
        {result?.analysis && (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2 text-xs">
              {result.analysis.strongest && (
                <span className="rounded-full px-2 py-0.5 bg-emerald-500/10 text-emerald-600">
                  強み: {(result.analysis.strongest as Record<string, unknown>).label as string}
                </span>
              )}
              {result.analysis.weakest && (
                <span className="rounded-full px-2 py-0.5 bg-red-500/10 text-red-600">
                  弱み: {(result.analysis.weakest as Record<string, unknown>).label as string}
                </span>
              )}
              {result.analysis.recent_trend && (
                <span className="rounded-full px-2 py-0.5 bg-purple-500/10 text-purple-600">
                  トレンド: {result.analysis.recent_trend}
                </span>
              )}
            </div>
            {result.analysis.auto_keywords.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {result.analysis.auto_keywords.map((kw, i) => (
                  <span key={i} className="rounded-full px-2 py-0.5 text-xs bg-blue-500/10 text-blue-600">
                    {kw}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Recommendations */}
        {result && result.recommendations.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-semibold text-gray-500">推薦論文 ({result.total_recommended}件)</p>
            {result.recommendations.map((rec) => {
              const id = rec.paper.arxiv_id;
              const done = fetched.has(id);
              const skip = skipped.has(id);
              if (skip) return null;
              return (
                <div
                  key={id}
                  className="rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-3 space-y-2"
                >
                  <p className="text-sm font-medium">{rec.paper.title}</p>
                  <p className="text-xs text-gray-500">
                    {rec.paper.authors.slice(0, 3).join(", ")}
                    <span className="ml-2 rounded-full px-2 py-0.5 bg-blue-500/10 text-blue-600">
                      関連度 {(rec.relevance * 100).toFixed(0)}%
                    </span>
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{rec.connection}</p>
                  {!done ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleFetch(rec.paper.pdf_url, rec.paper.title, id)}
                        disabled={fetchingId === id}
                        className="rounded-lg px-3 py-1 text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
                      >
                        {fetchingId === id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                        追加
                      </button>
                      <button
                        onClick={() => setSkipped((prev) => new Set(prev).add(id))}
                        className="rounded-lg px-3 py-1 text-xs font-medium border border-gray-300 dark:border-gray-600 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-1"
                      >
                        <X className="w-3 h-3" /> スキップ
                      </button>
                    </div>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-emerald-600">
                      <CheckCircle className="w-3 h-3" /> 追加済み
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {result && result.recommendations.length === 0 && (
          <p className="text-sm text-gray-500">サーベイ結果がありません。まず論文を追加してください。</p>
        )}
      </div>
    </section>
  );
}

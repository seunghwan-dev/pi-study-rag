import { useState, useEffect } from "react";
import { Search, Loader2, BookOpen, MessageCircle } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import { mockCategories, mockTutorAnswer, mockSocraticAnswer } from "../mock/mockData";
import MarkdownView from "./MarkdownView";
import type { AskResponse, CategoryItem } from "../types/study";

const EXAMPLE_QUERIES = [
  "Small Data MLの一般的なアプローチは？",
  "Transfer Learningとは？",
  "Digital Twinの最新動向は？",
];

export default function SearchSection() {
  const { isLive } = useApp();
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<"tutor" | "socratic">("tutor");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [highlightedSource, setHighlightedSource] = useState<number | null>(null);

  const handleCitationClick = (n: number) => {
    const el = document.getElementById(`source-${n}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      setHighlightedSource(n);
      setTimeout(() => setHighlightedSource(null), 1500);
    }
  };

  // Load categories
  useEffect(() => {
    if (!isLive) {
      setCategories(mockCategories);
      return;
    }
    fetch("/api/v1/study/categories")
      .then((r) => r.json())
      .then((data: CategoryItem[]) => setCategories(data.filter((c) => c.chunk_count > 0)))
      .catch(() => {});
  }, [isLive]);

  const handleAsk = async (q?: string) => {
    const query = q || question;
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    setShowAnswer(false);
    if (!isLive) {
      await new Promise((r) => setTimeout(r, 1000));
      setResult(mode === "tutor" ? mockTutorAnswer : mockSocraticAnswer);
      setLoading(false);
      return;
    }
    try {
      const res = await fetch("/api/v1/study/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: query,
          mode,
          category_filter: categoryFilter,
        }),
      });
      if (res.ok) setResult(await res.json());
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="animate-[fade-in_0.4s_ease-out]">
      <div className="rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 space-y-4">
        {/* Mode toggle */}
        <div className="flex gap-1">
          {(["tutor", "socratic"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                mode === m
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
              }`}
            >
              {m === "tutor" ? <BookOpen className="w-3.5 h-3.5" /> : <MessageCircle className="w-3.5 h-3.5" />}
              {m === "tutor" ? "Tutor" : "Socratic"}
            </button>
          ))}
        </div>

        {/* Category filter chips */}
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setCategoryFilter(null)}
              className={`rounded-full px-2.5 py-0.5 text-xs transition-colors ${
                categoryFilter === null
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
              }`}
            >
              全カテゴリ
            </button>
            {categories.map((c) => (
              <button
                key={c.category}
                onClick={() => setCategoryFilter(c.category === categoryFilter ? null : c.category)}
                className={`rounded-full px-2.5 py-0.5 text-xs transition-colors ${
                  categoryFilter === c.category
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        )}

        {/* Search input */}
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder="質問を入力..."
            className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={() => handleAsk()}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            検索
          </button>
        </div>

        {/* Example queries */}
        <div className="flex flex-wrap gap-1.5">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => {
                setQuestion(q);
                handleAsk(q);
              }}
              className="rounded-full px-2.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Results */}
        {result && (
          <div className="space-y-3 animate-[fade-in_0.4s_ease-out]">
            {/* Tutor mode answer */}
            {result.has_direct_answer && result.answer && (
              <MarkdownView
                content={result.answer}
                className="text-sm"
                onCitationClick={handleCitationClick}
              />
            )}

            {/* Socratic mode */}
            {!result.has_direct_answer && (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20">
                  <p className="text-xs font-semibold text-amber-600 mb-1">ヒント</p>
                  <MarkdownView
                    content={result.hint || ""}
                    className="text-sm"
                    onCitationClick={handleCitationClick}
                  />
                </div>
                {result.follow_up_question && (
                  <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                    <p className="text-xs font-semibold text-blue-600 mb-1">フォローアップ</p>
                    <p className="text-sm">{result.follow_up_question}</p>
                  </div>
                )}
                <button
                  onClick={() => setShowAnswer((s) => !s)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  {showAnswer ? "答えを隠す" : "答えを見る"}
                </button>
                {showAnswer && result.hint && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">{result.hint}</p>
                )}
              </div>
            )}

            {/* Sources */}
            {result.sources.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">参照元</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.sources.map((s, i) => (
                    <span
                      key={i}
                      id={`source-${i + 1}`}
                      className={`rounded-full px-2 py-0.5 text-xs transition-all duration-300 ${
                        highlightedSource === i + 1
                          ? "bg-blue-500 text-white ring-2 ring-blue-300 scale-105"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                      }`}
                    >
                      {s.doc_title} {s.page_hint} ({((s.similarity ?? 0) * 100).toFixed(0)}%)
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Processing time */}
            <p className="font-mono text-xs text-gray-400">
              {result.processing_time_sec}秒 &middot; {result.mode}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

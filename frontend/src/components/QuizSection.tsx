import { useState, useEffect } from "react";
import { PenLine, Loader2, CheckCircle, XCircle, AlertCircle, RefreshCw } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import { mockCategories, MOCK_QUIZZES, MOCK_EVALUATIONS } from "../mock/mockData";
import MarkdownView from "./MarkdownView";
import type { QuizGenerateResponse, QuizEvaluateResponse, CategoryItem } from "../types/study";

type Phase = "idle" | "question" | "answering" | "result";
type Difficulty = "auto" | "basic" | "intermediate" | "advanced";
type QuizWithAnswer = QuizGenerateResponse & { model_answer?: string };

const DIFFICULTY_OPTIONS: { value: Difficulty; label: string }[] = [
  { value: "auto", label: "お任せ" },
  { value: "basic", label: "基本" },
  { value: "intermediate", label: "中級" },
  { value: "advanced", label: "上級" },
];

const SCORE_STYLES: Record<string, { bg: string; text: string; label: string; icon: typeof CheckCircle }> = {
  correct:           { bg: "bg-emerald-500/10", text: "text-emerald-600", label: "正解", icon: CheckCircle },
  partially_correct: { bg: "bg-amber-500/10",   text: "text-amber-600",  label: "部分正解", icon: AlertCircle },
  incorrect:         { bg: "bg-red-500/10",      text: "text-red-600",    label: "不正解", icon: XCircle },
};

export default function QuizSection() {
  const { isLive } = useApp();
  const [phase, setPhase] = useState<Phase>("idle");
  const [category, setCategory] = useState<string>("");
  const [difficulty, setDifficulty] = useState<Difficulty>("auto");
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [quiz, setQuiz] = useState<QuizWithAnswer | null>(null);
  const [answer, setAnswer] = useState("");
  const [evalResult, setEvalResult] = useState<QuizEvaluateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [quizIndex, setQuizIndex] = useState(0);
  const [showModelAnswer, setShowModelAnswer] = useState(false);

  useEffect(() => {
    if (!isLive) { setCategories(mockCategories); return; }
    fetch("/api/v1/study/categories")
      .then((r) => r.json())
      .then((data: CategoryItem[]) => setCategories(data.filter((c) => c.chunk_count > 0)))
      .catch(() => {});
  }, [isLive]);

  const handleGenerate = async () => {
    setLoading(true);
    setQuiz(null);
    setAnswer("");
    setEvalResult(null);
    setShowModelAnswer(false);
    if (!isLive) {
      await new Promise((r) => setTimeout(r, 1000));
      const next = MOCK_QUIZZES[quizIndex % MOCK_QUIZZES.length];
      setQuiz(next);
      setQuizIndex((i) => i + 1);
      setPhase("question");
      setLoading(false);
      return;
    }
    try {
      const body: Record<string, string> = { difficulty };
      if (category) body.category = category;
      const res = await fetch("/api/v1/study/quiz/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setQuiz(await res.json());
        setPhase("question");
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!quiz || !answer.trim()) return;
    setLoading(true);
    if (!isLive) {
      await new Promise((r) => setTimeout(r, 1000));
      const quizId = quiz?.quiz_id ?? "demo-quiz-001";
      setEvalResult(MOCK_EVALUATIONS[quizId] ?? MOCK_EVALUATIONS["demo-quiz-001"]);
      setPhase("result");
      setLoading(false);
      return;
    }
    try {
      const res = await fetch("/api/v1/study/quiz/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quiz_id: quiz.quiz_id, user_answer: answer }),
      });
      if (res.ok) {
        setEvalResult(await res.json());
        setPhase("result");
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = () => {
    setQuiz(null);
    setAnswer("");
    handleGenerate();
  };

  const handleNext = () => {
    setPhase("idle");
    setQuiz(null);
    setAnswer("");
    setEvalResult(null);
    handleGenerate();
  };

  const handleEnd = () => {
    setPhase("idle");
    setQuiz(null);
    setAnswer("");
    setEvalResult(null);
    setShowModelAnswer(false);
  };

  return (
    <section className="animate-[fade-in_0.4s_ease-out]">
      <div className="rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 space-y-4">
        {/* Idle: category + difficulty + start */}
        {phase === "idle" && (
          <div className="space-y-3">
            <div className="flex gap-2 items-center">
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none"
              >
                <option value="">全カテゴリ</option>
                {categories.map((c) => (
                  <option key={c.category} value={c.category}>{c.label}</option>
                ))}
              </select>
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <PenLine className="w-4 h-4" />}
                クイズ開始
              </button>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-500">難易度:</span>
              {DIFFICULTY_OPTIONS.map((d) => (
                <button
                  key={d.value}
                  onClick={() => setDifficulty(d.value)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    difficulty === d.value
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Question */}
        {(phase === "question" || phase === "answering") && quiz && (
          <div className="space-y-3 animate-[fade-in_0.4s_ease-out]">
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs ${
                quiz.difficulty === "basic" ? "bg-green-500/10 text-green-600" :
                quiz.difficulty === "advanced" ? "bg-red-500/10 text-red-600" :
                "bg-amber-500/10 text-amber-600"
              }`}>
                {quiz.difficulty}
              </span>
              <span className="text-xs text-gray-500">{quiz.source.doc_title} {quiz.source.page_hint}</span>
            </div>
            <p className="text-sm font-medium leading-relaxed">{quiz.question}</p>
            <textarea
              value={answer}
              onChange={(e) => { setAnswer(e.target.value); setPhase("answering"); }}
              placeholder="回答を入力..."
              rows={4}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex gap-2">
              <button
                onClick={handleEvaluate}
                disabled={loading || !answer.trim()}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                回答を提出
              </button>
              <button
                onClick={handleRegenerate}
                disabled={loading}
                className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 flex items-center gap-1"
              >
                <RefreshCw className="w-4 h-4" />
                別の問題
              </button>
              {!isLive && quiz.model_answer && (
                <button
                  type="button"
                  onClick={() => setShowModelAnswer((s) => !s)}
                  className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700 flex items-center gap-1"
                >
                  {showModelAnswer ? "模範解答を隠す" : "模範解答を見る (デモ用)"}
                </button>
              )}
            </div>

            {showModelAnswer && quiz.model_answer && (
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <p className="text-xs font-semibold text-blue-600 mb-1">模範解答 (デモ用)</p>
                <MarkdownView content={quiz.model_answer} className="text-sm" />
              </div>
            )}
          </div>
        )}

        {/* Result */}
        {phase === "result" && evalResult && (
          <div className="space-y-3 animate-[fade-in_0.4s_ease-out]">
            {/* Score badge */}
            {(() => {
              const s = SCORE_STYLES[evalResult.score] || SCORE_STYLES.partially_correct;
              const Icon = s.icon;
              return (
                <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium ${s.bg} ${s.text}`}>
                  <Icon className="w-4 h-4" /> {s.label}
                </span>
              );
            })()}

            <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
              <p className="text-xs font-semibold text-gray-500 mb-1">フィードバック</p>
              <MarkdownView content={typeof evalResult.feedback === "string" ? evalResult.feedback : JSON.stringify(evalResult.feedback)} className="text-sm" />
            </div>

            <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <p className="text-xs font-semibold text-blue-600 mb-1">完全な回答</p>
              <MarkdownView content={typeof evalResult.complete_answer === "string" ? evalResult.complete_answer : JSON.stringify(evalResult.complete_answer)} className="text-sm" />
            </div>

            <p className="font-mono text-xs text-gray-400">出典: {typeof evalResult.source === "string" ? evalResult.source : JSON.stringify(evalResult.source)}</p>

            <div className="flex gap-2">
              <button
                onClick={handleNext}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
              >
                次の質問
              </button>
              <button
                onClick={handleEnd}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                終了
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

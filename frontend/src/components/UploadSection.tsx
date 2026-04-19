import { useState, useRef } from "react";
import { Upload, Search, Plus, CheckCircle, Loader2 } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import {
  mockIngestResult,
  mockArxivSearch,
  mockFetchResult,
  MOCK_ARXIV_RESULTS,
  EXAMPLE_ARXIV_QUERIES,
} from "../mock/mockData";
import type { IngestResponse, PaperSchema, FetchPaperResponse } from "../types/study";

type Tab = "upload" | "arxiv";

export default function UploadSection() {
  const { isLive } = useApp();
  const [tab, setTab] = useState<Tab>("upload");

  return (
    <section className="animate-[fade-in_0.4s_ease-out]">
      {/* Tabs */}
      <div className="flex gap-1 mb-4">
        {(["upload", "arxiv"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              tab === t
                ? "bg-blue-600 text-white"
                : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
            }`}
          >
            {t === "upload" ? "ファイルアップロード" : "arXiv検索"}
          </button>
        ))}
      </div>

      <div className="rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        {tab === "upload" ? <UploadTab isLive={isLive} /> : <ArxivTab isLive={isLive} />}
      </div>
    </section>
  );
}

// ── Upload Tab ──

function UploadTab({ isLive }: { isLive: boolean }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState("");

  const handleUpload = async (file: File) => {
    setUploading(true);
    setError("");
    setResult(null);
    if (!isLive) {
      await new Promise((r) => setTimeout(r, 2500));
      setResult(mockIngestResult);
      setUploading(false);
      return;
    }
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/v1/study/ingest", { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "アップロードに失敗しました");
    } finally {
      setUploading(false);
    }
  };

  const runDemoIngest = async () => {
    setUploading(true);
    setError("");
    setResult(null);
    await new Promise((r) => setTimeout(r, 2500));
    setResult(mockIngestResult);
    setUploading(false);
  };

  return (
    <div>
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const f = e.dataTransfer.files[0];
          if (f) handleUpload(f);
        }}
        className="rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 p-8 text-center cursor-pointer hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
      >
        {uploading ? (
          <Loader2 className="w-8 h-8 mx-auto text-blue-500 animate-spin" />
        ) : (
          <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {uploading ? "処理中..." : "PDFをドラッグ＆ドロップ、またはクリック"}
        </p>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleUpload(f);
        }}
      />

      {!isLive && (
        <div className="mt-3 flex items-center gap-2 text-sm">
          <span className="text-gray-500 dark:text-gray-400">📄 デモ:</span>
          <button
            type="button"
            onClick={runDemoIngest}
            disabled={uploading}
            className="text-xs px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 disabled:opacity-50 transition-colors"
          >
            サンプル論文をアップロード
          </button>
        </div>
      )}

      {result && (
        <div className="mt-4 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-sm">
          <p className="flex items-center gap-1 font-medium text-emerald-700 dark:text-emerald-400">
            <CheckCircle className="w-4 h-4" />
            {result.chunks_created}件のチャンク抽出 ({result.vlm_pages_processed > 0 ? `VLM ${result.vlm_pages_processed}ページ` : "テキスト抽出"})
          </p>
          {result.chunks_by_method && (
            <p className="mt-1 font-mono text-xs text-gray-500">
              テキスト: {result.chunks_by_method.pymupdf_text}, テーブル: {result.chunks_by_method.pymupdf_table}, 図表: {result.chunks_by_method.vlm_figure}
            </p>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-500/5 border border-red-500/20 text-sm text-red-600">{error}</div>
      )}
    </div>
  );
}

// ── arXiv Search Tab ──

function ArxivTab({ isLive }: { isLive: boolean }) {
  const [query, setQuery] = useState("");
  const [papers, setPapers] = useState<PaperSchema[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [fetchingId, setFetchingId] = useState<string | null>(null);
  const [fetchResult, setFetchResult] = useState<FetchPaperResponse | null>(null);

  const handleSearch = async (q?: string) => {
    const effective = (q ?? query).trim();
    if (!effective) return;
    setSearching(true);
    setPapers([]);
    setFetchResult(null);
    setSearchError("");
    if (!isLive) {
      await new Promise((r) => setTimeout(r, 2000));
      setPapers(MOCK_ARXIV_RESULTS[effective] ?? mockArxivSearch);
      setSearching(false);
      return;
    }
    try {
      const res = await fetch("/api/v1/study/search-papers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: effective, max_results: 8 }),
      });
      if (res.status === 429) {
        setSearchError("arXivのレート制限中です。数分待ってから再試行してください。");
        return;
      }
      const data = await res.json();
      setPapers(data.papers || []);
    } catch {
      // silent
    } finally {
      setSearching(false);
    }
  };

  const handleFetch = async (paper: PaperSchema) => {
    setFetchingId(paper.arxiv_id);
    setFetchResult(null);
    if (!isLive) {
      await new Promise((r) => setTimeout(r, 2000));
      setFetchResult(mockFetchResult);
      setPapers((prev) =>
        prev.map((p) => (p.arxiv_id === paper.arxiv_id ? { ...p, already_ingested: true } : p))
      );
      setFetchingId(null);
      return;
    }
    try {
      const res = await fetch("/api/v1/study/fetch-paper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pdf_url: paper.pdf_url, title: paper.title }),
      });
      if (res.ok) {
        const data: FetchPaperResponse = await res.json();
        setFetchResult(data);
        setPapers((prev) =>
          prev.map((p) => (p.arxiv_id === paper.arxiv_id ? { ...p, already_ingested: true } : p))
        );
      }
    } catch {
      // silent
    } finally {
      setFetchingId(null);
    }
  };

  return (
    <div>
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="キーワードを入力 (例: small data machine learning)"
          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => handleSearch()}
          disabled={searching}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
        >
          {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          検索
        </button>
      </div>

      <div className="mt-2 flex flex-wrap gap-2">
        <span className="text-xs text-gray-500 dark:text-gray-400 self-center">例:</span>
        {EXAMPLE_ARXIV_QUERIES.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => { setQuery(q); handleSearch(q); }}
            disabled={searching}
            className="text-xs px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 disabled:opacity-50 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      {papers.length > 0 && (
        <ul className="mt-4 space-y-2">
          {papers.map((p) => (
            <li
              key={p.arxiv_id}
              className="flex items-start justify-between gap-3 p-3 rounded-lg border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{p.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {p.authors.slice(0, 3).join(", ")} &middot; {p.published}
                </p>
              </div>
              {p.already_ingested ? (
                <span className="rounded-full px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-700 text-gray-500 whitespace-nowrap">
                  適載済み
                </span>
              ) : (
                <button
                  onClick={() => handleFetch(p)}
                  disabled={fetchingId === p.arxiv_id}
                  className="rounded-lg px-3 py-1 text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1 whitespace-nowrap"
                >
                  {fetchingId === p.arxiv_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                  追加
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {fetchResult && (
        <div className="mt-3 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-sm">
          <p className="flex items-center gap-1 font-medium text-emerald-700 dark:text-emerald-400">
            <CheckCircle className="w-4 h-4" />
            {fetchResult.chunks_created}件チャンク抽出 ({fetchResult.processing_time_sec}秒)
          </p>
        </div>
      )}

      {searchError && (
        <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-sm text-amber-600">
          {searchError}
        </div>
      )}
    </div>
  );
}

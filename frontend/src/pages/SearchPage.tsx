import { Search } from "lucide-react";
import SearchSection from "../components/SearchSection";

export default function SearchPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Search className="w-7 h-7 text-blue-500" />
          ナレッジ検索
        </h1>
        <p className="text-sm text-gray-500 mt-1 ml-10">登録済み論文からハイブリッド検索 + AI 回答</p>
      </div>
      <SearchSection />
    </div>
  );
}

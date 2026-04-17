import { History } from "lucide-react";
import HistorySection from "../components/HistorySection";

export default function HistoryPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <History className="w-7 h-7 text-blue-500" />
          学習履歴
        </h1>
        <p className="text-sm text-gray-500 mt-1 ml-10">過去のクイズ結果と学習記録</p>
      </div>
      <HistorySection />
    </div>
  );
}

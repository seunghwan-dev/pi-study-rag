import { BarChart3 } from "lucide-react";
import DashboardSection from "../components/DashboardSection";

export default function DashboardPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <BarChart3 className="w-7 h-7 text-blue-500" />
          ダッシュボード
        </h1>
        <p className="text-sm text-gray-500 mt-1 ml-10">学習進捗と論文統計の概要</p>
      </div>
      <DashboardSection />
    </div>
  );
}

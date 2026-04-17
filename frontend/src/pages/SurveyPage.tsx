import { Bot } from "lucide-react";
import SurveySection from "../components/SurveySection";

export default function SurveyPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Bot className="w-7 h-7 text-blue-500" />
          論文サーベイ
        </h1>
        <p className="text-sm text-gray-500 mt-1 ml-10">AI エージェントが関連論文を自動収集・分析</p>
      </div>
      <SurveySection />
    </div>
  );
}

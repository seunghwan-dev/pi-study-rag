import { PenLine } from "lucide-react";
import QuizSection from "../components/QuizSection";

export default function QuizPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <PenLine className="w-7 h-7 text-blue-500" />
          クイズモード
        </h1>
        <p className="text-sm text-gray-500 mt-1 ml-10">論文内容の理解度をクイズで確認</p>
      </div>
      <QuizSection />
    </div>
  );
}

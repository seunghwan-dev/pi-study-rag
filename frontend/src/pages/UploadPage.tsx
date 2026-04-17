import { FileUp } from "lucide-react";
import UploadSection from "../components/UploadSection";

export default function UploadPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <FileUp className="w-7 h-7 text-blue-500" />
          論文を追加
        </h1>
        <p className="text-sm text-gray-500 mt-1 ml-10">PDF アップロード または arXiv から検索</p>
      </div>
      <UploadSection />
    </div>
  );
}

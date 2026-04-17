import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "./contexts/AppContext";
import Sidebar from "./components/layout/Sidebar";
import Header from "./components/layout/Header";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";
import SurveyPage from "./pages/SurveyPage";
import QuizPage from "./pages/QuizPage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";

export default function App() {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("pi-dark") === "true";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("pi-dark", String(darkMode));
  }, [darkMode]);

  return (
    <AppProvider>
      <BrowserRouter>
        <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
          <Sidebar />
          <div className="flex-1 ml-60 flex flex-col">
            <Header
              darkMode={darkMode}
              onToggleDark={() => setDarkMode((d) => !d)}
            />
            <main className="flex-1 p-6 max-w-5xl w-full mx-auto">
              <Routes>
                <Route path="/" element={<UploadPage />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/survey" element={<SurveyPage />} />
                <Route path="/quiz" element={<QuizPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/history" element={<HistoryPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </AppProvider>
  );
}

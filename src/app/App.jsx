import { HashRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppHeader } from "../components/AppHeader";
import { ClubProfilePage } from "../pages/ClubProfilePage";
import { ClubsPage } from "../pages/ClubsPage";
import { ComparePage } from "../pages/ComparePage";

export default function App() {
  return (
    <HashRouter>
      <div className="appFrame">
        <AppHeader />
        <main className="appShell">
          <Routes>
            <Route path="/" element={<Navigate to="/compare" replace />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/clubs" element={<ClubsPage />} />
            <Route path="/clubs/:clubSlug" element={<ClubProfilePage />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
}

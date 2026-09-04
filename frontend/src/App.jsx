import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Settings from "./pages/Settings.jsx";
import IngestionLogs from "./pages/IngestionLogs.jsx";
import Validation from "./pages/Validation.jsx";
import ProposalDetail from "./pages/ProposalDetail.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/ingestion-logs" element={<IngestionLogs />} />
          <Route path="/validation" element={<Validation />} />
          <Route path="/validation/:domain/:proposalId" element={<ProposalDetail />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

// src/App.jsx
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { Activity, BarChart2, Upload } from "lucide-react";
import PredictPage from "./pages/PredictPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import BatchPage from "./pages/BatchPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
        {/* ── Sidebar ── */}
        <aside className="fixed inset-y-0 left-0 w-56 bg-slate-900 border-r border-slate-800 flex flex-col z-10">
          {/* Logo */}
          <div className="px-5 pt-7 pb-6 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md bg-gradient-to-br from-orange-500 to-rose-600 flex items-center justify-center">
                <Activity size={15} className="text-white" />
              </div>
              <div>
                <p className="text-xs font-bold tracking-widest uppercase text-orange-400">ChurnGuard</p>
                <p className="text-[10px] text-slate-500">Prediction System</p>
              </div>
            </div>
          </div>

          {/* Nav */}
          <nav className="flex-1 px-3 pt-5 space-y-1">
            {[
              { to: "/",         icon: Activity,  label: "Predict"   },
              { to: "/analytics",icon: BarChart2,  label: "Analytics" },
              { to: "/batch",    icon: Upload,     label: "Batch CSV" },
            ].map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ` +
                  (isActive
                    ? "bg-orange-500/15 text-orange-400 border border-orange-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800")
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </nav>

          <p className="px-5 py-4 text-[10px] text-slate-600">v1.0.0 · Internship Project</p>
        </aside>

        {/* ── Main content ── */}
        <main className="ml-56 min-h-screen">
          <Routes>
            <Route path="/"          element={<PredictPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/batch"     element={<BatchPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

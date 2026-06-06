// src/pages/BatchPage.jsx
import { useState, useRef } from "react";
import { predictCSV } from "../utils/api";
import { Upload, Download, Loader2, FileText } from "lucide-react";

const riskColor = {
  Low:    "bg-green-500/15 text-green-400 border-green-500/30",
  Medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  High:   "bg-rose-500/15 text-rose-400 border-rose-500/30",
};

export default function BatchPage() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [fileName, setFileName] = useState("");
  const inputRef = useRef();

  const handleFile = async (file) => {
    if (!file) return;
    setFileName(file.name); setError(""); setResults(null);
    setLoading(true);
    try {
      const data = await predictCSV(file);
      setResults(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Upload failed – check the CSV format.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const downloadCSV = () => {
    if (!results) return;
    const rows = [
      ["row_index", "customerID", "churn_probability", "churn_label", "risk_level"],
      ...results.predictions.map(r => [
        r.row_index, r.customerID || "", r.churn_probability, r.churn_label, r.risk_level
      ])
    ];
    const csv  = rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a"); a.href = url; a.download = "churn_predictions.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  const summary = results ? {
    total:  results.count,
    high:   results.predictions.filter(r => r.risk_level === "High").length,
    medium: results.predictions.filter(r => r.risk_level === "Medium").length,
    low:    results.predictions.filter(r => r.risk_level === "Low").length,
  } : null;

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Batch CSV Prediction</h1>
        <p className="text-slate-400 mt-1 text-sm">Upload a CSV file with customer data to predict churn for multiple customers at once.</p>
      </div>

      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={e => e.preventDefault()}
        onClick={() => inputRef.current.click()}
        className="border-2 border-dashed border-slate-700 hover:border-orange-500/50 rounded-2xl
                   p-10 flex flex-col items-center justify-center gap-4 cursor-pointer
                   transition-all bg-slate-900/40 hover:bg-slate-900/80 mb-6"
      >
        <div className="w-12 h-12 rounded-xl bg-orange-500/10 border border-orange-500/30 flex items-center justify-center">
          {loading ? <Loader2 size={22} className="text-orange-400 animate-spin" /> : <Upload size={22} className="text-orange-400" />}
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-semibold">{loading ? "Processing…" : "Drop CSV file here or click to browse"}</p>
          <p className="text-slate-500 text-sm mt-1">Supports up to 1,000 rows · Must include tenure, MonthlyCharges, Contract, etc.</p>
        </div>
        {fileName && <p className="text-xs text-orange-400 font-medium">📎 {fileName}</p>}
        <input ref={inputRef} type="file" accept=".csv" className="hidden" onChange={e => handleFile(e.target.files[0])} />
      </div>

      {error && (
        <div className="p-3 mb-6 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-sm">
          {error}
        </div>
      )}

      {results && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[
              { label: "Total",  val: summary.total,  color: "text-white"  },
              { label: "High Risk", val: summary.high, color: "text-rose-400" },
              { label: "Medium Risk",val: summary.medium, color: "text-amber-400" },
              { label: "Low Risk", val: summary.low,  color: "text-green-400" },
            ].map(({ label, val, color }) => (
              <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
                <p className={`text-2xl font-bold ${color}`}>{val}</p>
                <p className="text-xs text-slate-500 mt-1">{label}</p>
              </div>
            ))}
          </div>

          {/* Download Button */}
          <div className="flex justify-end mb-4">
            <button
              onClick={downloadCSV}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700
                         text-slate-300 hover:text-white text-sm font-medium transition"
            >
              <Download size={14} /> Export Results CSV
            </button>
          </div>

          {/* Results Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-sm">
                <thead className="bg-slate-800 sticky top-0">
                  <tr>
                    {["#", "Customer ID", "Probability", "Churn", "Risk Level"].map(h => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {results.predictions.map((r, i) => (
                    <tr key={i} className="hover:bg-slate-800/50 transition">
                      <td className="px-4 py-3 text-slate-500">{r.row_index + 1}</td>
                      <td className="px-4 py-3 text-slate-300 font-mono text-xs">{r.customerID || "—"}</td>
                      <td className="px-4 py-3 font-semibold text-slate-100">{(r.churn_probability * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${r.churn_label === "Yes" ? "bg-rose-500/15 text-rose-400 border-rose-500/30" : "bg-green-500/15 text-green-400 border-green-500/30"}`}>
                          {r.churn_label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${riskColor[r.risk_level]}`}>
                          {r.risk_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

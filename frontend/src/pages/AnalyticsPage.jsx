// src/pages/AnalyticsPage.jsx
import { useEffect, useState } from "react";
import { getModelInfo, getHealth } from "../utils/api";
import {
  RadialBarChart, RadialBar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

const MetricCard = ({ label, value, color }) => (
  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-2">
    <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">{label}</p>
    <p className={`text-3xl font-bold ${color}`}>{(value * 100).toFixed(1)}%</p>
    <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${value * 100}%`, background: color.includes("green") ? "#22c55e" : color.includes("amber") ? "#f59e0b" : color.includes("blue") ? "#3b82f6" : color.includes("purple") ? "#a855f7" : "#f97316" }} />
    </div>
  </div>
);

export default function AnalyticsPage() {
  const [info, setInfo]   = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getModelInfo(), getHealth()])
      .then(([i, h]) => { setInfo(i); setHealth(h); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="p-8 flex items-center gap-3 text-slate-400">
      <Loader2 size={18} className="animate-spin" /> Loading model info…
    </div>
  );

  if (!info) return (
    <div className="p-8 text-rose-400">
      Could not load model info. Make sure the backend is running and a model has been trained.
    </div>
  );

  const m = info.metrics;
  const chartData = [
    { name: "Accuracy",  value: m.accuracy,  fill: "#f97316" },
    { name: "Precision", value: m.precision, fill: "#3b82f6" },
    { name: "Recall",    value: m.recall,    fill: "#a855f7" },
    { name: "F1 Score",  value: m.f1,        fill: "#22c55e" },
    { name: "ROC-AUC",   value: m.roc_auc,   fill: "#f59e0b" },
  ];

  return (
    <div className="p-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Model Analytics</h1>
        <p className="text-slate-400 mt-1 text-sm">Performance metrics for the deployed churn prediction model.</p>
      </div>

      {/* Status Banner */}
      <div className={`flex items-center gap-3 p-4 rounded-xl border mb-6 text-sm font-medium ${
        health?.model_ready
          ? "bg-green-500/10 border-green-500/30 text-green-300"
          : "bg-rose-500/10 border-rose-500/30 text-rose-300"
      }`}>
        {health?.model_ready ? <CheckCircle size={16} /> : <XCircle size={16} />}
        {health?.model_ready
          ? `Model "${info.model_name}" is live and ready.`
          : "Model is not loaded. Run the training script first."}
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {[
          { label: "Accuracy",  value: m.accuracy,  color: "text-orange-400" },
          { label: "Precision", value: m.precision, color: "text-blue-400"   },
          { label: "Recall",    value: m.recall,    color: "text-purple-400" },
          { label: "F1 Score",  value: m.f1,        color: "text-green-400"  },
          { label: "ROC-AUC",   value: m.roc_auc,   color: "text-amber-400"  },
        ].map(p => <MetricCard key={p.label} {...p} />)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <p className="text-sm font-semibold text-slate-300 mb-4">Metrics Overview</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} barSize={30}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} />
              <YAxis domain={[0, 1]} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}
                labelStyle={{ color: "#e2e8f0" }}
                formatter={v => [`${(v * 100).toFixed(2)}%`]}
              />
              <Bar dataKey="value" radius={[4,4,0,0]}>
                {chartData.map((entry, i) => (
                  <rect key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Feature list */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <p className="text-sm font-semibold text-slate-300 mb-4">
            Input Features <span className="text-slate-500 font-normal">({info.features.length} total)</span>
          </p>
          <div className="grid grid-cols-2 gap-1.5 max-h-52 overflow-y-auto pr-1">
            {info.features.map(f => (
              <div key={f} className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1.5 rounded-lg truncate">
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

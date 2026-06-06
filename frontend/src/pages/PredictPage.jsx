// src/pages/PredictPage.jsx
import { useState } from "react";
import { predictChurn } from "../utils/api";
import RiskGauge from "../components/RiskGauge";
import { Loader2, Send, RefreshCw } from "lucide-react";

const INITIAL = {
  gender: "Male", SeniorCitizen: 0, Partner: "No", Dependents: "No",
  tenure: 12, PhoneService: "Yes", MultipleLines: "No",
  InternetService: "DSL", OnlineSecurity: "No", TechSupport: "No",
  StreamingTV: "No", Contract: "Month-to-month", PaperlessBilling: "Yes",
  PaymentMethod: "Electronic check", MonthlyCharges: 65.0,
};

const Field = ({ label, children }) => (
  <div className="flex flex-col gap-1.5">
    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{label}</label>
    {children}
  </div>
);

const Select = ({ value, onChange, options }) => (
  <select
    value={value} onChange={e => onChange(e.target.value)}
    className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100
               focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition"
  >
    {options.map(o => <option key={o}>{o}</option>)}
  </select>
);

const NumberInput = ({ value, onChange, min, max, step = 1 }) => (
  <input
    type="number" value={value} min={min} max={max} step={step}
    onChange={e => onChange(Number(e.target.value))}
    className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100
               focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition"
  />
);

export default function PredictPage() {
  const [form, setForm] = useState(INITIAL);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async () => {
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await predictChurn(form);
      setResult(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "API error – is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Churn Prediction</h1>
        <p className="text-slate-400 mt-1 text-sm">Enter customer details below to predict churn probability.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Form ── */}
        <div className="lg:col-span-2 bg-slate-900 rounded-2xl border border-slate-800 p-6">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Gender">
              <Select value={form.gender} onChange={v => set("gender", v)} options={["Male", "Female"]} />
            </Field>
            <Field label="Senior Citizen">
              <Select value={String(form.SeniorCitizen)} onChange={v => set("SeniorCitizen", Number(v))} options={["0", "1"]} />
            </Field>
            <Field label="Partner">
              <Select value={form.Partner} onChange={v => set("Partner", v)} options={["Yes", "No"]} />
            </Field>
            <Field label="Dependents">
              <Select value={form.Dependents} onChange={v => set("Dependents", v)} options={["Yes", "No"]} />
            </Field>
            <Field label="Tenure (months)">
              <NumberInput value={form.tenure} onChange={v => set("tenure", v)} min={0} max={72} />
            </Field>
            <Field label="Monthly Charges ($)">
              <NumberInput value={form.MonthlyCharges} onChange={v => set("MonthlyCharges", v)} min={0} max={200} step={0.5} />
            </Field>
            <Field label="Internet Service">
              <Select value={form.InternetService} onChange={v => set("InternetService", v)}
                options={["DSL", "Fiber optic", "No"]} />
            </Field>
            <Field label="Contract">
              <Select value={form.Contract} onChange={v => set("Contract", v)}
                options={["Month-to-month", "One year", "Two year"]} />
            </Field>
            <Field label="Payment Method">
              <Select value={form.PaymentMethod} onChange={v => set("PaymentMethod", v)}
                options={["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]} />
            </Field>
            <Field label="Online Security">
              <Select value={form.OnlineSecurity} onChange={v => set("OnlineSecurity", v)}
                options={["Yes", "No", "No internet service"]} />
            </Field>
            <Field label="Tech Support">
              <Select value={form.TechSupport} onChange={v => set("TechSupport", v)}
                options={["Yes", "No", "No internet service"]} />
            </Field>
            <Field label="Paperless Billing">
              <Select value={form.PaperlessBilling} onChange={v => set("PaperlessBilling", v)} options={["Yes", "No"]} />
            </Field>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleSubmit} disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-400
                         disabled:opacity-60 text-white font-semibold text-sm transition"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {loading ? "Predicting…" : "Predict Churn"}
            </button>
            <button
              onClick={() => { setForm(INITIAL); setResult(null); setError(""); }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-700
                         text-slate-400 hover:text-slate-200 hover:border-slate-600 text-sm transition"
            >
              <RefreshCw size={14} /> Reset
            </button>
          </div>
        </div>

        {/* ── Result Panel ── */}
        <div className="flex flex-col gap-4">
          {result ? (
            <>
              <RiskGauge probability={result.churn_probability} riskLevel={result.risk_level} />

              <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Prediction Details</p>
                {[
                  ["Probability",  `${(result.churn_probability * 100).toFixed(1)}%`],
                  ["Will Churn",   result.churn_label],
                  ["Risk Level",   result.risk_level],
                  ["Model Used",   result.model_name],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between text-sm">
                    <span className="text-slate-400">{k}</span>
                    <span className="font-semibold text-slate-100">{v}</span>
                  </div>
                ))}
              </div>

              <div className={`rounded-2xl p-4 text-sm font-medium ${
                result.risk_level === "High"
                  ? "bg-rose-500/10 border border-rose-500/30 text-rose-300"
                  : result.risk_level === "Medium"
                  ? "bg-amber-500/10 border border-amber-500/30 text-amber-300"
                  : "bg-green-500/10 border border-green-500/30 text-green-300"
              }`}>
                {result.risk_level === "High" && "⚠️  Immediate retention action recommended."}
                {result.risk_level === "Medium" && "📊  Monitor customer – consider a loyalty offer."}
                {result.risk_level === "Low" && "✅  Customer appears satisfied and stable."}
              </div>
            </>
          ) : (
            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-8 flex flex-col items-center justify-center text-center gap-3 h-full min-h-[280px]">
              <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center">
                <Send size={20} className="text-slate-600" />
              </div>
              <p className="text-slate-500 text-sm">Fill in the form and click<br/><span className="text-orange-400 font-semibold">Predict Churn</span> to see results.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

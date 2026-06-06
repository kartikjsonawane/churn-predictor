// src/components/RiskGauge.jsx
// Circular gauge showing churn probability with color coding

export default function RiskGauge({ probability, riskLevel }) {
  const pct      = Math.round(probability * 100);
  const radius   = 52;
  const circ     = 2 * Math.PI * radius;
  const dashArr  = `${(pct / 100) * circ} ${circ}`;

  const colors = {
    Low:    { stroke: "#22c55e", text: "text-green-400",  bg: "bg-green-500/10",  border: "border-green-500/30"  },
    Medium: { stroke: "#f59e0b", text: "text-amber-400",  bg: "bg-amber-500/10",  border: "border-amber-500/30"  },
    High:   { stroke: "#ef4444", text: "text-rose-400",   bg: "bg-rose-500/10",   border: "border-rose-500/30"   },
  };
  const c = colors[riskLevel] || colors.Low;

  return (
    <div className={`flex flex-col items-center gap-4 p-6 rounded-2xl border ${c.bg} ${c.border}`}>
      <svg width="140" height="140" viewBox="0 0 140 140">
        {/* Track */}
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#1e293b" strokeWidth="12" />
        {/* Progress */}
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke={c.stroke}
          strokeWidth="12"
          strokeDasharray={dashArr}
          strokeDashoffset={circ / 4}   /* start at top */
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
        {/* Label */}
        <text x="70" y="65" textAnchor="middle" fill="white" fontSize="22" fontWeight="700">
          {pct}%
        </text>
        <text x="70" y="85" textAnchor="middle" fill="#94a3b8" fontSize="11">
          Churn Risk
        </text>
      </svg>

      <div className={`px-4 py-1.5 rounded-full text-sm font-semibold ${c.text} ${c.bg} border ${c.border}`}>
        {riskLevel} Risk
      </div>
    </div>
  );
}

"use client";

type KPIProps = {
  kpis: {
    total_jobs: number;
    avg_ctc: number;
    avg_experience: number;
    top_skill: string | null;
  } | null;
  loading?: boolean;
};

function formatNumber(n: number | undefined) {
  if (n == null) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return n.toLocaleString();
}

export default function KPIBar({ kpis, loading }: KPIProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      
      {/* Active Jobs */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Jobs</div>
        <div className="mt-2 text-3xl font-bold text-slate-900">
          {loading ? "..." : kpis?.total_jobs.toLocaleString()}
        </div>
      </div>

      {/* Avg Salary */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Avg Annual CTC</div>
        <div className="mt-2 text-3xl font-bold text-emerald-600">
          {loading ? "..." : `₹${formatNumber(kpis?.avg_ctc)}`}
        </div>
      </div>

      {/* Avg Experience */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Avg Experience</div>
        <div className="mt-2 text-3xl font-bold text-blue-600">
          {loading ? "..." : `${kpis?.avg_experience.toFixed(1)} yrs`}
        </div>
      </div>

      {/* Top Skill */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">🔥 Top Skill</div>
        <div className="mt-2 text-2xl font-bold text-slate-900 capitalize truncate">
          {loading ? "..." : kpis?.top_skill || "N/A"}
        </div>
      </div>

    </div>
  );
}
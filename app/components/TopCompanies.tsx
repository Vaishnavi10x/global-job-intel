"use client";

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

type CompanyPoint = { company: string; count: number };
type Props = { companies: CompanyPoint[] };

export default function TopCompanies({ companies }: Props) {
  if (!companies || companies.length === 0) {
    return <div className="h-full flex items-center justify-center text-slate-400 text-xs">No company data available.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={companies}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
      >
        <XAxis type="number" hide />
        <YAxis
          dataKey="company"
          type="category"
          width={120}
          tick={{ fontSize: 10, fill: "#475569", fontWeight: 600 }}
          interval={0}
        />
        <Tooltip
          cursor={{ fill: '#f1f5f9' }}
          content={({ active, payload }) => {
            if (!active || !payload || !payload.length) return null;
            const p = payload[0].payload as any;
            return (
              <div className="bg-white border border-slate-200 px-2 py-1 text-xs rounded shadow-md text-slate-700">
                <div className="font-bold text-emerald-600">{p.company}</div>
                <div>{p.count.toLocaleString()} jobs</div>
              </div>
            );
          }}
        />
        <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} barSize={15} />
      </BarChart>
    </ResponsiveContainer>
  );
}
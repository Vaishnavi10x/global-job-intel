"use client";

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

type SkillPoint = { skill: string; count: number };
type Props = { skills: SkillPoint[] };

export default function InDemandSkills({ skills }: Props) {
  if (!skills || skills.length === 0) {
    return <div className="h-full flex items-center justify-center text-slate-400 text-xs">No skills data available.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={skills}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
      >
        <XAxis type="number" hide />
        <YAxis
          dataKey="skill"
          type="category"
          width={100}
          tick={{ fontSize: 11, fill: "#475569", fontWeight: 500 }} // Dark Slate Text
        />
        <Tooltip
          cursor={{ fill: '#f1f5f9' }}
          content={({ active, payload }) => {
            if (!active || !payload || !payload.length) return null;
            const p = payload[0].payload as any;
            return (
              <div className="bg-white border border-slate-200 px-2 py-1 text-xs rounded shadow-md text-slate-700">
                <div className="font-bold text-blue-600 capitalize">{p.skill}</div>
                <div>{p.count.toLocaleString()} jobs</div>
              </div>
            );
          }}
        />
        <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={18} />
      </BarChart>
    </ResponsiveContainer>
  );
}
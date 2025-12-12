"use client";

import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip, ZAxis, Brush } from "recharts";

type MapPoint = { city: string; count: number; lat: number; lon: number; };
type Props = { points: MapPoint[] };

export default function HiringMap({ points }: Props) {
  if (!points || points.length === 0) return <div className="h-full flex items-center justify-center text-slate-500">No Data</div>;

  const data = points.map((p) => ({ ...p, x: p.lon, y: p.lat, size: Math.sqrt(p.count) * 4 }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        {/* Domain set to standard map coordinates */}
        <XAxis type="number" dataKey="x" domain={[-180, 180]} hide />
        <YAxis type="number" dataKey="y" domain={[-60, 85]} hide />
        <ZAxis type="number" dataKey="size" range={[50, 400]} />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload || !payload.length) return null;
            const p = payload[0].payload as MapPoint;
            return (
              <div className="bg-slate-900 border border-slate-700 p-2 text-xs text-white rounded shadow-xl z-50">
                <div className="font-bold">{p.city}</div>
                <div className="text-sky-400">{p.count} Jobs</div>
              </div>
            );
          }}
        />
        <Scatter data={data} fill="#38bdf8" fillOpacity={0.7} stroke="#0ea5e9" />
        {/* Allows dragging to zoom horizontally */}
        <Brush dataKey="x" height={20} stroke="#475569" fill="#1e293b" />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
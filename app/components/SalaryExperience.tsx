"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from "recharts";

type SalaryPoint = { city: string; years: number; avg_salary: number; job_count: number };
type Props = { data: SalaryPoint[] };

export default function SalaryExperience({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-400 text-sm">
        <span className="text-2xl mb-2">📊</span>
        Add cities from the dropdown to compare salaries.
      </div>
    );
  }

  const yearsSet = Array.from(new Set(data.map((d) => d.years))).sort((a, b) => a - b);
  const cities = Array.from(new Set(data.map((d) => d.city)));
  
  // Bright/Distinct colors for light mode
  const colors = ["#2563eb", "#db2777", "#16a34a", "#d97706", "#7c3aed"];

  const chartData = yearsSet.map((y) => {
    const row: any = { years: y };
    cities.forEach((c) => {
      const match = data.find((d) => d.years === y && d.city === c);
      if (match) {
        row[c] = match.avg_salary;
        row[`${c}_count`] = match.job_count; 
      }
    });
    return row;
  });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-slate-200 p-3 rounded shadow-lg text-xs text-slate-700">
          <p className="font-bold mb-2 text-slate-900">{label} Years Experience</p>
          {payload.map((entry: any, index: number) => {
            const cityName = entry.name;
            const salary = entry.value;
            const count = entry.payload[`${cityName}_count`] || 0;
            return (
              <div key={index} className="flex items-center gap-2 mb-1">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></div>
                <span className="font-medium">{cityName}:</span>
                <span className="text-emerald-600 font-bold">₹{(salary/100000).toFixed(1)}L</span>
                <span className="text-slate-400">({count} jobs)</span>
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
        {/* Light Grid */}
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        
        <XAxis 
          dataKey="years" 
          stroke="#64748b" 
          tick={{ fontSize: 11 }}
          label={{ value: 'Years Exp', position: 'insideBottom', offset: -5, fill: '#94a3b8', fontSize: 10 }}
        />
        
        <YAxis 
          stroke="#64748b"
          tickFormatter={(v) => `${(v/100000).toFixed(0)}L`} 
          tick={{ fontSize: 11 }}
        />
        
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ color: '#475569' }} />
        
        {cities.map((city, index) => (
          <Line
            key={city}
            type="monotone"
            dataKey={city}
            stroke={colors[index % colors.length]}
            strokeWidth={3}
            dot={{ r: 4, strokeWidth: 2 }}
            activeDot={{ r: 6 }}
            connectNulls={true} 
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
"use client";

type Job = {
  job_role: string;
  city: string;
  country: string;
  min_experience: number;
  parsed_salary: number;
  job_type: string;
  location_type: string;
  apply_url?: string; // May exist
  job_id?: string;    // May exist
};

export default function JobsTable({ jobs }: { jobs: Job[] }) {
  if (!jobs || jobs.length === 0) return <div className="text-slate-400 text-sm text-center py-4">No recent jobs found matching your filters.</div>;

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-left text-sm text-slate-600">
        <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-bold border-b border-slate-200">
          <tr>
            <th className="p-4">Role</th>
            <th className="p-4">Location</th>
            <th className="p-4">Exp</th>
            <th className="p-4">Salary (Est.)</th>
            <th className="p-4">Type</th>
            <th className="p-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {jobs.map((job, i) => {
            // Priority: Apply URL > CareerPilot Job Page > CareerPilot Home
            let link = job.apply_url;
            if (!link && job.job_id) {
                link = `https://careerpilot.10xscale.ai/jobs/${job.job_id}`;
            } else if (!link) {
                link = "https://careerpilot.10xscale.ai/";
            }

            return (
            <tr key={i} className="hover:bg-slate-50 transition">
              <td className="p-4 font-medium text-slate-900">
                 {/* Clickable Title */}
                 <a href={link} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 hover:underline">
                    {job.job_role}
                 </a>
              </td>
              <td className="p-4">{job.city}, {job.country}</td>
              <td className="p-4">{job.min_experience} Yrs</td>
              <td className="p-4 text-emerald-600 font-medium">
                {job.parsed_salary > 0 ? `₹${(job.parsed_salary/100000).toFixed(1)}L` : "—"}
              </td>
              <td className="p-4">
                 <div className="flex gap-2">
                    {job.location_type && <span className="bg-blue-50 text-blue-600 px-2 py-1 rounded text-xs font-medium border border-blue-100">{job.location_type}</span>}
                    {job.job_type && <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded text-xs border border-slate-200">{job.job_type}</span>}
                 </div>
              </td>
              <td className="p-4 text-right">
                <a 
                    href={link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="bg-slate-900 text-white px-4 py-2 rounded-md text-xs font-medium hover:bg-slate-700 transition shadow-sm"
                >
                    Apply ↗
                </a>
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
"use client";

import { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic"; 
import KPIBar from "@/components/KPIBar"; 
import InDemandSkills from "@/components/InDemandSkills"; 
import SalaryExperience from "@/components/SalaryExperience"; 
import TopCompanies from "@/components/TopCompanies"; 

import { 
  fetchKpis, fetchMapPoints, fetchSkills, fetchSalaryCurve, 
  fetchFilterOptions, fetchCompanies 
} from "@/app/lib/api";

const InteractiveMap = dynamic(() => import("@/components/InteractiveMap"), { 
  ssr: false, loading: () => <div className="h-full flex items-center justify-center text-slate-400">Loading Map...</div>
});

export default function DashboardPage() {
  const [optionCountries, setOptionCountries] = useState<string[]>([]);
  const [optionRoles, setOptionRoles] = useState<string[]>([]);

  const [selectedCountry, setSelectedCountry] = useState<string>("Global"); 
  const [selectedRole, setSelectedRole] = useState<string>("All Roles");
  const [searchKeyword, setSearchKeyword] = useState<string>(""); 
  const [minExperience, setMinExperience] = useState<number>(10);
  const [dateFilter, setDateFilter] = useState<string>("all");

  const [kpis, setKpis] = useState(null);
  const [mapPoints, setMapPoints] = useState([]);
  const [skills, setSkills] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [salaryData, setSalaryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedComparisonCities, setSelectedComparisonCities] = useState<string[]>([]);

  useEffect(() => {
    async function loadOptions() {
        const data = await fetchFilterOptions();
        setOptionCountries(Array.from(new Set(["Global", ...data.countries])));
        setOptionRoles(Array.from(new Set(["All Roles", ...data.roles])));
    }
    loadOptions();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      async function loadDashboardData() {
          setLoading(true);
          try {
            const filters = {
                countries: selectedCountry === "Global" ? [] : [selectedCountry],
                role: selectedRole === "All Roles" ? "" : selectedRole,
                minExp: minExperience,
                keywords: searchKeyword,
                daysAgo: dateFilter,
            };

            const [kpiRes, mapRes, skillRes, salRes, compRes] = await Promise.all([
                fetchKpis(filters),
                fetchMapPoints(filters),
                fetchSkills(filters),
                fetchSalaryCurve(filters),
                fetchCompanies(filters)
            ]);

            setKpis(kpiRes);
            setMapPoints(mapRes);
            setSkills(skillRes);
            setSalaryData(salRes);
            setCompanies(compRes);
            
            if (salRes.length > 0) {
                const uniqueCities = Array.from(new Set(salRes.map((x: any) => x.city)));
                if (selectedComparisonCities.length === 0) {
                    setSelectedComparisonCities(uniqueCities.slice(0, 3) as string[]);
                }
            }
          } catch (error) { console.error(error); } 
          finally { setLoading(false); }
      }
      loadDashboardData();
    }, 500);
    return () => clearTimeout(timer);
  }, [selectedCountry, selectedRole, minExperience, searchKeyword, dateFilter]);

  const filteredSalaryData = useMemo(() => {
      return salaryData.filter((d: any) => selectedComparisonCities.includes(d.city));
  }, [salaryData, selectedComparisonCities]);

  const availableCities = useMemo(() => {
      return Array.from(new Set(salaryData.map((d: any) => d.city))).sort();
  }, [salaryData]);

  const handleCitySelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const city = e.target.value;
      if (city && !selectedComparisonCities.includes(city)) {
          if (selectedComparisonCities.length < 5) setSelectedComparisonCities(prev => [...prev, city]);
          else alert("Max 5 cities allowed.");
      }
  };

  const removeCity = (city: string) => {
      setSelectedComparisonCities(prev => prev.filter(c => c !== city));
  };

  return (
    <div className="bg-slate-50 min-h-screen text-slate-900 font-sans p-6">
      
      <div className="max-w-7xl mx-auto mb-6">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Job Trends</h1>
        
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap gap-4 items-end shadow-sm">
          
          <div className="flex flex-col">
            <label className="text-[10px] text-slate-500 font-bold tracking-wider mb-1">LOCATION</label>
            <select 
              suppressHydrationWarning
              className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm w-48 focus:ring-2 focus:ring-blue-500 outline-none text-slate-700"
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
            >
              {optionCountries.map((c, i) => <option key={`${c}-${i}`} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-[10px] text-slate-500 font-bold tracking-wider mb-1">JOB ROLE</label>
            <select 
              suppressHydrationWarning
              className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm w-56 focus:ring-2 focus:ring-blue-500 outline-none text-slate-700"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
            >
               {optionRoles.map((r, i) => <option key={`${r}-${i}`} value={r}>{r}</option>)}
            </select>
          </div>

          <div className="flex flex-col flex-1 min-w-[200px]">
             <label className="text-[10px] text-slate-500 font-bold tracking-wider mb-1">SEARCH</label>
             <input 
                suppressHydrationWarning
                type="text" placeholder="e.g. Remote, Java..." 
                className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm w-full focus:ring-2 focus:ring-blue-500 outline-none text-slate-700 placeholder-slate-400"
                value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)}
             />
          </div>

          <div className="flex flex-col">
            <label className="text-[10px] text-slate-500 font-bold tracking-wider mb-1">POSTED DATE</label>
            <select 
              suppressHydrationWarning
              className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm w-40 focus:ring-2 focus:ring-blue-500 outline-none text-slate-700"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            >
               <option value="all">All Time</option>
               <option value="7">Last 7 Days</option>
               <option value="30">Last 30 Days</option>
               <option value="90">Last 90 Days</option>
            </select>
          </div>

          <div className="flex flex-col w-40">
             <label className="text-[10px] text-slate-500 font-bold tracking-wider mb-1 flex justify-between">
                <span>EXPERIENCE</span>
                <span className="text-blue-600 font-bold">{minExperience} Yrs</span>
             </label>
             <input 
               type="range" min="0" max="30" step="1" 
               value={minExperience} onChange={(e) => setMinExperience(parseInt(e.target.value))}
               className="h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600 mt-2"
             />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        <KPIBar kpis={kpis} loading={loading} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[500px]">
          {/* MAP */}
          <div className="lg:col-span-8 bg-white border border-slate-200 rounded-2xl p-4 flex flex-col shadow-sm">
             <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2"><span className="text-xl">🌍</span> Hiring Density</h3>
             <div className="flex-1 rounded-xl overflow-hidden border border-slate-100 z-0">
                <InteractiveMap points={mapPoints} />
             </div>
          </div>

          {/* SKILLS */}
          <div className="lg:col-span-4 bg-white border border-slate-200 rounded-2xl p-4 flex flex-col shadow-sm">
             <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2"><span className="text-xl">⚡</span> Top Skills</h3>
             <div className="flex-1 min-h-0">
                {loading ? <div className="text-center mt-10 text-slate-400">Loading...</div> : <InDemandSkills skills={skills} />}
             </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
           {/* SALARY CHART */}
           <div className="lg:col-span-8 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
             <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-slate-800 flex items-center gap-2"><span className="text-xl">💰</span> Salary vs Experience</h3>
                <select 
                  className="bg-slate-50 border border-slate-300 text-slate-700 text-xs rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500"
                  onChange={handleCitySelect}
                  value=""
                >
                  <option value="" disabled>+ Add City</option>
                  {availableCities.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
             </div>
             <div className="flex flex-wrap gap-2 mb-4">
                {selectedComparisonCities.map(city => (
                    <button key={city} onClick={() => removeCity(city)}
                      className="px-3 py-1 rounded-full text-xs font-medium border bg-blue-50 border-blue-200 text-blue-700 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition flex items-center gap-1"
                    >
                      {city} ✕
                    </button>
                ))}
             </div>
             <div className="h-80 w-full">
               {loading ? <div className="h-full flex items-center justify-center text-slate-400">Loading Chart...</div> : <SalaryExperience data={filteredSalaryData} />}
             </div>
           </div>

           {/* TOP COMPANIES */}
           <div className="lg:col-span-4 bg-white border border-slate-200 rounded-2xl p-4 flex flex-col shadow-sm">
               <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2"><span className="text-xl">🏢</span> Top Companies</h3>
               <div className="flex-1 min-h-0">
                  {loading ? <div className="text-center mt-10 text-slate-400">Loading...</div> : <TopCompanies companies={companies} />}
               </div>
           </div>
        </div>

        {/* --- NEW: VIEW ALL JOBS BANNER (Replaced Table) --- */}
        <div className="mt-8 mb-12 flex flex-col items-center justify-center bg-blue-50 border border-blue-100 rounded-2xl p-8 shadow-sm">
           <h3 className="text-2xl font-bold text-slate-900 mb-2">Looking for more details?</h3>
           <p className="text-slate-500 mb-6 text-center max-w-lg">
             Explore thousands of live job listings, filter by specific criteria, and apply directly on our main platform.
           </p>
           <a 
             href="https://careerpilot.10xscale.ai/login" 
             target="_blank" 
             rel="noopener noreferrer"
             className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-full shadow-lg transition transform hover:scale-105 flex items-center gap-2"
           >
             View All Job Openings ↗
           </a>
        </div>

      </div>
    </div>
  );
}
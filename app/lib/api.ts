const BACKEND = "/api/proxy";

function buildQuery(filters: any) {
  const params = new URLSearchParams();

  if (filters.countries && filters.countries.length > 0) {
    filters.countries.forEach((c: string) => params.append("countries", c));
  }
  if (filters.role) params.append("role", filters.role);
  if (filters.minExp !== undefined) params.append("exp_min", filters.minExp.toString());
  if (filters.keywords) params.append("keywords", filters.keywords);
  
  // Date Filter
  if (filters.daysAgo && filters.daysAgo !== "all") {
      params.append("days_ago", filters.daysAgo);
  }

  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

async function fetchJSON<T>(endpoint: string, filters: any = {}): Promise<T> {
  const queryString = buildQuery(filters);
  const url = `${BACKEND}${endpoint}${queryString}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    if (endpoint.includes("kpis")) return null as any;
    return [] as any;
  }
  return res.json();
}

export async function fetchFilterOptions() {
    const res = await fetch(`${BACKEND}/filter-options`, { cache: "no-store" });
    if (!res.ok) return { countries: [], roles: [] };
    return res.json();
}

export async function fetchKpis(filters: any) { return fetchJSON<any>("/kpis", filters); }
export async function fetchMapPoints(filters: any) { return fetchJSON<any[]>("/map-points", filters); }
export async function fetchSkills(filters: any) { return fetchJSON<any[]>("/skills", filters); }
export async function fetchSalaryCurve(filters: any) { return fetchJSON<any[]>("/salary_by_experience", filters); }
export async function fetchCompanies(filters: any) { return fetchJSON<any[]>("/companies", filters); } // NEW

export async function fetchRawJobs(filters: any) {
    const queryString = buildQuery(filters);
    const url = `${BACKEND}/raw-jobs${queryString}&limit=20`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
}
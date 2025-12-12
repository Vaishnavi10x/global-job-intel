"use client";

import { useEffect, useState } from "react";

type JobRow = {
  id?: string | number;
  title?: string | null;
  city?: string | null;
  country?: string | null;
  min_experience?: number | null;
  parsed_salary?: number | null;
  [key: string]: any;
};

export default function ApiTestPage() {
  const [data, setData] = useState<JobRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);

        await fetch("http://127.0.0.1:8000/init");

        const res = await fetch("http://127.0.0.1:8000/sample");
        if (!res.ok) throw new Error(`Backend error: ${res.status}`);

        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1>Backend API Test</h1>
      <p>This fetches from FastAPI backend.</p>

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && !error && (
        <>
          <p>Rows received: {data.length}</p>
          <div style={{ maxHeight: 400, overflow: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>City</th>
                  <th>Country</th>
                  <th>Experience</th>
                  <th>Salary</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={i}>
                    <td>{row.title}</td>
                    <td>{row.city}</td>
                    <td>{row.country}</td>
                    <td>{row.min_experience}</td>
                    <td>{row.parsed_salary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}

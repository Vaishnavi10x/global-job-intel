import { backendFetch } from "@/app/lib/api";

export default async function APITest2(props: any) {
  // MUST AWAIT searchParams
  const sp = await props.searchParams;
  const test = sp?.test || "cities";

  let endpoint = "/cities";

  if (test === "jobs") endpoint = "/jobs?page=1&limit=20";
  if (test === "roles") endpoint = "/roles";
  if (test === "sample") endpoint = "/sample";

  const data = await backendFetch(endpoint);

  return (
    <div style={{ padding: 20 }}>
      <h1>API Test 2</h1>
      <p>
        Test: <b>{test}</b>
      </p>
      <p>
        Endpoint: <code>{endpoint}</code>
      </p>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

// app/api/proxy/[...path]/route.ts
import { NextResponse } from "next/server";

export async function GET(
  req: Request,
  // FIX 1: Update the type definition because params is now a Promise
  { params }: { params: Promise<{ path?: string[] }> }
) {
  try {
    // FIX 2: Await the params before using them
    const { path: pathPartsRaw } = await params;
    const pathParts = pathPartsRaw ?? [];
    
    const path = "/" + pathParts.join("/");

    // Keep same backend host/port you use for FastAPI
    const BACKEND = "http://127.0.0.1:8000";

    // Preserve incoming query string
    const url = new URL(req.url);
    const query = url.search; // includes leading "?" if present

    const target = `${BACKEND}${path}${query}`;

    // Prepare headers: It's safer to remove the 'host' header so the backend 
    // doesn't get confused by the frontend's host.
    const headers = new Headers(req.headers);
    headers.delete("host"); 

    const res = await fetch(target, {
      method: "GET",
      headers: headers, 
    });

    // We assume backend returns JSON (your FastAPI does).
    const contentType = res.headers.get("content-type") || "application/json";
    const data = await res.json();

    return new NextResponse(JSON.stringify(data), {
      status: res.status,
      headers: { "content-type": contentType },
    });
  } catch (err: any) {
    console.error("proxy error:", err);
    return new NextResponse(JSON.stringify({ error: String(err) }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
}
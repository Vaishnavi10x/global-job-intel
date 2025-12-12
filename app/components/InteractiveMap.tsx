"use client";

import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

type MapPoint = { city: string; count: number; lat: number; lon: number; };

// Center slightly adjusted for better global view
const center: [number, number] = [20, 10]; 

export default function InteractiveMap({ points }: { points: MapPoint[] }) {
  if (!points || points.length === 0) {
    return <div className="h-full flex items-center justify-center text-slate-400 text-sm">No location data found for these filters.</div>;
  }

  return (
    <MapContainer 
        center={center} 
        zoom={2} 
        scrollWheelZoom={true} 
        style={{ height: "100%", width: "100%", background: "#f8fafc" }} // Light Gray bg
    >
      {/* Light Mode Tiles (CartoDB Voyager) */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
      />

      {points.map((p, idx) => (
        <CircleMarker
          key={idx}
          center={[p.lat, p.lon]}
          pathOptions={{ color: '#0ea5e9', fillColor: '#0ea5e9', fillOpacity: 0.6, weight: 1 }} // Sky Blue
          radius={Math.log(p.count) * 3 + 3} 
        >
          <Tooltip direction="top" offset={[0, -5]} opacity={1} className="custom-tooltip">
            <div className="font-bold text-slate-900">{p.city}</div>
            <div className="text-slate-600">{p.count.toLocaleString()} Jobs</div>
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
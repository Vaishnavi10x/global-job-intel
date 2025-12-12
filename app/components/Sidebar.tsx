'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { name: "Dashboard", path: "/" },
  { name: "Cities", path: "/cities" },
  { name: "Roles", path: "/roles" },
  { name: "Skills", path: "/skills" },
  { name: "Companies", path: "/companies" },
  { name: "Raw Jobs", path: "/api-test2?test=jobs" }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="h-screen w-64 bg-gray-900 text-white p-5 fixed shadow-lg">
      <h1 className="text-2xl font-bold mb-8 tracking-wide">
        Job Intel
      </h1>

      <nav className="flex flex-col space-y-3">
        {navItems.map((item) => {
          const active = pathname === item.path;

          return (
            <Link
              key={item.path}
              href={item.path}
              className={`p-2 rounded text-sm transition 
                ${active ? "bg-gray-700 font-semibold" : "hover:bg-gray-800"}
              `}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

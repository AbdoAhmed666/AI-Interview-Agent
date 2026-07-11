"use client";

import Link from "next/link";
import { LayoutDashboard, Brain, History, User } from "lucide-react";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/interview", label: "Interview", icon: Brain },
  { href: "/history", label: "History", icon: History },
  { href: "/profile", label: "Profile", icon: User },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-[var(--surface)] border-r border-[var(--border)] p-6">
      <h2 className="text-xl font-bold mb-8">AI Interview</h2>

      <nav className="space-y-2">
        {items.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-lg px-4 py-3 hover:bg-[var(--primary)] transition"
            >
              <Icon size={20} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
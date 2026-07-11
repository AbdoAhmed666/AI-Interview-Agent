"use client";

import { useAuth } from "@/contexts/AuthContext";
import { LogOut } from "lucide-react";

export default function Navbar() {

  const { user, logout } = useAuth();

  return (
    <header
      className="
        h-16
        border-b
        border-[var(--border)]
        bg-[var(--surface)]
        flex
        items-center
        justify-between
        px-8
      "
    >
      <div>
        <h1 className="text-xl font-bold">
          AI Interview Agent
        </h1>
      </div>

      <div className="flex items-center gap-4">

        <span className="text-[var(--text-secondary)]">
          Welcome {user?.name ?? "Guest"}
        </span>

        <div
          className="
            w-10
            h-10
            rounded-full
            bg-[var(--primary)]
            flex
            items-center
            justify-center
            font-bold
          "
        >
          {user?.name?.charAt(0).toUpperCase() ?? "A"}
        </div>

        <button
            onClick={logout}
            className="flex items-center gap-2 rounded-lg bg-red-500 px-4 py-2 hover:bg-red-600 transition"
            >
            <LogOut size={18} />
            Logout
        </button>

      </div>

    </header>
  );
}
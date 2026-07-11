import { ReactNode } from "react";

interface Props {
  children: ReactNode;
  className?: string;
}

export default function Card({
  children,
  className = "",
}: Props) {
  return (
    <div
      className={`
        rounded-2xl
        border
        border-[var(--border)]
        bg-[var(--surface)]
        p-6
        shadow-lg
        ${className}
      `}
    >
      {children}
    </div>
  );
}
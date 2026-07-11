import { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement>;

export default function Input({
  className = "",
  ...props
}: Props) {
  return (
    <input
      {...props}
      className={`
        w-full
        rounded-xl
        border
        border-[var(--border)]
        bg-[var(--surface)]
        px-4
        py-3
        text-white
        placeholder:text-[var(--text-muted)]
        focus:border-[var(--primary)]
        ${className}
      `}
    />
  );
}
import { ButtonHTMLAttributes } from "react";
import Spinner from "./Spinner";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
}

export default function Button({
  children,
  loading = false,
  className = "",
  ...props
}: Props) {
  return (
    <button
      disabled={loading || props.disabled}
      {...props}
      className={`
        flex
        items-center
        justify-center
        gap-2
        rounded-xl
        bg-[var(--primary)]
        px-5
        py-3
        font-semibold
        hover:bg-[var(--primary-hover)]
        disabled:opacity-60
        disabled:cursor-not-allowed
        transition-all
        ${className}
      `}
    >
      {loading && <Spinner />}

      {children}
    </button>
  );
}
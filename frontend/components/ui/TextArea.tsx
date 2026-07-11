import { TextareaHTMLAttributes } from "react";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement>;

export default function TextArea({
  className = "",
  ...props
}: Props) {
  return (
    <textarea
      {...props}
      className={`
        w-full
        min-h-40
        rounded-xl
        border
        border-[var(--border)]
        bg-[var(--surface)]
        p-4
        resize-none
        text-white
        placeholder:text-[var(--text-muted)]
        focus:border-[var(--primary)]
        ${className}
      `}
    />
  );
}
interface Props {
  text: string;
}

export default function Badge({
  text,
}: Props) {
  return (
    <span
      className="
      rounded-full
      bg-cyan-600/20
      px-3
      py-1
      text-sm
      text-cyan-300
    "
    >
      {text}
    </span>
  );
}
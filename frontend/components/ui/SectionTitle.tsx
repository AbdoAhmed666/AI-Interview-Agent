interface Props {
  title: string;
  subtitle?: string;
}

export default function SectionTitle({
  title,
  subtitle,
}: Props) {
  return (
    <div className="mb-8">
      <h2 className="text-3xl font-bold">
        {title}
      </h2>

      {subtitle && (
        <p className="mt-2 text-[var(--text-secondary)]">
          {subtitle}
        </p>
      )}
    </div>
  );
}
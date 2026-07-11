import Card from "./Card";

interface Props {
  title: string;
  value: string | number;
}

export default function StatCard({
  title,
  value,
}: Props) {
  return (
    <Card>

      <p className="text-sm text-[var(--text-secondary)]">
        {title}
      </p>

      <h3 className="mt-4 text-3xl font-bold">
        {value}
      </h3>

    </Card>
  );
}
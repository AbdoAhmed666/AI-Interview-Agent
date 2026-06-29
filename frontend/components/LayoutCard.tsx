type Props = {
  children: React.ReactNode
}

export default function LayoutCard({
  children
}: Props) {
  return (
    <div className="
      bg-[#111827]
      border
      border-gray-800
      rounded-2xl
      p-8
      shadow-xl
      mb-8
    ">
      {children}
    </div>
  )
}
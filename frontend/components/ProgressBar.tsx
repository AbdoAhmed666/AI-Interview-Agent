type Props = {
  current: number
  total: number
}

export default function ProgressBar({
  current,
  total
}: Props) {

  const percentage = (current / total) * 100

  return (
    <div className="mb-8">

      <div className="flex justify-between mb-2">

        <p className="text-gray-400">
          Interview Progress
        </p>

        <p className="text-cyan-400">
          {current}/{total}
        </p>

      </div>

      <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">

        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-cyan-500 transition-all duration-700"
          style={{
            width: `${percentage}%`
          }}
        />

      </div>

    </div>
  )
}
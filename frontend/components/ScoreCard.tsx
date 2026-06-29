type Props = {
  score: number
  feedback: string
}

export default function ScoreCard({
  score,
  feedback
}: Props) {

  return (
    <div className="mt-8 bg-[#111827] p-8 rounded-2xl border border-gray-800">

      <div className="text-center">

        <p className="text-gray-400 mb-2">
          Interview Score
        </p>

        <h2 className="text-5xl font-bold text-cyan-400 mb-4">
          {score}/10
        </h2>

      </div>

      <div className="mt-5 p-4 rounded-xl bg-[#0b1220]">

        <p className="text-gray-300">
          {feedback}
        </p>

      </div>

    </div>
  )
}
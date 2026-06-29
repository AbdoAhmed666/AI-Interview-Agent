type Props = {
  evaluation: any
}

export default function EvaluationCard({ evaluation }: Props) {
  return (
    <div className="mt-8">

      <div className="mb-6 bg-[#111827] p-6 rounded-2xl border border-gray-800">

        <p className="text-gray-400 mb-2">
          Score
        </p>

        <h2 className="text-4xl font-bold text-green-400">
          {evaluation.score}/10
        </h2>

      </div>

      <div className="grid md:grid-cols-2 gap-5">

        <div className="bg-[#111827] p-6 rounded-2xl">

          <p className="text-green-400 mb-4">
            Strengths
          </p>

          {evaluation.strengths?.map((item: string, i: number) => (
            <p key={i} className="mb-2">
              • {item}
            </p>
          ))}

        </div>

        <div className="bg-[#111827] p-6 rounded-2xl">

          <p className="text-red-400 mb-4">
            Weaknesses
          </p>

          {evaluation.weaknesses?.map((item: string, i: number) => (
            <p key={i} className="mb-2">
              • {item}
            </p>
          ))}

        </div>

      </div>

      <div className="mt-5 bg-[#111827] p-6 rounded-2xl">

        <p className="text-cyan-400 mb-4">
          AI Feedback
        </p>

        <p className="text-gray-300">
          {evaluation.feedback}
        </p>

      </div>

    </div>
  )
}
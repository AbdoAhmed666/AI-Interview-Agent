interface Props {
  summary: any
}

export default function InterviewFinished({ summary }: Props) {
  return (

    <div className="bg-[#111827] p-10 rounded-2xl border border-green-500">

      <h2 className="text-3xl font-bold text-green-400 mb-4">
        Interview Completed
      </h2>

      <p className="text-gray-300 mb-6">
        You completed all interview questions successfully.
      </p>

      {summary && (
        <div className="space-y-3">

          <p>
            Final Score: {summary.overall_score}/10
          </p>

          <p>
            Recommendation: {summary.hiring_recommendation}
          </p>

        </div>
      )}

    </div>
  )
}
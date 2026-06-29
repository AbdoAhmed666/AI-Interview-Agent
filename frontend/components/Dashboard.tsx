interface Props {
  evaluations: any[]
}

export default function Dashboard({ evaluations }: Props) {

  if (evaluations.length === 0) return null

  const scoreBuckets = {
    low: evaluations.filter(e => e.score < 5).length,
    mid: evaluations.filter(e => e.score >= 5 && e.score < 8).length,
    high: evaluations.filter(e => e.score >= 8).length,
    }

  const avg =
    evaluations.reduce((a, e) => a + e.score, 0) /
    evaluations.length

  const best =
    Math.max(...evaluations.map(e => e.score))

  const trend = evaluations.map(e => e.score)

  const weakAreas = evaluations.flatMap(e => e.weaknesses || [])
  const topWeak = weakAreas.slice(0, 5)

  const strengths = evaluations.flatMap(e => e.strengths || [])
  const topStrengths = strengths.slice(0, 5)

  return (
    <div className="bg-[#111827] p-6 rounded-xl mt-6">

      <h2 className="text-2xl font-bold mb-4">
        Performance Dashboard
      </h2>

      <div className="space-y-3">

        <p>Average Score: {avg.toFixed(1)}/10</p>

        <p>Best Score: {best}/10</p>

        <p>Questions Answered: {evaluations.length}</p>

      </div>

     <div className="mt-4">
        <h3 className="font-bold mb-2">Score Distribution</h3>

        <div className="space-y-2">
            <p>🔥 High (8-10): {scoreBuckets.high}</p>
            <p>⚡ Medium (5-7): {scoreBuckets.mid}</p>
            <p>⚠️ Low (0-4): {scoreBuckets.low}</p>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-bold mb-2">Performance Trend</h3>

        <div className="flex items-end gap-2 h-24">
            {trend.map((t, i) => (
            <div
                key={i}
                className="w-4 bg-cyan-500 rounded"
                style={{ height: `${t * 10}px` }}
            />
            ))}
        </div>
     </div>

     <div className="mt-6">
        <h3 className="font-bold text-red-400 mb-2">
            Weak Areas
        </h3>

        <div className="flex flex-wrap gap-2">
            {topWeak.map((w, i) => (
            <span
                key={i}
                className="px-2 py-1 bg-red-900/40 text-red-300 rounded"
            >
                {w}
            </span>
            ))}
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-bold text-green-400 mb-2">
            Strengths
        </h3>

        <div className="flex flex-wrap gap-2">
            {topStrengths.map((s, i) => (
            <span
                key={i}
                className="px-2 py-1 bg-green-900/40 text-green-300 rounded"
            >
                {s}
            </span>
            ))}
        </div>
      </div>

    </div>
  )
}
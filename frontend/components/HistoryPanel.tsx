type Props = {
  evaluations: any[]
}

export default function HistoryPanel({
  evaluations
}: Props) {
  return (
    <div className="bg-[#111827] rounded-2xl p-6">

      <h2 className="mb-5 text-cyan-400">
        History
      </h2>

      {evaluations.map((item, index) => (

        <div
          key={index}
          className="mb-4 p-4 bg-[#0b1220] rounded-xl"
        >

          <p>
            Question {index + 1}
          </p>

          <p className="text-green-400">
            Score: {item.score}/10
          </p>

        </div>

      ))}

    </div>
  )
}
type Props = {
  question: string
}

export default function InterviewCard({ question }: Props) {
  return (
    <div className="mt-8 bg-[#111827] border border-gray-800 rounded-2xl p-8">

      <p className="text-sm text-cyan-400 mb-3">
        Interview Question
      </p>

      <h2 className="text-xl leading-8">
        {question}
      </h2>

    </div>
  )
}
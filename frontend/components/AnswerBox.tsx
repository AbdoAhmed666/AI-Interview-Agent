// type Props = {
//   answer: string
//   setAnswer: (value: string) => void
//   onEvaluate: () => void
//   loading: boolean
// }

// export default function AnswerBox({
//   answer,
//   setAnswer,
//   onEvaluate,
//   loading
// }: Props) {
//   return (
//     <div className="mt-8 bg-[#111827] border border-gray-800 rounded-2xl p-8">

//       <p className="text-sm text-cyan-400 mb-3">
//         Your Answer
//       </p>

//       <textarea
//         value={answer}
//         onChange={(e) => setAnswer(e.target.value)}
//         rows={8}
//         className="
//           w-full
//           p-4
//           rounded-xl
//           bg-[#0b1220]
//           border
//           border-gray-700
//           text-white
//           resize-none
//           mb-5
//           outline-none
//         "
//       />

//       <button
//         onClick={onEvaluate}
//         className="
//           w-full
//           p-4
//           rounded-xl
//           bg-green-600
//           hover:bg-green-500
//           transition
//         "
//       >
//         {loading ? "Evaluating..." : "Evaluate Answer"}
//       </button>

//     </div>
//   )
// }

type Props = {
  answer: string
  setAnswer: (value: string) => void
  onSubmit: () => void
  loading: boolean
}

export default function AnswerBox({
  answer,
  setAnswer,
  onSubmit,
  loading
}: Props) {

  return (
    <div className="mt-8 bg-[#111827] p-8 rounded-2xl border border-gray-800">

      <p className="text-sm text-gray-400 mb-4">
        Your Answer
      </p>

      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        className="
                  w-full
                  min-h-[220px]
                  p-4
                  rounded-xl
                  bg-[#0b1220]
                  border border-gray-700
                  text-white
                  resize-none
                  outline-none
                  leading-7
                  "
      />

      <button
        onClick={onSubmit}
        className="mt-5 w-full p-4 rounded-xl bg-green-600 hover:bg-green-500"
      >
        {loading ? "Evaluating..." : "Submit Answer"}
      </button>

    </div>
  )
}
"use client"

import { useState } from "react"
import { downloadReport, startInterview, adaptiveInterview } from "../lib/api"

import InterviewCard from "../components/InterviewCard"
import AnswerBox from "../components/AnswerBox"
import EvaluationCard from "../components/EvaluationCard"
import ProgressBar from "../components/ProgressBar"
import HistoryPanel from "../components/HistoryPanel"
import Dashboard from "../components/Dashboard"
import VoiceRecorder from "../components/VoiceRecorder"
import QuestionSpeaker from "../components/QuestionSpeaker"

export default function Home() {

  const [role, setRole] = useState("")
  const [loading, setLoading] = useState(false)

  const [questions, setQuestions] = useState<string[]>([])
  const [answers, setAnswers] = useState<string[]>([])
  const [currentAnswer, setCurrentAnswer] = useState("")

  const [evaluations, setEvaluations] = useState<any[]>([])

  const [evalLoading, setEvalLoading] = useState(false)

  const [questionNumber, setQuestionNumber] = useState(1)
  const TOTAL_QUESTIONS = 5

  const [difficulty, setDifficulty] = useState(3)
  const [isFinished, setIsFinished] = useState(false)

  const [summary, setSummary] = useState<any>(null)

  // ---------------- START INTERVIEW ----------------
  async function handleStart() {
    try {
      setLoading(true)

      const data = await startInterview(role)

      setQuestions([data.question])
      setQuestionNumber(1)

      setAnswers([])
      setEvaluations([])

    } catch (error) {
      console.log(error)
      alert("Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  // ---------------- EVALUATE ----------------
async function handleEvaluate() {
  try {
    setEvalLoading(true)

    const lastQuestion = questions[questions.length - 1]

    const data = await adaptiveInterview(
      role,
      lastQuestion,
      currentAnswer,
      difficulty
    )

    const updatedAnswers = [...answers, currentAnswer]
    const updatedEvaluations = [...evaluations, data.evaluation]

    setAnswers(updatedAnswers)
    setEvaluations(updatedEvaluations)
    setDifficulty(data.difficulty)

    const nextQuestionNumber = questionNumber + 1

    if (nextQuestionNumber > TOTAL_QUESTIONS) {

      setIsFinished(true)

      const response = await fetch(
        "http://127.0.0.1:8001/summarize-session",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            role,
            questions,
            answers: updatedAnswers,
            evaluations: updatedEvaluations
          })
        }
      )

      const summaryData = await response.json()
      setSummary(summaryData)

    } else {

      if (data.evaluation.follow_up_question) {
        setQuestions(prev => [
          ...prev,
          data.evaluation.follow_up_question
        ])
      } else {
        setQuestions(prev => [
          ...prev,
          data.next_question
        ])
      }

      setQuestionNumber(nextQuestionNumber)
    }

    setCurrentAnswer("")

  } catch (error) {
    console.log(error)
    alert("Evaluation failed")
  } finally {
    setEvalLoading(false)
  }
}


  // ---------------- PDF ----------------
  async function handleDownload() {
    const reportData = {
      role,

      overall_score: summary.overall_score,

      overall_strengths:
        summary.overall_strengths,

      overall_weaknesses:
        summary.overall_weaknesses,

      hiring_recommendation:
        summary.hiring_recommendation,

      questions,
      answers,
      evaluations
    }

    const blob = await downloadReport(reportData)

    const url = window.URL.createObjectURL(blob)

    const a = document.createElement("a")
    a.href = url
    a.download = "report.pdf"
    a.click()
  }

  return (
    <main className="min-h-screen bg-[#071120] text-white px-6 py-12 flex justify-center">

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">

        {/* LEFT */}
        <div className="lg:col-span-2 space-y-6">

          <div className="text-center mb-10">
            <h1 className="text-5xl font-bold mb-5">
              AI Interview Agent
            </h1>

            <p className="text-gray-400">
              Practice technical interviews with AI
            </p>

            <ProgressBar
              current={questionNumber}
              total={TOTAL_QUESTIONS}
            />
          </div>

          {/* ROLE INPUT */}
          <div className="bg-[#111827] p-8 rounded-2xl border border-gray-800">

            <input
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="Data Scientist"
              className="w-full p-4 rounded-xl bg-[#0b1220] border border-gray-700 mb-5"
            />

            <button
              onClick={handleStart}
              className="w-full p-4 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-500"
            >
              {loading ? "Loading..." : "Start Interview"}
            </button>

          </div>

          {/* QUESTION */}
          {questions.length > 0 && (
            <>
              <InterviewCard
                question={questions[questions.length - 1]}
              />

              <QuestionSpeaker
                question={questions[questions.length - 1]}
              />
            </>
          )}

          {/* ANSWER */}
          {questions.length > 0 && (
            <>
              <AnswerBox
                answer={currentAnswer}
                setAnswer={setCurrentAnswer}
                onSubmit={handleEvaluate}
                loading={evalLoading}
              />

              <VoiceRecorder
                onTranscript={(text) => setCurrentAnswer(text)}
              />
            </>
          )}

          {/* EVALUATION */}
          {evaluations.length > 0 && (
            <EvaluationCard
              evaluation={evaluations[evaluations.length - 1]}
            />
          )}

        </div>

        {/* RIGHT SIDEBAR */}
        <div className="space-y-6">

          <HistoryPanel evaluations={evaluations} />
          <Dashboard evaluations={evaluations} />

        {isFinished && (
          <button
            onClick={handleDownload}
            className="w-full p-3 bg-green-600 rounded-xl"
          >
            Download PDF Report
          </button>
        )}

        </div>

      </div>
    </main>
  )
}
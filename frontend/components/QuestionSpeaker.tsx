"use client"

import { useEffect } from "react"

interface QuestionSpeakerProps {
  question: string
}

export default function QuestionSpeaker({
  question,
}: QuestionSpeakerProps) {
  useEffect(() => {
    if (!question) return

    const utterance = new SpeechSynthesisUtterance(question)

    utterance.lang = "en-US"
    utterance.rate = 1
    utterance.pitch = 1

    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)

    return () => {
      window.speechSynthesis.cancel()
    }
  }, [question])

  return null
}
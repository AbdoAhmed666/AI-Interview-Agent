"use client"

import { useState, useRef } from "react"

interface VoiceRecorderProps {
  onTranscript: (text: string) => void
}

export default function VoiceRecorder({
  onTranscript,
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [fullTranscript, setFullTranscript] = useState("")
  const recognitionRef = useRef<any>(null)

  const startRecording = () => {
    console.log("START CLICKED")

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition

    console.log("SpeechRecognition:", SpeechRecognition)

    if (!SpeechRecognition) {
      alert("Speech Recognition NOT supported")
      return
    }

    const recognition = new SpeechRecognition()

    recognition.lang = "en-US"

    // IMPORTANT
    recognition.continuous = true
    recognition.interimResults = true

    recognition.onstart = () => {
      console.log("RECORDING STARTED")
      setIsRecording(true)
    }


    recognition.onresult = (event: any) => {
        let finalTranscript = ""

        for (let i = 0; i < event.results.length; i++) {
            finalTranscript += event.results[i][0].transcript + " "
        }

        console.log("FULL:", finalTranscript)

        setFullTranscript(finalTranscript)

        onTranscript(finalTranscript)
        }
    // recognition.onresult = (event: any) => {
    //   console.log("EVENT:", event)

    //   const transcript =
    //     event.results[event.results.length - 1][0].transcript

    //   console.log("TRANSCRIPT:", transcript)

    //   onTranscript(transcript)
    // }

    recognition.onerror = (event: any) => {
      console.log("ERROR:", event)
      setIsRecording(false)
    }

    recognition.onend = () => {
      console.log("RECORDING ENDED")
      setIsRecording(false)
    }

    recognitionRef.current = recognition

    recognition.start()
  }

  const stopRecording = () => {
    recognitionRef.current?.stop()
  }

  return (
    <div className="flex gap-3 mt-4">
      {!isRecording ? (
        <button
          onClick={startRecording}
          className="bg-blue-600 px-4 py-2 rounded text-white"
        >
          Start Voice Answer
        </button>
      ) : (
        <button
          onClick={stopRecording}
          className="bg-red-600 px-4 py-2 rounded text-white"
        >
          Stop Recording
        </button>
      )}
    </div>
  )
}
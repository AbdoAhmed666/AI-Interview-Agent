// const API_URL = "http://127.0.0.1:8001";

// export async function startInterview(role: string) {
//   const response = await fetch(`${API_URL}/start-interview`, {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//     },
//     body: JSON.stringify({
//       role,
//     }),
//   });

//   if (!response.ok) {
//     throw new Error("Failed to start interview");
//   }

//   return response.json();
// }

// export async function evaluateAnswer(
//   role: string,
//   question: string,
//   answer: string
// ) {
//   const response = await fetch(`${API_URL}/evaluate-answer`, {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//     },
//     body: JSON.stringify({
//       role,
//       question,
//       answer,
//       current_difficulty: 3,
//     }),
//   });

//   if (!response.ok) {
//     throw new Error("Evaluation failed");
//   }

//   return response.json();
// }

const API_URL = "http://127.0.0.1:8001"

export async function startInterview(role: string) {
  const response = await fetch(`${API_URL}/start-interview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      role,
    }),
  })

  if (!response.ok) {
    throw new Error("Failed to start interview")
  }

  return response.json()
}


export async function adaptiveInterview(
  role: string,
  question: string,
  answer: string,
  difficulty: number
) {
  const response = await fetch(`${API_URL}/adaptive-interview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify({
      role,
      question,
      answer,
      current_difficulty: difficulty
    }),
  })

  if (!response.ok) {
    throw new Error("Evaluation failed")
  }

  return response.json()
}

export async function downloadReport(reportData: any) {
  const response = await fetch(
    `${API_URL}/download-report`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(reportData)
    }
  )

  if (!response.ok) {
    throw new Error("PDF failed")
  }

  return response.blob()
}
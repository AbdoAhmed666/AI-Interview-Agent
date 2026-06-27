# AI Interview Agent

Production-grade AI interview simulation platform that dynamically evaluates technical answers using LLMs, adapts interview difficulty in real time, generates hiring recommendations, and produces detailed interview analytics.

---

## Overview

AI Interview Agent is a full-stack AI system designed to simulate real technical interviews for software engineers, data scientists, and technical professionals.

Instead of simply generating interview questions, the system behaves like an adaptive interviewer that:

* Generates role-specific technical questions
* Evaluates candidate answers using Large Language Models
* Measures candidate performance
* Dynamically adjusts question difficulty
* Detects strengths and knowledge gaps
* Generates hiring recommendations
* Produces downloadable PDF interview reports
* Displays interview analytics dashboard

The goal of this project is to build a production-grade AI interviewing platform that mimics real-world technical screening processes.

---

## Core Features

### AI Question Generation

Generate interview questions tailored to a specific role.

Examples:

* Data Scientist
* Backend Engineer
* Machine Learning Engineer
* Frontend Developer

---

### Adaptive Interview Engine

The system dynamically changes question difficulty based on candidate performance.

Difficulty Logic:

* Strong Answer → Increase difficulty
* Weak Answer → Decrease difficulty
* Medium Answer → Keep same difficulty

Difficulty Range:

* Minimum = 1
* Maximum = 5

---

### AI Evaluation Engine

Each answer is evaluated using LLM reasoning.

Evaluation returns structured JSON:

```json
{
  "score": 82,
  "level": "strong",
  "strengths": ["Good understanding of model evaluation"],
  "weaknesses": ["Lacked explanation of overfitting"],
  "feedback": "Solid answer overall",
  "concept_gaps": ["Cross validation"],
  "follow_up_question": "Explain regularization."
}
```

---

### Multi Provider LLM Routing

The system supports multiple AI providers.

Current providers:

* Google Gemini
* Groq LLM API
* Mock Provider (fallback)

Routing Logic:

```text
Try Gemini
      ↓
If quota/rate limit reached
      ↓
Try Groq
      ↓
If failure occurs
      ↓
Fallback to Mock Provider
```

This architecture reduces downtime caused by API quota limitations.

---

### Session Summary Generation

At the end of the interview, the system generates:

* Overall score
* Performance summary
* Hiring recommendation

Possible hiring recommendations:

* Strong Hire
* Hire
* Weak Hire
* Reject

---

### PDF Report Generator

Generate a professional PDF report containing:

* Candidate role
* Final score
* Question-by-question evaluation
* Strengths
* Weaknesses
* Knowledge gaps
* Hiring recommendation

Implemented using ReportLab.

---

### Analytics Dashboard

Interactive dashboard displaying:

* Average Score
* Best Score
* Questions Answered
* Score Distribution
* Performance Trend
* Strength Areas
* Weak Areas

---

## Tech Stack

### Frontend

* Next.js
* TypeScript
* TailwindCSS

### Backend

* FastAPI
* Python
* Pydantic

### AI Layer

* Gemini API
* Groq API

### Reporting

* ReportLab PDF Generator

---

## Project Architecture

```text
                USER
                  │
                  ▼

          Next.js Frontend
                  │
                  ▼

            FastAPI Backend
                  │
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼

 Adaptive Engine        Session Manager
       │                     │
       └──────────┬──────────┘
                  │
                  ▼

          LLM Router Provider
                  │
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼

 Gemini Provider       Groq Provider
       │                     │
       └────Fallback Logic───┘
                  │
                  ▼

        Evaluation Engine
                  │
                  ▼

        PDF Report Generator
```

---

## API Endpoints

### Start Interview

```http
POST /start-interview
```

Generate first interview question.

---

### Adaptive Interview

```http
POST /adaptive-interview
```

Evaluate answer and generate next adaptive question.

---

### Session Summary

```http
POST /summarize-session
```

Generate final interview summary.

---

### Download Report

```http
POST /download-report
```

Generate downloadable PDF report.

---

## Project Structure

```text
AI-Interview-Agent/

backend/
│
├── adaptive_engine.py
├── evaluator.py
├── history.py
├── interview.py
├── llm_provider.py
├── prompts.py
├── schemas.py
├── config.py
└── main.py


frontend/
│
├── app/
│   └── page.tsx
│
├── components/
│   ├── InterviewCard.tsx
│   ├── AnswerBox.tsx
│   ├── EvaluationCard.tsx
│   ├── ProgressBar.tsx
│   ├── HistoryPanel.tsx
│   └── Dashboard.tsx
```

---

## Screenshots

### Home Screen

(Add screenshot)

### Interview Session

(Add screenshot)

### Evaluation Screen

(Add screenshot)

### Analytics Dashboard

(Add screenshot)

---

## Environment Variables

Create .env file

```env
GEMINI_API_KEY=

MODEL_NAME=gemini-2.0-flash

GROQ_API_KEY=

GROQ_MODEL=llama-3.3-70b-versatile

LLM_PROVIDER=router
```

---

## Development Roadmap

### Completed

* AI Question Generation
* Adaptive Interview Logic
* AI Answer Evaluation
* Gemini Provider Integration
* Groq Provider Integration
* Multi Provider Router
* Session Summarization
* PDF Report Generation
* Analytics Dashboard

---

### Phase 2

* Authentication
* Database Integration
* Save Interview History

---

### Phase 3

* Voice Interview Mode
* Speech To Text

---

### Phase 4

* Webcam Analysis
* Facial Emotion Detection

---

### Phase 5

* Cloud Deployment

---

## Why This Project Matters

Most interview bots simply ask random questions.

AI Interview Agent simulates a real technical interviewer by:

* Understanding answer quality
* Measuring candidate level
* Adapting difficulty in real time
* Generating recruiter-like hiring decisions

This project focuses on real AI system design rather than simple chatbot behavior.

---

## Future Vision

The long-term goal is building a fully autonomous AI recruiter capable of:

* Conducting interviews
* Understanding voice responses
* Reading facial expressions
* Detecting confidence and hesitation
* Producing complete hiring decisions

---

## License

MIT License

# AI Interview Agent

Production-grade AI Interview Platform that conducts adaptive technical interviews, evaluates candidates using Large Language Models (LLMs), stores interview history, generates recruiter-style reports, and is being extended with a Personalized Hybrid RAG system for context-aware technical interviews.

---

# Overview

AI Interview Agent is a full-stack AI platform designed to simulate real-world technical interviews for software engineers, machine learning engineers, data scientists, frontend developers, and backend engineers.

Unlike traditional interview bots that simply ask random questions, this platform behaves like an intelligent interviewer capable of:

- Generating role-specific technical questions
- Evaluating answers using LLM reasoning
- Measuring candidate performance
- Adapting interview difficulty in real time
- Detecting strengths and knowledge gaps
- Producing hiring recommendations
- Saving complete interview history
- Generating professional PDF reports
- Displaying interview analytics

The long-term vision is building an AI Technical Assessment Platform capable of conducting personalized interviews grounded in both the candidate's CV and a technical knowledge base using Retrieval-Augmented Generation (RAG).

---

# Architecture

```
                    User
                      │
                      ▼

              Next.js Frontend
                      │
                      ▼

              FastAPI REST API
                      │
              JWT Authentication
                      │
                      ▼

             Interview Engine
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼

 Adaptive Difficulty Engine   Session Manager
         │                         │
         └────────────┬────────────┘
                      │
                      ▼

               LLM Router Layer
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼

   Gemini Provider            Groq Provider
        │                           │
        └──────── Fallback Logic ───┘
                      │
                      ▼

            AI Evaluation Engine
                      │
                      ▼

      PostgreSQL + SQLAlchemy ORM
                      │
                      ▼

          PDF Report Generator
```

---

# Upcoming Architecture (Personalized Hybrid RAG)

```
Candidate CV
        │
        ▼

Knowledge Base (PDF / Markdown)

        │
        ▼

Chunking

        │
        ▼

Embeddings

        │
        ▼

FAISS Vector Store

        │
        ▼

Retriever

        │
        ▼

Context Builder

        │
        ▼

Gemini

        │
        ▼

Context-aware Interview &
Answer Evaluation
```

---

# Core Features

## Authentication

- JWT Authentication
- User Registration
- User Login
- Protected Endpoints
- User Profile

---

## AI Interview Engine

- AI Question Generation
- Role-based Interviews
- Adaptive Difficulty
- Technical Answer Evaluation
- Knowledge Gap Detection
- Strength Detection
- Weakness Detection
- Follow-up Question Generation

---

## Interview Management

- Interview Sessions
- Question History
- Answer Storage
- Difficulty Tracking
- Score Tracking
- Hiring Recommendation

---

## Reports

- Professional PDF Report
- Session Summary
- Recruiter-style Recommendation

---

## Dashboard

- Total Interviews
- Average Score
- Best Score
- Completed Interviews
- Interview History

---

# Adaptive Interview Engine

The interview dynamically adjusts its difficulty according to candidate performance.

### Difficulty Logic

Strong Answer

⬆ Increase Difficulty

Medium Answer

➡ Keep Difficulty

Weak Answer

⬇ Decrease Difficulty

Difficulty ranges from **1 → 5**.

---

# AI Evaluation Example

```json
{
  "score": 8,
  "level": "Strong",
  "strengths": [
    "Good understanding of evaluation metrics"
  ],
  "weaknesses": [
    "Limited discussion of class imbalance"
  ],
  "feedback": "Solid answer with room for deeper analysis.",
  "concept_gaps": [
    "Precision-Recall Curve"
  ],
  "follow_up_question": "Explain ROC-AUC."
}
```

---

# Multi-Provider LLM Routing

The system supports multiple AI providers.

Current providers:

- Google Gemini
- Groq
- Mock Provider (Fallback)

Routing strategy:

```
Gemini

↓

Groq

↓

Mock Provider
```

This architecture minimizes downtime caused by quota limits or provider failures.

---

# Database Schema

## Users

- id
- name
- email
- hashed_password
- is_active
- created_at

---

## Interview Sessions

- id
- user_id
- role
- overall_score
- recommendation
- status
- started_at
- finished_at

---

## Interview Questions

- id
- session_id
- question
- answer
- score
- feedback
- difficulty

---

# REST API

## Authentication

```
POST /register

POST /login

GET /me
```

## Interview

```
POST /start-interview

POST /adaptive-interview

POST /finish-interview

POST /summarize-session
```

## Reports

```
POST /download-report
```

## History

```
GET /my-sessions

GET /session/{id}
```

---

# Tech Stack

## Frontend

- Next.js 16
- React
- TypeScript
- TailwindCSS
- Axios
- Context API

---

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic

---

## Authentication

- JWT
- OAuth2

---

## AI

- Google Gemini
- Groq
- Prompt Engineering
- Adaptive Difficulty Engine

---

## Reporting

- ReportLab

---

## Development

- Git
- GitHub

---

## Upcoming AI Stack

- Personalized Hybrid RAG
- FAISS
- Sentence Transformers
- LangChain

---

# Project Structure

```
AI-Interview-Agent/

backend/
│
├── adaptive_engine.py
├── auth.py
├── config.py
├── crud.py
├── database.py
├── evaluator.py
├── interview.py
├── llm_provider.py
├── models.py
├── prompts.py
├── schemas.py
├── security.py
├── main.py
│
├── alembic/
│
└── migrations/

frontend/
│
├── app/
├── components/
├── contexts/
├── hooks/
├── services/
├── lib/
└── public/

assets/

README.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Interview-Agent.git

cd AI-Interview-Agent
```

---

## Backend

```bash
cd backend

python -m venv .venv

source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# Environment Variables

```
DATABASE_URL=

SECRET_KEY=

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60

GEMINI_API_KEY=

MODEL_NAME=gemini-2.5-flash

GROQ_API_KEY=

GROQ_MODEL=llama-3.3-70b-versatile

LLM_PROVIDER=router
```

---

# Screenshots

- Home
- Login
- Register
- Dashboard
- Interview
- AI Evaluation
- History
- Profile
- PDF Report

(Add screenshots here)

---

# Development Roadmap

## Completed

- AI Question Generation
- Adaptive Difficulty Engine
- AI Evaluation Engine
- Gemini Integration
- Groq Integration
- Multi-Provider Router
- Authentication
- JWT
- PostgreSQL
- SQLAlchemy
- Alembic
- Interview History
- Dashboard
- PDF Report
- Session Summary

---

## In Progress

- Personalized Hybrid RAG
- Knowledge Base
- FAISS Vector Database
- Embeddings
- Retriever
- Context Builder
- CV Upload
- Resume Understanding

---

## Planned

- Voice Interview
- Speech-to-Text
- Text-to-Speech
- Webcam Interview
- Facial Emotion Detection
- Recruiter Dashboard
- Cloud Deployment

---

# Why This Project Is Different

Most interview bots simply ask predefined questions.

AI Interview Agent behaves like a real technical interviewer by:

- Understanding answer quality
- Measuring candidate knowledge
- Adapting interview difficulty
- Detecting strengths and weaknesses
- Identifying knowledge gaps
- Generating recruiter-style hiring recommendations
- Storing interview history
- Producing professional reports

The next evolution of the platform introduces **Personalized Hybrid RAG**, allowing interview generation and answer evaluation to be grounded in both the candidate's CV and a curated technical knowledge base, resulting in highly personalized and fact-based assessments.

---

# Future Vision

The goal is to evolve this project into a complete AI Technical Assessment Platform capable of:

- Personalized Hybrid RAG
- CV Understanding
- Context-aware Question Generation
- Context-aware Answer Evaluation
- Resume Parsing
- Voice Interviews
- AI Recruiter Dashboard
- Multi-language Interviews
- Cloud Deployment

---

# License

MIT License

---

Built with ❤️ using

- FastAPI
- Next.js
- PostgreSQL
- SQLAlchemy
- Gemini
- Groq
- ReportLab
- TypeScript

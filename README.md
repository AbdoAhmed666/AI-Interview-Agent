# AI Interview Agent


> **An AI-powered technical interview platform that conducts adaptive, personalized interviews using candidate CV analysis, role matching, Retrieval-Augmented Generation (RAG), multi-provider LLM routing, and recruiter-style evaluation.**


AI Interview Agent is a full-stack AI assessment platform designed to simulate a real technical interview rather than a static question-and-answer chatbot.


The platform analyzes a candidate's CV, determines role suitability, retrieves relevant technical knowledge, generates role-specific interview questions, evaluates answers using LLMs, adapts interview difficulty based on performance, and stores the complete interview history.


The system is built with **FastAPI, Next.js, PostgreSQL, Gemini, Groq, FAISS, Sentence Transformers, and JWT authentication**.


---


## 🚀 Why AI Interview Agent?


Traditional interview bots often follow a fixed sequence of predefined questions.


This project takes a different approach.


The interviewer dynamically uses:


- Candidate CV information
- Selected technical role
- Role requirements
- Technical knowledge base
- Previous answers
- Previous evaluation results
- Candidate strengths and weaknesses
- Current interview difficulty


to create a more realistic and personalized technical assessment.


### The result


Instead of:


> Question → Answer → Next Question


the platform follows:


> **CV → Role Analysis → Knowledge Retrieval → Personalized Question → Answer Evaluation → Difficulty Adaptation → Next Question → Final Assessment**


---


# ✨ Key Capabilities


## 🤖 AI-Powered Technical Interviews


The platform can conduct technical interviews for roles such as:


- Machine Learning Engineer
- Data Scientist
- Backend Developer
- Frontend Developer
- Software Engineer


The interview engine generates technical questions dynamically instead of relying exclusively on a predefined question list.


---


## 📄 CV Upload & Analysis


Candidates can upload their CV directly from their profile.


The system:


1. Accepts the candidate CV
2. Extracts the document content
3. Analyzes candidate information
4. Identifies technical skills and experience
5. Matches the candidate against supported roles
6. Determines role eligibility
7. Uses the CV as personalized interview context


The CV is also integrated into the RAG pipeline so interview questions can be grounded in the candidate's actual background.


### Example


A candidate with experience in:


```text
Python
TensorFlow
PyTorch
Machine Learning
FastAPI
Docker

can receive questions that are relevant to their actual technical background rather than completely generic questions.

🧠 Personalized Hybrid RAG

One of the core AI engineering components of the platform is the Personalized Hybrid RAG pipeline.

The system combines:

Candidate Context
CV content
Candidate skills
Candidate experience
Role matching results
Technical Knowledge
Curated technical documentation
Role-specific knowledge
Backend concepts
Machine Learning concepts
Technical interview material

The pipeline is:

                  Candidate CV
                       │
                       ▼
                 PDF Extraction
                       │
                       ▼
                    Chunking
                       │
                       ▼
                  Embeddings
                       │
                       ▼
                 FAISS Vector DB
                       │
                       │
Technical Knowledge ──┘
                       │
                       ▼
                    Retriever
                       │
                       ▼
                 Context Builder
                       │
                       ▼
                Query / Prompt Builder
                       │
                       ▼
                     LLM
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Interview Question   Answer Evaluation

This allows the system to ground AI-generated content in retrieved information rather than relying only on the model's general knowledge.

🎯 Role Matching & Eligibility

Before starting an interview, the system analyzes whether the candidate's CV is suitable for the selected role.

The platform supports role-aware matching and eligibility decisions.

For example:

Candidate CV
     │
     ▼
Skill Extraction
     │
     ▼
Role Matching
     │
     ▼
Eligibility Check
     │
     ├── Eligible → Start Interview
     │
     └── Not Eligible → Reject Role

This prevents the interview from blindly starting when the candidate's profile does not sufficiently match the selected role.

🎤 Adaptive Interview Engine

The interview is not static.

After every answer, the AI evaluates the candidate and uses the result to determine the next difficulty level.

Difficulty Logic
             Candidate Answer
                    │
                    ▼
              AI Evaluation
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      Strong      Medium       Weak
        │           │           │
        ▼           ▼           ▼
    Increase      Maintain    Decrease
    Difficulty    Difficulty  Difficulty

Difficulty is controlled across levels:

1 → 2 → 3 → 4 → 5

This creates a more realistic interview experience where the interview adjusts to the candidate's demonstrated knowledge.

📊 AI Answer Evaluation

Each candidate answer is evaluated by the AI.

The evaluation can include:

Score
Performance level
Strengths
Weaknesses
Feedback
Knowledge gaps
Follow-up questions

Example evaluation:

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

This transforms raw answers into structured candidate insights.

🔄 Multi-Provider LLM Architecture

The system was designed with an LLM provider abstraction instead of tightly coupling the application to one model provider.

Supported providers include:

Google Gemini
Groq
Mock Provider

The routing architecture follows:

                LLM Router
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       Gemini                Groq
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
              Mock Fallback

This makes the application more resilient to provider availability and quota limitations.

🔐 Authentication & Security

The application includes authentication and protected application flows.

Implemented capabilities include:

User registration
User login
JWT authentication
Protected endpoints
Authenticated user context
User-specific interview history
User-specific CV storage
Centralized frontend token handling
Automatic handling of unauthorized sessions

Sensitive runtime data and credentials are excluded from version control.

👤 User Profile

Each authenticated candidate has a dedicated profile area.

The profile supports:

Candidate information
CV upload
CV processing
CV analysis
Role matching
Personalized interview preparation

The system also prevents a failed CV processing attempt from immediately replacing a previously valid active CV.

📚 Technical Knowledge Base

The platform includes a structured technical knowledge base.

Current knowledge content includes technical documentation such as:

backend/
├── docker.md
├── fastapi.md
└── jwt.md

The knowledge base is indexed and consumed by the RAG pipeline to provide technical context during interview generation and evaluation.

🗂️ Interview History

Every completed interview is associated with the authenticated candidate.

The platform stores and displays:

Interview role
Interview status
Overall score
Recommendation
Interview questions
Candidate answers
Individual question scores
Feedback
Difficulty progression
Session information

Candidates can review previous interviews through the history interface.

📄 Recruiter-Style Reports

The platform can generate professional interview reports containing structured assessment information.

Reports are designed around recruiter-friendly insights such as:

Overall candidate performance
Technical evaluation
Strengths
Weaknesses
Knowledge gaps
Recommendation
Interview summary

The goal is to convert a conversational interview into structured assessment data.

📈 Dashboard & Analytics

The dashboard provides an overview of candidate interview performance.

It includes metrics such as:

Total interviews
Average score
Best score
Completed interviews
Interview history

This gives candidates a centralized view of their interview performance over time.

🏗️ System Architecture
                              ┌─────────────────────┐
                              │       Candidate     │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   Next.js Frontend  │
                              │ React + TypeScript  │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │     FastAPI API     │
                              └──────────┬──────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
             Authentication         CV System          Interview Engine
                 JWT                    │                    │
                                      ▼                    ▼
                                CV Analysis           Adaptive Engine
                                      │                    │
                                      ▼                    ▼
                                Role Matching         LLM Router
                                      │                    │
                                      └──────────┬─────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │    RAG Pipeline     │
                                      │                     │
                                      │ CV + Knowledge Base │
                                      │       ↓             │
                                      │    Chunking         │
                                      │       ↓             │
                                      │   Embeddings        │
                                      │       ↓             │
                                      │     FAISS           │
                                      │       ↓             │
                                      │    Retrieval        │
                                      └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │      LLM Layer      │
                                      │                     │
                                      │ Gemini / Groq       │
                                      └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │ AI Evaluation Engine │
                                      └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │ PostgreSQL Database  │
                                      └──────────┬──────────┘
                                                 │
                              ┌──────────────────┴──────────────┐
                              ▼                                 ▼
                       Interview History                 PDF Reports
🧩 Core Application Flow

The complete candidate journey is:

Register
   ↓
Login
   ↓
Profile
   ↓
Upload CV
   ↓
Analyze CV
   ↓
Select Technical Role
   ↓
Role Eligibility Check
   ↓
Start Interview
   ↓
Generate Question
   ↓
Candidate Answers
   ↓
AI Evaluation
   ↓
Adaptive Difficulty
   ↓
Next Question
   ↓
Interview Completion
   ↓
Session Summary
   ↓
Score + Recommendation
   ↓
Interview History
   ↓
Detailed Report
🛠️ Technology Stack
Frontend
Next.js 16
React
TypeScript
Tailwind CSS
Axios
Context API
Backend
Python
FastAPI
SQLAlchemy
Pydantic
Alembic
PostgreSQL
AI / LLM
Google Gemini
Groq
LLM Provider Abstraction
Prompt Engineering
Adaptive Interview Logic
Structured AI Evaluation
RAG
FAISS
Sentence Transformers
LangChain Text Splitters
Custom Retrieval Pipeline
CV-based Retrieval
Knowledge Base Retrieval
Document Processing
PDF parsing
CV text extraction
Document chunking
Embedding generation
Authentication
JWT
OAuth2
Password hashing
Protected API routes
Reporting
ReportLab
PDF report generation
Development
Git
GitHub
REST APIs
Environment-based configuration
📁 Project Structure
AI-Interview-Agent/
│
├── backend/
│   │
│   ├── api/
│   │   ├── cv.py
│   │   ├── history.py
│   │   └── interview.py
│   │
│   ├── cv/
│   │   ├── analyzer.py
│   │   ├── eligibility.py
│   │   ├── matcher.py
│   │   ├── role_matcher.py
│   │   ├── role_profiles.py
│   │   ├── role_recommender.py
│   │   └── storage.py
│   │
│   ├── interview/
│   │   ├── interview_manager.py
│   │   └── models.py
│   │
│   ├── rag/
│   │   ├── chunker.py
│   │   ├── config.py
│   │   ├── embeddings.py
│   │   ├── loader.py
│   │   ├── models.py
│   │   ├── parser.py
│   │   ├── prompt_builder.py
│   │   ├── query_builder.py
│   │   ├── retriever.py
│   │   ├── role_matcher.py
│   │   ├── rag_service.py
│   │   └── vector_store.py
│   │
│   ├── services/
│   │   ├── cv_service.py
│   │   ├── interview_service.py
│   │   └── main.py
│   │
│   ├── knowledge_base/
│   │   └── backend/
│   │       ├── docker.md
│   │       ├── fastapi.md
│   │       └── jwt.md
│   │
│   ├── evaluator.py
│   ├── main.py
│   ├── schemas.py
│   ├── config.py
│   └── ...
│
├── frontend/
│   │
│   ├── app/
│   │   ├── dashboard/
│   │   ├── history/
│   │   ├── interview/
│   │   ├── profile/
│   │   └── ...
│   │
│   ├── components/
│   ├── contexts/
│   ├── hooks/
│   ├── services/
│   └── lib/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── package.json
├── README.md
└── LICENSE
🔌 REST API
Authentication
POST /register
POST /login
GET  /me
CV
POST /cv/upload
GET  /cv
Interview
POST /start-interview
POST /adaptive-interview
POST /finish-interview
POST /summarize-session
History
GET /my-sessions
GET /session/{id}
Reports
POST /download-report
⚙️ Installation
1. Clone the repository
git clone https://github.com/AbdoAhmed666/AI-Interview-Agent.git


cd AI-Interview-Agent
2. Backend Setup
cd backend


python -m venv .venv
Windows
.venv\Scripts\activate
Linux / macOS
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run the API:

uvicorn main:app --reload

The backend will be available at:

http://localhost:8000

FastAPI documentation:

http://localhost:8000/docs
3. Frontend Setup

Open another terminal:

cd frontend


npm install


npm run dev

The frontend will be available at:

http://localhost:3000
🔐 Environment Configuration

Create a .env file based on .env.example.

DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/ai_interview_agent


SECRET_KEY=replace_with_a_long_random_secret


ALGORITHM=HS256


ACCESS_TOKEN_EXPIRE_MINUTES=60


GEMINI_API_KEY=your_gemini_api_key


MODEL_NAME=gemini-2.0-flash


GROQ_API_KEY=your_groq_api_key


GROQ_MODEL=llama-3.3-70b-versatile


LLM_PROVIDER=router

Never commit real API keys, database passwords, JWT secrets, CVs, generated indexes, or runtime user data to GitHub.

🧪 Testing

The repository includes backend tests covering important application components, including:

CV analysis
CV storage
CV indexing
Role eligibility
Role matching
Role recommendation
Interview flow
RAG service
Vector store
Retrieval pipeline

Example:

pytest
🔒 Runtime Data & Privacy

User-generated and machine-generated runtime artifacts are intentionally excluded from version control.

The repository ignores:

.env
.runtime/
uploads/
temporary files
generated FAISS indexes
generated metadata
local history data
test artifacts
debug scripts
temporary JSON files

This keeps the GitHub repository clean and prevents accidental exposure of candidate data or secrets.

📊 Engineering Highlights

This project demonstrates practical experience across multiple areas of modern AI engineering.

AI Engineering
LLM-powered question generation
Structured LLM evaluation
Multi-provider LLM routing
Adaptive reasoning workflow
Prompt engineering
Context-aware generation
RAG Engineering
Document parsing
Intelligent chunking
Embedding generation
FAISS vector indexing
Semantic retrieval
Context construction
Candidate-specific retrieval
Backend Engineering
FastAPI REST architecture
Service-layer separation
Pydantic schemas
SQLAlchemy ORM
PostgreSQL
Alembic migrations
JWT authentication
Protected endpoints
Frontend Engineering
Next.js App Router
TypeScript
Component-based architecture
Authentication context
API service layer
Axios interceptors
Protected application shell
Interview state management
Software Engineering
Environment-based configuration
Runtime data isolation
Git/GitHub workflow
Modular architecture
Testable services
Separation of concerns
Error handling
Provider abstraction
💡 Key Engineering Decisions
Provider Abstraction

Instead of embedding a specific LLM provider throughout the application, the project uses an abstraction layer that allows providers to be switched or routed.

This makes the AI layer easier to maintain and extend.

Personalized Context

Interview questions are not generated independently from the candidate.

The platform combines:

Candidate
   +
CV
   +
Selected Role
   +
Technical Knowledge
   +
Previous Performance

to generate a more personalized assessment.

Adaptive Difficulty

The interview engine uses evaluation results to dynamically control question difficulty.

This avoids a one-size-fits-all interview experience.

User-Specific Data Isolation

CVs and generated retrieval artifacts are organized around the authenticated user instead of being treated as globally shared runtime files.

This is important for a multi-user interview platform.

📸 Application Screenshots

The application includes interfaces for:

Landing Page
Authentication
Dashboard
Profile
CV Upload
CV Analysis
Role Selection
Technical Interview
AI Evaluation
Interview History
Interview Details
PDF Report

Screenshots can be added here:

docs/
└── screenshots/
    ├── home.png
    ├── login.png
    ├── dashboard.png
    ├── profile.png
    ├── cv-analysis.png
    ├── interview.png
    ├── evaluation.png
    ├── history.png
    └── report.png
🗺️ Roadmap
✅ Implemented
 User Registration
 User Login
 JWT Authentication
 Protected API Endpoints
 User Profile
 CV Upload
 CV Text Extraction
 CV Analysis
 Role Matching
 Role Eligibility
 Role Recommendation
 Personalized Interview Flow
 AI Question Generation
 Technical Answer Evaluation
 Adaptive Difficulty
 Strength Detection
 Weakness Detection
 Knowledge Gap Detection
 Follow-up Question Generation
 Gemini Integration
 Groq Integration
 LLM Provider Routing
 Mock LLM Fallback
 PostgreSQL Persistence
 SQLAlchemy ORM
 Alembic
 Interview History
 Detailed Interview View
 Dashboard Analytics
 PDF Reports
 Knowledge Base
 FAISS Vector Store
 Sentence Transformer Embeddings
 RAG Retrieval
 Context-Aware Prompt Construction
 User-specific CV/index runtime storage
 Runtime data protection through .gitignore
 Centralized frontend authentication handling
🚧 Next Improvements
 UI/UX refinement
 Expanded technical knowledge base
 More role profiles
 Improved evaluation consistency
 Automated end-to-end testing
 Production deployment
 Observability and logging
 Evaluation benchmarks for RAG quality
 LLM cost/latency monitoring
🔮 Future Vision

The long-term goal is to evolve AI Interview Agent into a complete AI technical assessment platform.

Potential future capabilities include:

🎙️ Real-time voice interviews
🗣️ Speech-to-text
🔊 Text-to-speech
📹 Video interview support
👨‍💼 Recruiter dashboard
🌍 Multi-language interviews
☁️ Cloud deployment
📊 Advanced candidate analytics
🧪 Automated interview benchmarking
🔍 Explainable candidate evaluation
🎯 What This Project Demonstrates

AI Interview Agent is more than a chatbot.

It demonstrates the ability to design and implement a complete AI product across the full stack:

Frontend
   ↓
REST API
   ↓
Authentication
   ↓
Business Logic
   ↓
CV Intelligence
   ↓
RAG Pipeline
   ↓
LLM Infrastructure
   ↓
AI Evaluation
   ↓
Adaptive Decision Making
   ↓
Database
   ↓
Reports & Analytics

The project combines AI engineering, backend engineering, RAG, LLM integration, authentication, database design, frontend development, and software architecture into one end-to-end application.

👨‍💻 Author

Abdelrhman Ahmed

AI Engineer | Machine Learning | LLMs | RAG | FastAPI | Python

GitHub:

https://github.com/AbdoAhmed666

📄 License

This project is licensed under the MIT License.

Built With

Python · FastAPI · Next.js · React · TypeScript · PostgreSQL · SQLAlchemy · Gemini · Groq · FAISS · Sentence Transformers · LangChain · ReportLab · JWT

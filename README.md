# 🤖 AI Interview Agent

An AI-powered interview preparation platform that simulates technical and behavioral interviews, evaluates answers using Large Language Models (LLMs), generates detailed feedback, and provides analytics dashboards for performance tracking.

---

## 🚀 Features

### 🎯 AI Interview Simulation

Generate role-specific interview questions for positions such as:

* Data Scientist
* Data Analyst
* Machine Learning Engineer
* Software Engineer
* Product Analyst
* Any custom role

---

### 📝 Intelligent Answer Evaluation

For every answer submitted, the system provides:

* Interview score
* Strengths
* Weaknesses
* Improvement suggestions
* Detailed feedback

---

### 📊 Interview Analytics Dashboard

Track interview performance over time:

* Total interviews completed
* Average score
* Highest score
* Lowest score
* Historical score trends
* Role-based performance analysis

---

### 🔄 Multi-Question Interview Sessions

The platform supports complete interview sessions:

1. Generate interview questions
2. Answer each question
3. Receive evaluation
4. Generate final summary
5. Store results for analytics

---

### 📈 Session Summary

At the end of every interview session:

* Overall score
* Overall strengths
* Overall weaknesses
* Hiring recommendation

---

## 🏗️ System Architecture

```text
Frontend (Streamlit)
        │
        ▼
FastAPI Backend
        │
        ▼
LLM Provider
        │
        ▼
Evaluation Engine
        │
        ▼
History Storage & Analytics
```

---

## 📂 Project Structure

```text
AI-INTERVIEW-AGENT/
│
├── backend/
│   ├── analytics.py
│   ├── config.py
│   ├── evaluator.py
│   ├── history.py
│   ├── interview.py
│   ├── llm_provider.py
│   ├── main.py
│   ├── prompts.py
│   └── schemas.py
│
├── frontend/
│   └── app.py
│
├── data/
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Technologies Used

### Backend

* FastAPI
* Pydantic
* Python

### Frontend

* Streamlit

### AI

* Large Language Models (LLMs)
* Prompt Engineering

### Data Processing

* Pandas

### Storage

* CSV-based history tracking

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/AI-Interview-Agent.git

cd AI-Interview-Agent
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

Add your API key inside:

```env
OPENAI_API_KEY=your_api_key_here
```

---

## ▶️ Running the Backend

```bash
python -m uvicorn backend.main:app --reload --port 8001
```

Backend:

```text
http://127.0.0.1:8001
```

---

## ▶️ Running the Frontend

```bash
streamlit run frontend/app.py
```

Frontend:

```text
http://localhost:8501
```

---

## 📸 Screenshots

### Interview Session

![images](image.png)
![images](image2.png)
---

### Answer Evaluation

Add screenshot here

---

### Analytics Dashboard

![images](analytics1.png)
![images](analytics2.png)

---

## 📌 Future Improvements

* PDF report generation
* Skill breakdown analytics
* SQLite database integration
* User authentication
* Interview difficulty levels
* Deployment to cloud platforms
* Advanced visual analytics

---

## 🎯 Project Goals

This project was built to:

* Practice AI application development
* Build production-like FastAPI services
* Create interactive Streamlit interfaces
* Explore LLM-based evaluation systems
* Track interview performance through analytics

---

## 👨‍💻 Author

Abdelrhman Ahmed

GitHub: https://github.com/AbdoAhmed666

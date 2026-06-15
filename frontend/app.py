"""Streamlit front-end entry point for the AI Interview Agent project.

This file contains the UI and API calls for the interview flow.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import pandas as pd
import requests
import streamlit as st

from backend.analytics import get_history_metrics, load_history_dataframe


API_BASE_URL = "http://127.0.0.1:8001"

START_URL = f"{API_BASE_URL}/start-interview"
EVALUATE_URL = f"{API_BASE_URL}/evaluate-answer"
SUMMARY_URL = f"{API_BASE_URL}/summarize-session"
REPORT_URL = f"{API_BASE_URL}/download-report"

st.set_page_config(page_title="AI Interview Agent", page_icon="🤖")

page = st.sidebar.radio("Navigation", ["Interview", "Analytics"])

if page == "Analytics":
    st.title("Analytics Dashboard")
    st.write("Review interview history stored in the local CSV file.")

    history = load_history_dataframe()

    if history.empty:
        st.info("No interview history available.")
    else:
        metrics = get_history_metrics(history)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Interviews", metrics["total_interviews"])
        col2.metric("Average Score", f"{metrics['average_score']:.1f}")
        col3.metric("Highest Score", metrics["highest_score"])
        col4.metric("Lowest Score", metrics["lowest_score"])

        st.subheader("Interview Scores History")
        score_history = history[["timestamp", "overall_score"]].copy()
        score_history = score_history.dropna(subset=["overall_score"])
        score_history["Interview"] = range(1, len(score_history) + 1)
        st.line_chart(score_history.set_index("Interview")["overall_score"])

        st.subheader("Average Score by Role")
        role_scores = history.groupby("role", dropna=False)["overall_score"].mean().reset_index()
        if not role_scores.empty:
            st.bar_chart(role_scores.set_index("role")["overall_score"])
        else:
            st.info("No role-based score data available.")

        st.subheader("Recent History")
        st.dataframe(history, use_container_width=True)

    st.stop()

st.title("AI Interview Agent")
st.write("Generate a question, answer it, and get a structured evaluation.")

if "question" not in st.session_state:
    st.session_state.question = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "session_started" not in st.session_state:
    st.session_state.session_started = False
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = []
if "evaluations" not in st.session_state:
    st.session_state.evaluations = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "final_summary" not in st.session_state:
    st.session_state.final_summary = None

role = st.text_input("Job role", value=st.session_state.role, placeholder="e.g. Data Scientist")

if st.button("Start Full Interview Session"):
    if not role.strip():
        st.warning("Please enter a job role before starting.")
    else:
        with st.spinner("Generating 5 interview questions..."):
            questions = []
            for _ in range(5):
                response = requests.post(START_URL, json={"role": role}, timeout=30)
                if not response.ok:
                    st.error("Failed to generate the interview questions.")
                    st.write(response.text)
                    break
                questions.append(response.json().get("question", ""))

        if len(questions) == 5:
            st.session_state.role = role
            st.session_state.questions = questions
            st.session_state.answers = [""] * 5
            st.session_state.evaluations = [None] * 5
            st.session_state.current_question_index = 0
            st.session_state.session_started = True
            st.session_state.final_summary = None
            st.success("Interview session ready.")

if st.session_state.session_started and st.session_state.questions:
    total_questions = len(st.session_state.questions)
    index = st.session_state.current_question_index
    progress = (index + 1) / total_questions

    st.subheader(f"Question {index + 1} of {total_questions}")
    st.progress(progress)
    st.write(f"Progress: {int(progress * 100)}%")
    st.write(st.session_state.questions[index])

    answer = st.text_area("Your answer", value=st.session_state.answers[index], height=150, placeholder="Type your response here...")
    st.session_state.answers[index] = answer

    if st.button("Evaluate Answer"):
        if not answer.strip():
            st.warning("Please provide an answer before evaluating.")
        else:
            with st.spinner("Evaluating your answer..."):
                response = requests.post(
                    EVALUATE_URL,
                    json={
                        "role": st.session_state.role,
                        "question": st.session_state.questions[index],
                        "answer": answer,
                    },
                    timeout=60,
                )

            if response.ok:
                evaluation = response.json()
                st.session_state.evaluations[index] = evaluation
                st.session_state.evaluation = evaluation
                st.success("Evaluation received.")
                st.metric("Score", f"{evaluation.get('score', 0)}/10")

                st.subheader("Strengths")
                for item in evaluation.get("strengths", []):
                    st.write("- " + item)
                st.subheader("Weaknesses")
                for item in evaluation.get("weaknesses", []):
                    st.write("- " + item)
                st.subheader("Feedback")
                st.write(evaluation.get("feedback", "No feedback returned."))

                if index < total_questions - 1:
                    st.session_state.current_question_index += 1
                    st.rerun()
                else:
                    with st.spinner("Generating final summary..."):
                        summary_response = requests.post(
                            SUMMARY_URL,
                            json={
                                "role": st.session_state.role,
                                "questions": st.session_state.questions,
                                "answers": st.session_state.answers,
                                "evaluations": st.session_state.evaluations,
                            },
                            timeout=60,
                        )

                    if summary_response.ok:
                        st.session_state.final_summary = summary_response.json()
                        st.success("Final summary generated.")
                        st.subheader("Final Summary")
                        st.metric("Overall Score", f"{st.session_state.final_summary.get('overall_score', 0)}/10")
                        st.subheader("Overall Strengths")
                        for item in st.session_state.final_summary.get("overall_strengths", []):
                            st.write("- " + item)
                        st.subheader("Overall Weaknesses")
                        for item in st.session_state.final_summary.get("overall_weaknesses", []):
                            st.write("- " + item)
                        st.subheader("Hiring Recommendation")
                        st.write(st.session_state.final_summary.get("hiring_recommendation", "No recommendation returned."))
                    else:
                        st.error("Failed to generate the final summary.")
                        st.write(summary_response.text)
            else:
                st.error("Evaluation failed.")
                st.write(response.text)

if st.session_state.final_summary:
    st.divider()
    st.subheader("Session Summary")
    st.write("All five questions and evaluations were used to generate this result.")

  "use client";

  import AppShell from "@/components/layout/AppShell";

  import RoleSelector from "@/components/interview/RoleSelector";
  import QuestionCard from "@/components/interview/QuestionCard";
  import AnswerEditor from "@/components/interview/AnswerEditor";
  import EvaluationPanel from "@/components/interview/EvaluationPanel";
  import InterviewToolbar from "@/components/interview/InterviewToolbar";
  import ProgressBar from "@/components/interview/ProgressBar";

  export default function InterviewPage() {
    return (
      <AppShell>

        <div className="space-y-6">

          <InterviewToolbar />

          <ProgressBar />

          <RoleSelector />

          <QuestionCard />

          <AnswerEditor />

          <EvaluationPanel />

        </div>

      </AppShell>
    );
  }
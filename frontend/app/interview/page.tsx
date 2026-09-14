  "use client";

  import AppShell from "@/components/layout/AppShell";
  import { useAuth } from "@/contexts/AuthContext";
  import { useInterview } from "@/contexts/InterviewContext";
  import { useEffect } from "react";
  import { useRouter } from "next/navigation";

  import RoleSelector from "@/components/interview/RoleSelector";
  import QuestionCard from "@/components/interview/QuestionCard";
  import AnswerEditor from "@/components/interview/AnswerEditor";
  import EvaluationPanel from "@/components/interview/EvaluationPanel";
  import ResultPanel from "@/components/interview/ResultPanel";
  import InterviewToolbar from "@/components/interview/InterviewToolbar";
  import ProgressBar from "@/components/interview/ProgressBar";

  export default function InterviewPage() {
    const { loading, isAuthenticated } = useAuth();
    const { resume } = useInterview();
    const router = useRouter();

    useEffect(() => {
      if (!loading && !isAuthenticated) {
        router.replace("/login");
      }
    }, [loading, isAuthenticated, router]);

    // A reload drops the interview from React state while the session is still
    // open in the database, so pick it back up. `resume` no-ops when this tab
    // already has an interview loaded or has tried once.
    useEffect(() => {
      if (!loading && isAuthenticated) {
        resume();
      }
      // `resume` is recreated on every render but guards itself internally.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, isAuthenticated]);
    return (
      <AppShell>

        <div className="space-y-6">

          <InterviewToolbar />

          <ProgressBar />

          <ResultPanel />

          <RoleSelector />

          <QuestionCard />

          <AnswerEditor />

          <EvaluationPanel />

        </div>

      </AppShell>
    );
  }
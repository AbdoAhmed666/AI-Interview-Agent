  "use client";

  import AppShell from "@/components/layout/AppShell";
  import { useAuth } from "@/contexts/AuthContext";
  import { useEffect } from "react";
  import { useRouter } from "next/navigation";

  import RoleSelector from "@/components/interview/RoleSelector";
  import QuestionCard from "@/components/interview/QuestionCard";
  import AnswerEditor from "@/components/interview/AnswerEditor";
  import EvaluationPanel from "@/components/interview/EvaluationPanel";
  import InterviewToolbar from "@/components/interview/InterviewToolbar";
  import ProgressBar from "@/components/interview/ProgressBar";

  export default function InterviewPage() {
    const { loading, isAuthenticated } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!loading && !isAuthenticated) {
        router.replace("/login");
      }
    }, [loading, isAuthenticated, router]);
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
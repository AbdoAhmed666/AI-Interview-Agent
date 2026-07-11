"use client";

import {
  createContext,
  useContext,
  ReactNode,
} from "react";

import useInterviewHook from "@/hooks/useInterview";

type InterviewContextType =
  ReturnType<typeof useInterviewHook>;

const InterviewContext =
  createContext<InterviewContextType | null>(null);

export function InterviewProvider({
  children,
}: {
  children: ReactNode;
}) {

  const interview = useInterviewHook();

  return (
    <InterviewContext.Provider value={interview}>
      {children}
    </InterviewContext.Provider>
  );
}

export function useInterview() {

  const context = useContext(InterviewContext);

  if (!context) {
    throw new Error(
      "useInterview must be used inside InterviewProvider"
    );
  }

  return context;
}
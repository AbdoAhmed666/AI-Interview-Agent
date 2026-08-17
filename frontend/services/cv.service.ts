import api from "@/lib/axios";

export async function getMyCV() {
  const { data } = await api.get("/cv");
  return data;
}

export async function getCVAnalysis() {
  const { data } = await api.get("/cv/analysis");
  return data;
}

import api from "@/lib/axios";

export async function getMySessions() {
  const { data } = await api.get("/my-sessions");
  return data;
}

export async function getSession(id: number) {
  const { data } = await api.get(`/session/${id}`);
  return data;
}
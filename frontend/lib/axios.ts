import axios from "axios";

import { getToken, removeToken } from "@/utils/token";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
  // Do not set a global Content-Type header here because some requests
  // (e.g. file uploads using FormData) rely on the browser/axios to
  // set the correct multipart boundary. Setting a global
  // `Content-Type: application/json` breaks multipart uploads.
});

api.interceptors.request.use((config) => {

  const token = getToken();

  if (token) {

    config.headers.Authorization = `Bearer ${token}`;

  }

  return config;

});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      removeToken();

      if (!["/login", "/register"].includes(window.location.pathname)) {
        window.location.assign("/login");
      }
    }

    return Promise.reject(error);
  }
);

export default api;

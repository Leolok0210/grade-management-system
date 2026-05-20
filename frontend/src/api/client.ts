import axios from "axios";
import type { LoginRequest, TokenResponse, ChatRequest, ChatResponse, ConversationItem, ConversationDetail } from "../types";

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post<TokenResponse>(
            `${api.defaults.baseURL}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (data: LoginRequest) => api.post<TokenResponse>("/auth/login", data),
  refresh: (refresh_token: string) =>
    api.post<TokenResponse>("/auth/refresh", { refresh_token }),
};

// Chat API
export const chatApi = {
  sendMessage: (data: ChatRequest) => api.post<ChatResponse>("/chat/message", data),
  getConversations: () => api.get<ConversationItem[]>("/chat/conversations"),
  getConversation: (id: number) => api.get<ConversationDetail>(`/chat/conversations/${id}`),
  system: {
    getConfig: () => api.get<{ welcome_hints: string[] }>("/system/config"),
  },
};

// Resources API
export const resourcesApi = {
  getClasses: () => api.get("/students/classes"),
  getStudents: (classId?: string) =>
    api.get("/students", { params: { class_id: classId } }),
  getSubjects: () => api.get("/subjects"),
  getMe: () => api.get("/users/me"),
};

export default api;
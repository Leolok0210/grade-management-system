export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  dataCard?: DataCard;
  dataCards?: DataCard[];
  confirmation?: ConfirmationRequest;
  _status?: string;
}

export interface DataCard {
  type: "table" | "chart" | "form" | "transcript";
  title: string;
  payload: any;
}

export interface ConfirmationRequest {
  requestId: string;
  skillName: string;
  description: string;
  preview?: DataCard;
}

export interface User {
  id: number;
  name: string;
  role: string;
  school_id: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ChatRequest {
  conversation_id?: number;
  message: string;
}

export interface ChatResponse {
  conversation_id: number;
  reply: string;
  data_card?: DataCard | null;
  needs_confirm?: boolean;
  confirm_request_id?: string | null;
}

export interface ConversationItem {
  id: number;
  updated_at: string | null;
  preview: string;
}

export interface ConversationDetail {
  id: number;
  messages: { role: string; content: string }[];
  updated_at: string | null;
}
// =====================================================
//   TYPES - TR4CTION FRONTEND
// =====================================================

export interface User {
  id: number;
  email: string;
  role: 'admin' | 'founder';
  startup_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: string;
  startup_name?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
}

export interface ChatRequest {
  question: string;
  trail_id?: string;
  step_id?: string;
  use_rag?: boolean;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  trail_id?: string;
  step_id?: string;
}

export interface Document {
  id: string;
  filename: string;
  trail_id: string;
  step_id: string;
  version: string;
  description?: string;
  uploaded_at: string;
  chunks_count?: number;
}

export interface Trail {
  id: string;
  name: string;
  description: string;
  steps: Step[];
}

export interface Step {
  id: string;
  name: string;
  description: string;
}

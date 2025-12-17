// =====================================================
//   API CLIENT - TR4CTION FRONTEND
// =====================================================

import { getToken, logout, isTokenExpired } from './auth';
import { AuthResponse, ChatRequest, ChatResponse, Document, Trail } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://54.144.92.71.sslip.io';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  
  // Verificar expiração do token
  if (token && isTokenExpired(token)) {
    logout();
    throw new ApiError('Sessão expirada', 401);
  }
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      logout();
    }
    const error = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
    throw new ApiError(error.detail || 'Erro na requisição', response.status);
  }
  
  // Handle empty responses
  const text = await response.text();
  if (!text) return {} as T;
  
  return JSON.parse(text);
}

// =====================================================
//   AUTH ENDPOINTS
// =====================================================

export async function login(email: string, password: string): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Credenciais inválidas' }));
    throw new ApiError(error.detail || 'Erro no login', response.status);
  }
  
  return response.json();
}

// =====================================================
//   CHAT ENDPOINTS
// =====================================================

export async function sendChatMessage(data: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// =====================================================
//   KNOWLEDGE BASE ENDPOINTS (ADMIN)
// =====================================================

export async function getDocuments(): Promise<Document[]> {
  return request<Document[]>('/admin/knowledge/documents');
}

export async function uploadDocument(
  file: File,
  trailId: string,
  stepId: string,
  version: string,
  description?: string
): Promise<Document> {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('trail_id', trailId);
  formData.append('step_id', stepId);
  formData.append('version', version);
  if (description) {
    formData.append('description', description);
  }
  
  const response = await fetch(`${API_URL}/admin/knowledge/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro no upload' }));
    throw new ApiError(error.detail || 'Erro no upload', response.status);
  }
  
  return response.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  return request<void>(`/admin/knowledge/documents/${documentId}`, {
    method: 'DELETE',
  });
}

export async function reindexKnowledge(): Promise<{ message: string }> {
  return request<{ message: string }>('/admin/knowledge/reindex', {
    method: 'POST',
  });
}

// =====================================================
//   TRAILS ENDPOINTS
// =====================================================

export async function getTrails(): Promise<Trail[]> {
  return request<Trail[]>('/founder/trails');
}

export async function getAdminTrails(): Promise<Trail[]> {
  return request<Trail[]>('/admin/trails');
}

// =====================================================
//   HEALTH CHECK
// =====================================================

export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}

export { ApiError };

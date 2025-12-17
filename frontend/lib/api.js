/**
 * Cliente HTTP centralizado para comunicação com a API
 * Usa 127.0.0.1 ao invés de localhost para evitar problemas de DNS/cache
 */

// Aceita tanto NEXT_PUBLIC_API_URL quanto NEXT_PUBLIC_API_BASE_URL para compatibilidade
const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "tr4ction_token";

/**
 * Obtém o token do localStorage
 */
function getToken() {
  if (typeof window !== "undefined") {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/**
 * Adiciona headers de autenticação se disponível
 */
function getAuthHeaders() {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Trata resposta de erro - redireciona para login se 401
 */
function handleAuthError(res) {
  if (res.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("tr4ction_user");
    window.location.href = "/login";
    throw new Error("Sessão expirada. Faça login novamente.");
  }
}

/**
 * Faz uma requisição GET para a API
 * @param {string} path - Caminho do endpoint (ex: "/founder/trails")
 * @returns {Promise<any>} - Dados da resposta
 */
export async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    cache: "no-store",
    headers: getAuthHeaders(),
  });

  handleAuthError(res);

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error ${res.status}`);
  }

  return res.json();
}

/**
 * Faz uma requisição POST para a API
 * @param {string} path - Caminho do endpoint
 * @param {object} body - Corpo da requisição
 * @returns {Promise<any>} - Dados da resposta
 */
export async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    cache: "no-store",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });

  handleAuthError(res);

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error ${res.status}`);
  }

  return res.json();
}

/**
 * Faz uma requisição PUT para a API
 * @param {string} path - Caminho do endpoint
 * @param {object} body - Corpo da requisição
 * @returns {Promise<any>} - Dados da resposta
 */
export async function apiPut(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    cache: "no-store",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });

  handleAuthError(res);

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error ${res.status}`);
  }

  return res.json();
}

/**
 * Faz download de um arquivo da API
 * @param {string} path - Caminho do endpoint
 * @param {string} filename - Nome do arquivo para download
 */
export async function apiDownload(path, filename) {
  const token = getToken();
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    cache: "no-store",
    headers,
  });

  handleAuthError(res);

  if (!res.ok) {
    throw new Error(`Download error ${res.status}`);
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

/**
 * Retorna a URL base da API
 */
export function getApiBase() {
  return API_BASE;
}

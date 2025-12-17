/**
 * Cliente HTTP centralizado para comunicação com a API
 * Usa 127.0.0.1 ao invés de localhost para evitar problemas de DNS/cache
 */

// Aceita tanto NEXT_PUBLIC_API_URL quanto NEXT_PUBLIC_API_BASE_URL para compatibilidade
const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "tr4ction_token";

// Configurações de retry
const RETRY_CONFIG = {
  maxAttempts: 3,
  initialDelayMs: 1000,
  maxDelayMs: 5000,
  backoffMultiplier: 2,
};

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
 * Aguarda N milissegundos com backoff exponencial
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Formata mensagem de erro de forma legível
 */
function formatErrorMessage(error, res = null) {
  let message = "Erro ao comunicar com o servidor";
  
  if (error instanceof TypeError && error.message === "fetch failed") {
    message = "Impossível conectar ao servidor. Verifique sua conexão.";
  } else if (res?.status === 429) {
    message = "Muitas requisições. Tente novamente em alguns momentos.";
  } else if (res?.status === 503) {
    message = "Servidor indisponível. Tente novamente mais tarde.";
  } else if (res?.status === 504) {
    message = "Timeout do servidor. Tente novamente.";
  } else if (error.message) {
    message = error.message;
  }
  
  return message;
}

/**
 * Faz uma requisição com retry automático
 */
async function fetchWithRetry(url, options = {}, isRetryable = true) {
  let lastError = null;
  let delayMs = RETRY_CONFIG.initialDelayMs;
  
  for (let attempt = 1; attempt <= RETRY_CONFIG.maxAttempts; attempt++) {
    try {
      const res = await fetch(url, {
        ...options,
        signal: AbortSignal.timeout(30000), // 30s timeout
      });
      
      handleAuthError(res);
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const errorMsg = errorData.detail || `HTTP ${res.status}`;
        
        // Não retenta em certos casos
        if (!isRetryable || res.status === 401 || res.status === 403 || res.status === 400) {
          throw new Error(errorMsg);
        }
        
        // Retenta em erros 5xx
        if (res.status >= 500 && attempt < RETRY_CONFIG.maxAttempts) {
          lastError = new Error(errorMsg);
          await delay(delayMs);
          delayMs = Math.min(delayMs * RETRY_CONFIG.backoffMultiplier, RETRY_CONFIG.maxDelayMs);
          continue;
        }
        
        throw new Error(errorMsg);
      }
      
      return await res.json();
    } catch (error) {
      lastError = error;
      
      // Retenta em erros de rede
      if (isRetryable && attempt < RETRY_CONFIG.maxAttempts && 
          (error instanceof TypeError || error.name === "AbortError")) {
        await delay(delayMs);
        delayMs = Math.min(delayMs * RETRY_CONFIG.backoffMultiplier, RETRY_CONFIG.maxDelayMs);
        continue;
      }
      
      throw error;
    }
  }
  
  throw lastError || new Error("Falha após múltiplas tentativas");
}

/**
 * Faz uma requisição GET para a API
 * @param {string} path - Caminho do endpoint (ex: "/founder/trails")
 * @param {boolean} retryable - Se deve fazer retry automático
 * @returns {Promise<any>} - Dados da resposta
 */
export async function apiGet(path, retryable = true) {
  try {
    return await fetchWithRetry(`${API_BASE}${path}`, {
      method: "GET",
      cache: "no-store",
      headers: getAuthHeaders(),
    }, retryable);
  } catch (error) {
    const msg = formatErrorMessage(error);
    const err = new Error(msg);
    err.originalError = error;
    throw err;
  }
}

/**
 * Faz uma requisição POST para a API
 * @param {string} path - Caminho do endpoint
 * @param {object} body - Corpo da requisição
 * @param {boolean} retryable - Se deve fazer retry automático
 * @returns {Promise<any>} - Dados da resposta
 */
export async function apiPost(path, body, retryable = true) {
  try {
    return await fetchWithRetry(`${API_BASE}${path}`, {
      method: "POST",
      cache: "no-store",
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    }, retryable);
  } catch (error) {
    const msg = formatErrorMessage(error);
    const err = new Error(msg);
    err.originalError = error;
    throw err;
  }
}

/**
 * Faz uma requisição PUT para a API
 * @param {string} path - Caminho do endpoint
 * @param {object} body - Corpo da requisição
 * @param {boolean} retryable - Se deve fazer retry automático
 * @returns {Promise<any>} - Dados da resposta
 */
export async function apiPut(path, body, retryable = true) {
  try {
    return await fetchWithRetry(`${API_BASE}${path}`, {
      method: "PUT",
      cache: "no-store",
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    }, retryable);
  } catch (error) {
    const msg = formatErrorMessage(error);
    const err = new Error(msg);
    err.originalError = error;
    throw err;
  }
}

/**
 * Faz download de um arquivo da API
 * @param {string} path - Caminho do endpoint
 * @param {string} filename - Nome do arquivo para download
 */
export async function apiDownload(path, filename) {
  try {
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
      throw new Error(`Erro ao baixar arquivo (HTTP ${res.status})`);
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
  } catch (error) {
    const msg = formatErrorMessage(error);
    const err = new Error(msg);
    err.originalError = error;
    throw err;
  }
}

/**
 * Retorna a URL base da API
 */
export function getApiBase() {
  return API_BASE;
}

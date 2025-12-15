// =====================================================
//   AUTH - TR4CTION FRONTEND
// =====================================================

import { AuthResponse, User } from './types';
import Cookies from 'js-cookie';

const TOKEN_KEY = 'tr4ction_token';
const USER_KEY = 'tr4ction_user';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return Cookies.get(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  Cookies.set(TOKEN_KEY, token, { expires: 7, sameSite: 'lax' });
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  Cookies.remove(TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

export function setUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function removeUser(): void {
  localStorage.removeItem(USER_KEY);
}

export function logout(): void {
  removeToken();
  removeUser();
  window.location.href = '/login';
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function parseJWT(token: string): { exp: number; sub: string; role: string } | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = parseJWT(token);
  if (!payload) return true;
  return Date.now() >= payload.exp * 1000;
}

export function handleAuthResponse(response: AuthResponse): User {
  setToken(response.access_token);
  
  const payload = parseJWT(response.access_token);
  const user: User = {
    id: 0,
    email: payload?.sub || '',
    role: response.role as 'admin' | 'founder',
    startup_name: response.startup_name,
  };
  
  setUser(user);
  return user;
}

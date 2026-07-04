const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T = any>(path: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const headers: Record<string, string> = { ...(options?.headers as Record<string, string>) };

  // FormData 不加 Content-Type，让浏览器自动设置 multipart boundary
  if (!(options?.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) { localStorage.removeItem('token'); if (typeof window !== 'undefined') window.location.href = '/login'; throw new ApiError(401, '未授权'); }
  if (!res.ok) { const err = await res.json().catch(() => ({ message: res.statusText })); throw new ApiError(res.status, err.message || err.detail || `API ${res.status}`, err); }
  return res.json();
}

export const api = {
  get: <T = any>(p: string) => request<T>(p),
  post: <T = any>(p: string, b?: any) => request<T>(p, { method: 'POST', body: b instanceof FormData ? b : (b != null ? JSON.stringify(b) : undefined) }),
  postFile: <T = any>(p: string, fd: FormData) => request<T>(p, { method: 'POST', body: fd }),
  put: <T = any>(p: string, b?: any) => request<T>(p, { method: 'PUT', body: b != null ? JSON.stringify(b) : undefined }),
  delete: <T = any>(p: string) => request<T>(p, { method: 'DELETE' }),
};

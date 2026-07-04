'use client';
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from './api';

interface User { id: string; full_name: string; email: string; }
interface AuthContextType { user: User | null; loading: boolean; login: (e: string, p: string) => Promise<void>; register: (u: string, e: string, p: string) => Promise<void>; logout: () => void; }
const AuthContext = createContext<AuthContextType>({} as AuthContextType);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) api.get<{ data: User }>('/api/v1/auth/me').then(r => setUser(r.data)).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false));
    else setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const r = await api.post<{ access_token: string; refresh_token: string }>('/api/v1/auth/login', { email, password });
    localStorage.setItem('token', r.access_token);
    const me = await api.get<User>('/api/v1/auth/me');
    setUser(me);
  };
  const register = async (full_name: string, email: string, password: string) => {
    await api.post('/api/v1/auth/register', { full_name, email, password });
    // Backend does not auto-login after register; call login
    await login(email, password);
  };
  const logout = () => { localStorage.removeItem('token'); setUser(null); };
  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>;
}

'use client';
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from './api';

interface User { id: number; username: string; email: string; }
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
    const r = await api.post<{ data: { token: string; user: User } }>('/api/v1/auth/login', { email, password });
    localStorage.setItem('token', r.data.token); setUser(r.data.user);
  };
  const register = async (username: string, email: string, password: string) => {
    const r = await api.post<{ data: { token: string; user: User } }>('/api/v1/auth/register', { username, email, password });
    localStorage.setItem('token', r.data.token); setUser(r.data.user);
  };
  const logout = () => { localStorage.removeItem('token'); setUser(null); };
  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>;
}

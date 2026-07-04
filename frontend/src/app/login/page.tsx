'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Loader2 } from 'lucide-react';

const loginSchema = z.object({ email: z.string().email('请输入有效邮箱'), password: z.string().min(6, '密码至少6位') });
const registerSchema = z.object({ full_name: z.string().min(2, '姓名至少2个字符'), email: z.string().email('请输入有效邮箱'), password: z.string().min(6, '密码至少6位'), confirmPassword: z.string() }).refine(d => d.password === d.confirmPassword, { message: '两次密码不一致', path: ['confirmPassword'] });

export default function LoginPage() {
  const { login, register } = useAuth();
  const router = useRouter();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const lf = useForm<z.infer<typeof loginSchema>>({ resolver: zodResolver(loginSchema), defaultValues: { email: '', password: '' } });
  const rf = useForm<z.infer<typeof registerSchema>>({ resolver: zodResolver(registerSchema), defaultValues: { full_name: '', email: '', password: '', confirmPassword: '' } });

  const handleLogin = async (data: z.infer<typeof loginSchema>) => { setError(''); setLoading(true); try { await login(data.email, data.password); router.push('/'); } catch (e: any) { setError(e.message); } finally { setLoading(false); } };
  const handleRegister = async (data: z.infer<typeof registerSchema>) => { setError(''); setLoading(true); try { await register(data.full_name, data.email, data.password); router.push('/'); } catch (e: any) { setError(e.message); } finally { setLoading(false); } };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center">
          <div className="mx-auto h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-3"><span className="text-white font-bold text-lg">SA</span></div>
          <CardTitle className="text-2xl">SciAgent</CardTitle>
          <CardDescription>智能科研助手平台</CardDescription>
        </CardHeader>
        <CardContent>
          {error && <Alert variant="destructive" className="mb-4"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}
          <Tabs defaultValue="login">
            <TabsList className="grid grid-cols-2 w-full"><TabsTrigger value="login">登录</TabsTrigger><TabsTrigger value="register">注册</TabsTrigger></TabsList>
            <TabsContent value="login">
              <form onSubmit={lf.handleSubmit(handleLogin)} className="space-y-4 mt-4">
                <div><Label htmlFor="email">邮箱</Label><Input id="email" type="email" placeholder="your@email.com" {...lf.register('email')} />{lf.formState.errors.email && <p className="text-sm text-red-500 mt-1">{lf.formState.errors.email.message}</p>}</div>
                <div><Label htmlFor="password">密码</Label><Input id="password" type="password" placeholder="••••••" {...lf.register('password')} />{lf.formState.errors.password && <p className="text-sm text-red-500 mt-1">{lf.formState.errors.password.message}</p>}</div>
                <Button type="submit" className="w-full" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}登录</Button>
              </form>
            </TabsContent>
            <TabsContent value="register">
              <form onSubmit={rf.handleSubmit(handleRegister)} className="space-y-4 mt-4">
                <div><Label htmlFor="rfn">姓名</Label><Input id="rfn" placeholder="你的姓名" {...rf.register('full_name')} />{rf.formState.errors.full_name && <p className="text-sm text-red-500 mt-1">{rf.formState.errors.full_name.message}</p>}</div>
                <div><Label htmlFor="re">邮箱</Label><Input id="re" type="email" placeholder="your@email.com" {...rf.register('email')} />{rf.formState.errors.email && <p className="text-sm text-red-500 mt-1">{rf.formState.errors.email.message}</p>}</div>
                <div><Label htmlFor="rp">密码</Label><Input id="rp" type="password" placeholder="••••••" {...rf.register('password')} />{rf.formState.errors.password && <p className="text-sm text-red-500 mt-1">{rf.formState.errors.password.message}</p>}</div>
                <div><Label htmlFor="rc">确认密码</Label><Input id="rc" type="password" placeholder="••••••" {...rf.register('confirmPassword')} />{rf.formState.errors.confirmPassword && <p className="text-sm text-red-500 mt-1">{rf.formState.errors.confirmPassword.message}</p>}</div>
                <Button type="submit" className="w-full" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}注册</Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

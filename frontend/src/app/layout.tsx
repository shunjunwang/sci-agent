'use client';

import { ThemeProvider } from 'next-themes';
import { AuthProvider, useAuth } from '@/lib/auth';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { cn } from '@/libs/utils';
import {
  LayoutDashboard, Search, Library, PenLine, Code2,
  Users, ShoppingBag, GitBranch, ShieldCheck, BarChart3,
  Settings, LogOut, ChevronLeft, ChevronRight, Sun, Moon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import './globals.css';

const navItems = [
  { href: '/', label: '仪表盘', icon: LayoutDashboard },
  { href: '/search', label: '文献检索', icon: Search },
  { href: '/library', label: '知识库', icon: Library },
  { href: '/writing', label: 'AI写作', icon: PenLine },
  { href: '/sandbox', label: '沙箱', icon: Code2 },
];
const navItems2 = [
  { href: '/workspace', label: '协作空间', icon: Users },
  { href: '/algorithms', label: '算法商城', icon: ShoppingBag },
];
const navItems3 = [
  { href: '/workflow', label: '工作流', icon: GitBranch },
  { href: '/academic-check', label: '学术自查', icon: ShieldCheck },
  { href: '/plot', label: '配图工具', icon: BarChart3 },
];

function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { logout } = useAuth();

  const NavLink = ({ href, label, icon: Icon }: { href: string; label: string; icon: any }) => {
    const active = pathname === href || (href !== '/' && pathname.startsWith(href));
    return (
      <Link href={href} className={cn('flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors', collapsed && 'justify-center px-2', active ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50')}>
        <Icon className="h-5 w-5 shrink-0" />
        {!collapsed && <span>{label}</span>}
      </Link>
    );
  };

  return (
    <aside className={cn('flex flex-col bg-slate-900 border-r border-slate-800 h-screen sticky top-0 transition-all duration-200', collapsed ? 'w-16' : 'w-60')}>
      <div className="flex items-center gap-2 px-4 h-14 border-b border-slate-800 shrink-0">
        {!collapsed ? (
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"><span className="text-white font-bold text-sm">SA</span></div>
            <span className="font-semibold text-white text-base">SciAgent</span>
          </div>
        ) : (
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto"><span className="text-white font-bold text-sm">SA</span></div>
        )}
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item) => (<NavLink key={item.href} {...item} />))}
        <Separator className="bg-slate-800 my-3" />
        {navItems2.map((item) => (<NavLink key={item.href} {...item} />))}
        <Separator className="bg-slate-800 my-3" />
        {navItems3.map((item) => (<NavLink key={item.href} {...item} />))}
      </nav>
      <div className="px-3 py-3 border-t border-slate-800 space-y-1">
        <NavLink href="/settings" label="设置" icon={Settings} />
        <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors">
          <LogOut className="h-5 w-5 shrink-0" />{!collapsed && <span>退出登录</span>}
        </button>
      </div>
      <button onClick={() => setCollapsed(!collapsed)} className="absolute -right-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center hover:bg-slate-600">
        {collapsed ? <ChevronRight className="h-3 w-3 text-slate-300" /> : <ChevronLeft className="h-3 w-3 text-slate-300" />}
      </button>
    </aside>
  );
}

function Topbar() {
  const { user, logout } = useAuth();
  const [isDark, setIsDark] = useState(false);

  useEffect(() => { setIsDark(document.documentElement.classList.contains('dark')); }, []);

  const toggleTheme = () => {
    const next = !isDark; setIsDark(next);
    document.documentElement.classList.toggle('dark', next);
  };

  return (
    <header className="h-14 border-b bg-white dark:bg-slate-950 flex items-center justify-between px-6 shrink-0">
      <div />
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className={cn('h-2 w-2 rounded-full', user ? 'bg-green-500' : 'bg-gray-400')} />
          <span>{user ? '在线' : '离线'}</span>
        </div>
        <Button variant="ghost" size="icon" onClick={toggleTheme}>{isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}</Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
              <Avatar className="h-8 w-8"><AvatarFallback className="bg-slate-700 text-white text-xs">{user?.full_name?.slice(0, 2).toUpperCase() || 'U'}</AvatarFallback></Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end">
            <DropdownMenuLabel><div className="flex flex-col"><span>{user?.full_name || '用户'}</span><span className="text-xs text-muted-foreground">{user?.email}</span></div></DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild><Link href="/settings">设置</Link></DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout}>退出登录</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user && pathname !== '/login') router.push('/login');
  }, [user, loading, pathname, router]);

  if (pathname === '/login') return <>{children}</>;
  if (loading) return (
    <div className="flex h-screen"><div className="w-60 bg-slate-900" /><div className="flex-1 p-6 space-y-4"><Skeleton className="h-14 w-full" /><Skeleton className="h-8 w-1/3" /><div className="grid grid-cols-4 gap-4">{[1,2,3,4].map(i => <Skeleton key={i} className="h-32" />)}</div></div></div>
  );
  if (!user) return null;

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          <AuthProvider><AuthGuard>{children}</AuthGuard></AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

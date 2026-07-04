'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { BookOpen, Library, PenLine, GitBranch, ArrowRight, Search, FileText } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [stats, setStats] = useState({ papers: 0, library: 0, writing: 0, workflow: 0 });
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [recentDocs, setRecentDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.get('/api/v2/papers/history?limit=5').catch(() => ({ data: [] })),
      api.get('/api/v3/library/entries?limit=5').catch(() => ({ data: [] })),
      api.get('/api/v5/writing/documents?limit=5').catch(() => ({ data: [] })),
    ]).then(([papersR, libR, writingR]) => {
      const papers = (papersR as any).value?.data || [];
      const libItems = (libR as any).value?.data || [];
      const docs = (writingR as any).value?.data || [];
      setStats({ papers: papers.length, library: libItems.length, writing: docs.length, workflow: 0 });
      setRecentSearches(papers.slice(0, 5));
      setRecentDocs(docs.slice(0, 5));
    }).finally(() => setLoading(false));
  }, []);

  const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });

  const statCards = [
    { label: '文献总数', value: stats.papers, icon: BookOpen, color: 'text-blue-600', bg: 'bg-blue-50 dark:bg-blue-950' },
    { label: '知识库条目', value: stats.library, icon: Library, color: 'text-purple-600', bg: 'bg-purple-50 dark:bg-purple-950' },
    { label: '写作文档', value: stats.writing, icon: PenLine, color: 'text-green-600', bg: 'bg-green-50 dark:bg-green-950' },
    { label: '工作流实例', value: stats.workflow, icon: GitBranch, color: 'text-orange-600', bg: 'bg-orange-50 dark:bg-orange-950' },
  ];

  const quickLinks = [
    { href: '/search', label: '文献检索', icon: Search },
    { href: '/writing', label: 'AI写作', icon: PenLine },
    { href: '/library', label: '知识库', icon: Library },
    { href: '/workflow', label: '工作流', icon: GitBranch },
  ];

  if (loading) return <div className="space-y-6"><Skeleton className="h-8 w-48" /><div className="grid grid-cols-4 gap-4">{[1,2,3,4].map(i => <Skeleton key={i} className="h-28" />)}</div></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">欢迎回来</h1>
        <p className="text-muted-foreground text-sm mt-1">{today}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((s) => (
          <Card key={s.label} className="shadow-sm">
            <CardContent className="p-4 flex items-center gap-4">
              <div className={`p-2.5 rounded-lg ${s.bg}`}><s.icon className={`h-5 w-5 ${s.color}`} /></div>
              <div><p className="text-2xl font-bold">{s.value}</p><p className="text-sm text-muted-foreground">{s.label}</p></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-base">快速入口</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {quickLinks.map((ql) => (
                <Link key={ql.href} href={ql.href}>
                  <Button variant="outline" className="w-full h-20 flex flex-col gap-1.5">
                    <ql.icon className="h-5 w-5" /><span className="text-xs">{ql.label}</span>
                  </Button>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-base">最近搜索</CardTitle><Link href="/search"><Button variant="ghost" size="sm"><ArrowRight className="h-4 w-4" /></Button></Link></CardHeader>
          <CardContent>
            {recentSearches.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">暂无搜索记录</p>
            ) : (
              <div className="space-y-2">
                {recentSearches.map((s: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm"><Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" /><span className="truncate">{s.query || s.title || `搜索记录 ${i + 1}`}</span></div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-base">最近文档</CardTitle><Link href="/writing"><Button variant="ghost" size="sm"><ArrowRight className="h-4 w-4" /></Button></Link></CardHeader>
        <CardContent>
          {recentDocs.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">暂无文档，<Link href="/writing" className="text-blue-600 hover:underline">去创建</Link></p>
          ) : (
            <div className="space-y-2">
              {recentDocs.map((d: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div className="flex items-center gap-2"><FileText className="h-4 w-4 text-muted-foreground" /><span className="text-sm">{d.title || '未命名文档'}</span></div>
                  <span className="text-xs text-muted-foreground">{d.updated_at ? new Date(d.updated_at).toLocaleDateString('zh-CN') : ''}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Search, Loader2, History, Download, ExternalLink, Clock } from 'lucide-react';

const SOURCES = ['arxiv', 'pubmed', 'keying'];

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [sources, setSources] = useState<string[]>(['arxiv']);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<any[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  const toggleSource = (s: string) => setSources(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true); setError('');
    try {
      const r = await api.post('/api/v2/papers/search', { query: query.trim(), sources });
      setResults(r.data || []);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const loadHistory = async () => {
    if (historyLoaded) return;
    try { const r = await api.get('/api/v2/papers/history?limit=20'); setHistory(r.data || []); } catch {}
    setHistoryLoaded(true);
  };

  const handleImport = async (paper: any) => {
    try { await api.post('/api/v3/knowledge/papers', paper); }
    catch (e: any) { setError(e.message); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">文献检索</h1>
        <p className="text-muted-foreground text-sm mt-1">跨数据库智能检索学术文献</p>
      </div>

      <Card className="shadow-sm">
        <CardContent className="p-4 space-y-4">
          <div className="flex gap-2">
            <Input value={query} onChange={e => setQuery(e.target.value)} placeholder="输入关键词、论文标题或作者..." className="flex-1" onKeyDown={e => e.key === 'Enter' && handleSearch()} />
            <Button onClick={handleSearch} disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}搜索</Button>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-muted-foreground">数据源：</span>
            {SOURCES.map(s => (
              <Badge key={s} variant={sources.includes(s) ? 'default' : 'outline'} className="cursor-pointer" onClick={() => toggleSource(s)}>{s === 'keying' ? '科应' : s.toUpperCase()}</Badge>
            ))}
            <Sheet onOpenChange={(open) => { if (open) loadHistory(); }}>
              <SheetTrigger asChild><Button variant="outline" size="sm"><History className="h-4 w-4 mr-1" />历史</Button></SheetTrigger>
              <SheetContent>
                <SheetHeader><SheetTitle>搜索历史</SheetTitle></SheetHeader>
                <ScrollArea className="h-[calc(100vh-100px)] mt-4">
                  {history.length === 0 ? <p className="text-sm text-muted-foreground text-center py-8">暂无搜索记录</p> : (
                    <div className="space-y-2">
                      {history.map((h: any, i: number) => (
                        <div key={i} className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer" onClick={() => setQuery(h.query || '')}>
                          <Clock className="h-3.5 w-3.5 text-muted-foreground shrink-0" /><span className="text-sm truncate">{h.query}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </SheetContent>
            </Sheet>
          </div>
        </CardContent>
      </Card>

      {error && <div className="p-4 bg-red-50 dark:bg-red-950 text-red-600 rounded-lg text-sm">{error}</div>}

      {loading ? (
        <div className="space-y-4">{[1,2,3].map(i => <Skeleton key={i} className="h-32" />)}</div>
      ) : results.length === 0 && query ? (
        <p className="text-center py-12 text-muted-foreground">未找到相关文献，尝试更换关键词</p>
      ) : (
        <div className="space-y-4">
          {results.map((paper: any, i: number) => (
            <Card key={i} className="shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-base mb-1">{paper.title}</h3>
                    <p className="text-sm text-muted-foreground mb-2">{paper.authors?.join(', ') || '未知作者'} · {paper.year || ''}</p>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="secondary" className="text-xs">{paper.source?.toUpperCase() || 'Unknown'}</Badge>
                      {paper.doi && <span className="text-xs text-muted-foreground">DOI: {paper.doi}</span>}
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">{paper.abstract}</p>
                  </div>
                  <div className="flex flex-col gap-2 shrink-0">
                    {paper.url && <Button variant="outline" size="sm" asChild><a href={paper.url} target="_blank"><ExternalLink className="h-3.5 w-3.5" /></a></Button>}
                    <Button variant="outline" size="sm" onClick={() => handleImport(paper)}><Download className="h-3.5 w-3.5 mr-1" />导入</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

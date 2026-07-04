'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Star, Download, Search, Play, TrendingUp, Cpu } from 'lucide-react';

const CATEGORIES = ['全部', '机器学习', '深度学习', 'NLP', 'CV', '优化', '统计'];

export default function AlgorithmsPage() {
  const [algorithms, setAlgorithms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('全部');
  const [selectedAlg, setSelectedAlg] = useState<any>(null);
  const [execOutput, setExecOutput] = useState('');
  const [execLoading, setExecLoading] = useState(false);
  const [params, setParams] = useState<Record<string, string>>({});

  useEffect(() => { fetchAlgorithms(); }, []);

  const fetchAlgorithms = async () => {
    setLoading(true);
    try { const r = await api.get('/api/v9/algorithms'); setAlgorithms(r.data?.items || []); } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const filtered = algorithms.filter(a => {
    if (category !== '全部' && a.category !== category) return false;
    if (search && !a.name?.toLowerCase().includes(search.toLowerCase()) && !a.description?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const handleExecute = async () => {
    setExecLoading(true); setExecOutput('');
    try { const r = await api.post(`/api/v9/algorithms/${selectedAlg.id}/execute`, params); setExecOutput(r.data?.status ? `执行已提交 (${r.data.status})\nID: ${r.data.execution_id}` : JSON.stringify(r.data, null, 2)); }
    catch (e: any) { setExecOutput(`Error: ${e.message}`); }
    finally { setExecLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold tracking-tight">算法商城</h1><p className="text-muted-foreground text-sm mt-1">浏览和执行学术算法</p></div>

      <Card className="shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" /><Input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索算法..." className="pl-9" /></div>
            <div className="flex gap-1 flex-wrap">
              {CATEGORIES.map(c => <Badge key={c} variant={category === c ? 'default' : 'outline'} className="cursor-pointer" onClick={() => setCategory(c)}>{c}</Badge>)}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{[1,2,3,4,5,6].map(i => <Skeleton key={i} className="h-40" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground"><Cpu className="h-12 w-12 mx-auto mb-3 opacity-30" /><p>暂无算法</p></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((alg: any) => (
            <Dialog key={alg.id}>
              <DialogTrigger asChild>
                <Card className="shadow-sm hover:shadow-md transition-shadow cursor-pointer h-full" onClick={() => { setSelectedAlg(alg); setParams({}); setExecOutput(''); }}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center"><Cpu className="h-5 w-5 text-blue-600" /></div>
                      <Badge variant="outline">{alg.category || '通用'}</Badge>
                    </div>
                    <h3 className="font-semibold mb-1">{alg.name}</h3>
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{alg.description}</p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Star className="h-3 w-3" />{alg.rating_avg || '-'}</span>
                      <span className="flex items-center gap-1"><Download className="h-3 w-3" />{alg.usage_count || 0}</span>
                    </div>
                  </CardContent>
                </Card>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader><DialogTitle>{alg.name}</DialogTitle></DialogHeader>
                <div className="space-y-4 mt-2">
                  <p className="text-sm text-muted-foreground">{alg.description}</p>
                  {alg.default_params && Object.keys(alg.default_params).length > 0 && (
                    <div className="space-y-3">
                      {Object.entries(alg.default_params || {}).map(([key, val]: [string, any]) => (
                        <div key={key}>
                          <Label className="text-xs">{key} (default: {String(val)})</Label>
                          <Input value={params[key] || ''} onChange={e => setParams(prev => ({ ...prev, [key]: e.target.value }))} placeholder={String(val)} />
                        </div>
                      ))}
                    </div>
                  )}
                  <Button onClick={handleExecute} disabled={execLoading} className="w-full"><Play className="h-4 w-4 mr-2" />{execLoading ? '执行中...' : '执行'}</Button>
                  {execOutput && <pre className="p-3 bg-slate-900 text-green-400 rounded-lg text-xs font-mono max-h-48 overflow-y-auto whitespace-pre-wrap">{execOutput}</pre>}
                </div>
              </DialogContent>
            </Dialog>
          ))}
        </div>
      )}
    </div>
  );
}

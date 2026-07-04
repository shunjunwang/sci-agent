'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search, Plus, Trash2, BookOpen, FileText, Database } from 'lucide-react';
import Link from 'next/link';

export default function LibraryPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [importOpen, setImportOpen] = useState(false);
  const [importText, setImportText] = useState('');

  useEffect(() => { fetchEntries(); }, []);

  const fetchEntries = async () => {
    setLoading(true);
    try { const r = await api.get('/api/v3/knowledge/papers'); setEntries(r.data || []); } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleDelete = async (id: number) => {
    try { await api.delete(`/api/v3/knowledge/papers/${id}`); setEntries(prev => prev.filter(e => e.id !== id)); } catch (e: any) { setError(e.message); }
  };

  const handleImport = async () => {
    if (!importText.trim()) return;
    try { await api.post('/api/v3/knowledge/papers/import', { text: importText }); setImportOpen(false); setImportText(''); fetchEntries(); } catch (e: any) { setError(e.message); }
  };

  const filtered = entries.filter(e => {
    if (filter !== 'all' && e.type !== filter) return false;
    if (search && !e.title?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const typeIcon = (type: string) => {
    switch (type) { case 'paper': return <BookOpen className="h-4 w-4" />; case 'note': return <FileText className="h-4 w-4" />; case 'dataset': return <Database className="h-4 w-4" />; default: return <FileText className="h-4 w-4" />; }
  };

  if (loading) return <div className="space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-10 w-full" /><Skeleton className="h-64 w-full" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold tracking-tight">知识库</h1><p className="text-muted-foreground text-sm mt-1">管理你的学术文献、笔记和数据集</p></div>
        <Dialog open={importOpen} onOpenChange={setImportOpen}>
          <DialogTrigger asChild><Button><Plus className="h-4 w-4 mr-2" />导入文献</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>导入文献</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <p className="text-sm text-muted-foreground">粘贴 BibTeX、DOI 或文本描述</p>
              <textarea className="w-full h-32 p-3 border rounded-lg text-sm" value={importText} onChange={e => setImportText(e.target.value)} placeholder="@article{...}" />
              <Button onClick={handleImport} className="w-full">导入</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && <div className="p-3 bg-red-50 dark:bg-red-950 text-red-600 rounded-lg text-sm">{error}</div>}

      <Card className="shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" /><Input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索标题..." className="pl-9" /></div>
            <Tabs value={filter} onValueChange={setFilter}>
              <TabsList><TabsTrigger value="all">全部</TabsTrigger><TabsTrigger value="paper">论文</TabsTrigger><TabsTrigger value="note">笔记</TabsTrigger><TabsTrigger value="dataset">数据集</TabsTrigger></TabsList>
            </Tabs>
          </div>
        </CardContent>
      </Card>

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <BookOpen className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>知识库为空</p>
          <p className="text-sm mt-1">导入你的第一篇文献开始构建知识库</p>
        </div>
      ) : (
        <Card className="shadow-sm">
          <Table>
            <TableHeader><TableRow><TableHead>标题</TableHead><TableHead>类型</TableHead><TableHead>作者/来源</TableHead><TableHead>标签</TableHead><TableHead>更新时间</TableHead><TableHead className="w-20">操作</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map((entry: any) => (
                <TableRow key={entry.id}>
                  <TableCell><Link href={`/library/${entry.id}`} className="font-medium hover:text-blue-600">{entry.title || '未命名'}</Link></TableCell>
                  <TableCell><Badge variant="outline" className="flex items-center gap-1 w-fit">{typeIcon(entry.type)}{entry.type}</Badge></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{entry.authors || entry.source || '-'}</TableCell>
                  <TableCell><div className="flex gap-1 flex-wrap">{(entry.tags || []).map((t: string) => <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>)}</div></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{entry.updated_at ? new Date(entry.updated_at).toLocaleDateString('zh-CN') : '-'}</TableCell>
                  <TableCell><Button variant="ghost" size="icon" onClick={() => handleDelete(entry.id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}

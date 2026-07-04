'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, PenLine, FileText, Trash2, Clock, CheckCircle, Edit3 } from 'lucide-react';
import Link from 'next/link';

export default function WritingPage() {
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  useEffect(() => { fetchDocs(); }, []);

  const fetchDocs = async () => {
    setLoading(true);
    try { const r = await api.get('/api/v5/writing/documents'); setDocs(r.data || []); } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    try { const r = await api.post('/api/v5/writing/plan', { topic: newTitle.trim(), style: 'academic', language: 'zh' }); setCreateOpen(false); setNewTitle(''); fetchDocs(); } catch (e: any) { setError(e.message); }
  };

  const handleDelete = async (id: number) => {
    try { await api.delete(`/api/v5/writing/documents/${id}`); setDocs(prev => prev.filter(d => d.document_id || d.id !== id)); } catch (e: any) { setError(e.message); }
  };

  const statusBadge = (status: string) => {
    switch (status) {
      case 'draft': return <Badge variant="secondary"><Edit3 className="h-3 w-3 mr-1" />草稿</Badge>;
      case 'completed': return <Badge variant="default"><CheckCircle className="h-3 w-3 mr-1" />已完成</Badge>;
      default: return <Badge variant="outline"><Clock className="h-3 w-3 mr-1" />{status}</Badge>;
    }
  };

  if (loading) return <div className="space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-64 w-full" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold tracking-tight">AI写作</h1><p className="text-muted-foreground text-sm mt-1">智能辅助学术写作</p></div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="h-4 w-4 mr-2" />新建文档</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>新建文档</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <Input value={newTitle} onChange={e => setNewTitle(e.target.value)} placeholder="文档标题" onKeyDown={e => e.key === 'Enter' && handleCreate()} />
              <Button onClick={handleCreate} className="w-full">创建</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && <div className="p-3 bg-red-50 dark:bg-red-950 text-red-600 rounded-lg text-sm">{error}</div>}

      {docs.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <PenLine className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>还没有文档</p>
          <p className="text-sm mt-1">创建你的第一篇学术文档</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {docs.map((doc: any) => (
            <Card key={doc.document_id || doc.id} className="shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div className="min-w-0">
                    <Link href={`/writing/${doc.document_id || doc.id}`} className="font-medium hover:text-blue-600 text-sm">{doc.title || '未命名文档'}</Link>
                    <p className="text-xs text-muted-foreground mt-0.5">{doc.updated_at ? new Date(doc.updated_at).toLocaleString('zh-CN') : '-'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {statusBadge(doc.status || 'draft')}
                  <Link href={`/writing/${doc.document_id || doc.id}`}><Button variant="ghost" size="sm">编辑</Button></Link>
                  <Button variant="ghost" size="icon" onClick={() => handleDelete(doc.document_id || doc.id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

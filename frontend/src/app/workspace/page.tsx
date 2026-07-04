'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Skeleton } from '@/components/ui/skeleton';
import { Users, Plus, UserPlus, Mail } from 'lucide-react';

export default function WorkspacePage() {
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [selectedWs, setSelectedWs] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [detailOpen, setDetailOpen] = useState(false);

  useEffect(() => { fetchWorkspaces(); }, []);

  const fetchWorkspaces = async () => {
    setLoading(true);
    try { const r = await api.get('/api/v1/workspaces'); setWorkspaces(r.data || []); } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try { await api.post('/api/v1/workspaces', { name: newName.trim() }); setCreateOpen(false); setNewName(''); fetchWorkspaces(); } catch (e: any) { setError(e.message); }
  };

  const openDetail = async (ws: any) => {
    setSelectedWs(ws); setDetailOpen(true);
    try { const r = await api.get(`/api/v1/workspaces/${ws.id}/members`); setMembers(r.data?.members || []); } catch {}
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim() || !selectedWs) return;
    try { await api.post(`/api/v1/workspaces/${selectedWs.id}/invitations`, { invitee_email: inviteEmail.trim() }); setInviteEmail(''); } catch (e: any) { setError(e.message); }
  };

  if (loading) return <div className="space-y-4"><Skeleton className="h-8 w-48" /><div className="grid grid-cols-2 gap-4">{[1,2,3,4].map(i => <Skeleton key={i} className="h-40" />)}</div></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold tracking-tight">协作空间</h1><p className="text-muted-foreground text-sm mt-1">团队协作与项目管理</p></div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="h-4 w-4 mr-2" />新建空间</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>创建协作空间</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="空间名称" onKeyDown={e => e.key === 'Enter' && handleCreate()} />
              <Button onClick={handleCreate} className="w-full">创建</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>}

      {workspaces.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground"><Users className="h-12 w-12 mx-auto mb-3 opacity-30" /><p>暂无协作空间</p><p className="text-sm mt-1">创建空间邀请团队成员加入</p></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {workspaces.map((ws: any) => (
            <Card key={ws.id} className="shadow-sm hover:shadow-md transition-shadow cursor-pointer" onClick={() => openDetail(ws)}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-lg">{ws.name}</h3>
                  <Badge variant="secondary">{ws.member_count || 0} 成员</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{ws.description || '暂无描述'}</p>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">{ws.task_count || 0} 个任务</span>
                  <span className="text-muted-foreground">·</span>
                  <span className="text-muted-foreground">{ws.created_at ? new Date(ws.created_at).toLocaleDateString('zh-CN') : ''}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent className="w-[400px] sm:w-[540px]">
          {selectedWs && (
            <>
              <SheetHeader><SheetTitle>{selectedWs.name}</SheetTitle></SheetHeader>
              <div className="mt-6 space-y-6">
                <div>
                  <h4 className="text-sm font-medium mb-2">成员 ({members.length})</h4>
                  <div className="space-y-2">
                    {members.map((m: any) => (
                      <div key={m.id} className="flex items-center gap-3 p-2 rounded-lg bg-slate-50 dark:bg-slate-900">
                        <div className="h-8 w-8 rounded-full bg-slate-300 dark:bg-slate-700 flex items-center justify-center text-xs font-medium">{m.username?.slice(0, 2).toUpperCase()}</div>
                        <div><p className="text-sm font-medium">{m.username}</p><p className="text-xs text-muted-foreground">{m.email}</p></div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium mb-2">邀请成员</h4>
                  <div className="flex gap-2">
                    <Input value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} placeholder="输入邮箱地址" onKeyDown={e => e.key === 'Enter' && handleInvite()} />
                    <Button onClick={handleInvite} size="sm"><UserPlus className="h-4 w-4 mr-1" />邀请</Button>
                  </div>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

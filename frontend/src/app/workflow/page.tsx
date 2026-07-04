'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Play, CheckCircle, Clock, Loader2, BookOpen, FileSearch, FlaskConical, Send, GraduationCap } from 'lucide-react';

const WORKFLOWS = [
  { id: 'topic', name: '开题', icon: BookOpen, desc: '选题分析、文献调研、开题报告', steps: ['选题分析', '文献调研', '开题报告撰写', '开题答辩'] },
  { id: 'review', name: '综述', icon: FileSearch, desc: '系统检索、文献筛选、综述撰写', steps: ['检索策略', '文献筛选', '质量评估', '综述撰写'] },
  { id: 'reproduce', name: '复现', icon: FlaskConical, desc: '论文实验复现与验证', steps: ['论文分析', '环境搭建', '代码实现', '结果验证'] },
  { id: 'submit', name: '投稿', icon: Send, desc: '选刊、格式检查、提交', steps: ['期刊选择', '格式检查', '投稿信撰写', '提交'] },
  { id: 'defense', name: '答辩', icon: GraduationCap, desc: '答辩准备与演练', steps: ['成果梳理', 'PPT制作', '模拟答辩', '正式答辩'] },
];

export default function WorkflowPage() {
  const [instances, setInstances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [starting, setStarting] = useState<string | null>(null);

  useEffect(() => { fetchInstances(); }, []);

  const fetchInstances = async () => {
    setLoading(true);
    try { const r = await api.get('/api/v1/workflow/instances'); setInstances(r.data || []); } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleStart = async (wfId: string) => {
    setStarting(wfId);
    try { await api.post(`/api/v1/workflow/${wfId}/start`); fetchInstances(); } catch (e: any) { setError(e.message); }
    finally { setStarting(null); }
  };

  const getInstanceStep = (wfId: string) => {
    const active = instances.filter(i => i.workflow_type === wfId && i.status === 'running');
    return active.length > 0 ? active[0] : null;
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold tracking-tight">工作流</h1><p className="text-muted-foreground text-sm mt-1">标准化科研流程</p></div>

      {error && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{[1,2,3].map(i => <Skeleton key={i} className="h-56" />)}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {WORKFLOWS.map(wf => {
            const active = getInstanceStep(wf.id);
            return (
              <Card key={wf.id} className="shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-950"><wf.icon className="h-5 w-5 text-blue-600" /></div>
                    {active ? <Badge variant="default" className="bg-green-600"><Loader2 className="h-3 w-3 animate-spin mr-1" />进行中</Badge> : <Badge variant="outline">未启动</Badge>}
                  </div>
                  <h3 className="font-semibold text-lg mb-1">{wf.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{wf.desc}</p>
                  {active ? (
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>步骤 {active.current_step}/{wf.steps.length}</span>
                        <span>{wf.steps[active.current_step - 1] || ''}</span>
                      </div>
                      <Progress value={(active.current_step / wf.steps.length) * 100} className="h-2" />
                    </div>
                  ) : (
                    <Button onClick={() => handleStart(wf.id)} disabled={starting === wf.id} className="w-full">
                      {starting === wf.id ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}启动
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {instances.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader><CardTitle className="text-base">历史实例</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {instances.filter(i => i.status === 'completed').slice(0, 10).map((inst: any) => (
                <div key={inst.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-900">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm">{WORKFLOWS.find(w => w.id === inst.workflow_type)?.name || inst.workflow_type}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{inst.started_at ? new Date(inst.started_at).toLocaleDateString('zh-CN') : ''}</span>
                    <Badge variant="secondary">已完成</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

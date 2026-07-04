'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Play, Loader2, Clock, AlertTriangle } from 'lucide-react';

const LANGUAGES = [
  { value: 'python', label: 'Python 3' },
  { value: 'r', label: 'R' },
  { value: 'julia', label: 'Julia' },
];

export default function SandboxPage() {
  const [code, setCode] = useState('print("Hello, SciAgent!")');
  const [language, setLanguage] = useState('python');
  const [output, setOutput] = useState('');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<{ code: string; lang: string; output: string; time: string }[]>([]);

  const handleRun = async () => {
    if (!code.trim()) return;
    setRunning(true); setError(''); setOutput('');
    try {
      const r = await api.post('/api/v6/sandbox/execute', { code: code.trim(), language });
      setOutput(r.data?.stdout || r.data?.stderr || '执行完成（无输出）');
      setHistory(prev => [{ code: code.trim(), lang: language, output: r.data?.stdout || '', time: new Date().toLocaleTimeString('zh-CN') }, ...prev].slice(0, 20));
    } catch (e: any) { setError(e.message); }
    finally { setRunning(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">沙箱</h1>
        <p className="text-muted-foreground text-sm mt-1">安全隔离的代码执行环境</p>
      </div>

      <Card className="shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
              <SelectContent>{LANGUAGES.map(l => <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>)}</SelectContent>
            </Select>
            <Button onClick={handleRun} disabled={running} className="bg-green-600 hover:bg-green-700">
              {running ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}运行
            </Button>
            <div className="flex-1" />
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
              <span>资源限制：CPU 1核 | 内存 512MB | 超时 30s | 无网络</span>
            </div>
          </div>
          <textarea
            value={code} onChange={e => setCode(e.target.value)}
            className="w-full h-64 p-4 font-mono text-sm bg-slate-900 text-green-400 rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            placeholder="输入代码..."
            spellCheck={false}
          />
        </CardContent>
      </Card>

      {running && <Progress value={undefined} className="animate-pulse" />}

      {error && <div className="p-4 bg-red-50 dark:bg-red-950 text-red-600 rounded-lg text-sm">{error}</div>}

      {(output || running) && (
        <Card className="shadow-sm">
          <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2">输出</CardTitle></CardHeader>
          <CardContent>
            <pre className="bg-slate-900 text-green-400 p-4 rounded-lg text-sm font-mono whitespace-pre-wrap min-h-[80px] max-h-96 overflow-y-auto">{output || '执行中...'}</pre>
          </CardContent>
        </Card>
      )}

      {history.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Clock className="h-4 w-4" />运行历史</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map((h, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer" onClick={() => { setCode(h.code); setLanguage(h.lang); }}>
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700">{h.lang}</span>
                    <code className="text-sm truncate max-w-md">{h.code}</code>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0">{h.time}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

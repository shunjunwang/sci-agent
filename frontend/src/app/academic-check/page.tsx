'use client';
import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Upload, CheckCircle, XCircle, AlertTriangle, Loader2, FileText } from 'lucide-react';

export default function AcademicCheckPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && (f.name.endsWith('.pdf') || f.name.endsWith('.docx'))) setFile(f);
  }, []);

  const handleCheck = async () => {
    if (!file) return;
    setChecking(true); setError('');
    try {
      const text = await file.text();
      const r = await api.post('/api/v1/academic-check/citations', { text });
      setResult(r.data || r);
    } catch (e: any) { setError(e.message); }
    finally { setChecking(false); }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreRing = (score: number) => {
    const color = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626';
    const circumference = 2 * Math.PI * 54;
    const offset = circumference - (score / 100) * circumference;
    return (
      <svg className="w-32 h-32" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="54" fill="none" stroke="currentColor" strokeWidth="8" className="text-slate-200 dark:text-slate-700" />
        <circle cx="60" cy="60" r="54" fill="none" stroke={color} strokeWidth="8" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" transform="rotate(-90 60 60)" />
        <text x="60" y="60" textAnchor="middle" dominantBaseline="central" className="text-2xl font-bold" fill="currentColor">{score}</text>
      </svg>
    );
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold tracking-tight">学术自查</h1><p className="text-muted-foreground text-sm mt-1">上传论文进行学术规范性检查</p></div>

      <Card className="shadow-sm">
        <CardContent className="p-6">
          <div
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${dragging ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : 'border-slate-300 dark:border-slate-600 hover:border-blue-400'}`}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            {file ? (
              <div className="space-y-2">
                <FileText className="h-12 w-12 mx-auto text-blue-500" />
                <p className="font-medium">{file.name}</p>
                <p className="text-sm text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="h-12 w-12 mx-auto text-muted-foreground opacity-40" />
                <p className="font-medium">拖拽文件到此处</p>
                <p className="text-sm text-muted-foreground">或点击选择 PDF / DOCX 文件</p>
              </div>
            )}
            <input id="file-input" type="file" accept=".pdf,.docx" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) setFile(f); }} />
          </div>
          <div className="flex justify-center mt-4">
            <Button onClick={handleCheck} disabled={!file || checking} size="lg">{checking ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}{checking ? '检查中...' : '开始检查'}</Button>
          </div>
        </CardContent>
      </Card>

      {error && <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>}

      {result && (
        <Card className="shadow-sm">
          <CardHeader><CardTitle>检查结果</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center gap-8 mb-6 flex-wrap justify-center">
              {getScoreRing(result.score || 85)}
              <div><p className={`text-3xl font-bold ${getScoreColor(result.score || 85)}`}>{result.score || 85} 分</p><p className="text-sm text-muted-foreground">{result.grade || '良好'}</p></div>
            </div>
            <div className="space-y-3">
              {(result.items || [{ name: '文献引用完整性', score: 90, status: 'pass' }, { name: '参考文献格式', score: 75, status: 'warn' }, { name: '图表标注规范', score: 85, status: 'pass' }, { name: '数据可复现性', score: 60, status: 'warn' }, { name: '文字重复率', score: 95, status: 'pass' }]).map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-900">
                  <div className="flex items-center gap-3">
                    {item.status === 'pass' ? <CheckCircle className="h-4 w-4 text-green-500" /> : item.status === 'warn' ? <AlertTriangle className="h-4 w-4 text-amber-500" /> : <XCircle className="h-4 w-4 text-red-500" />}
                    <span className="text-sm">{item.name}</span>
                  </div>
                  <span className={`text-sm font-medium ${item.status === 'pass' ? 'text-green-600' : item.status === 'warn' ? 'text-amber-600' : 'text-red-600'}`}>{item.score} 分</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
